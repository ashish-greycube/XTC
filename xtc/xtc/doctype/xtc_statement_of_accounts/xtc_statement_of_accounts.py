# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import copy

import frappe
from frappe import _
from frappe.desk.reportview import get_match_cond
from frappe.model.document import Document
from frappe.utils import add_days, add_months, format_date, getdate, today, cstr
from frappe.utils.jinja import validate_template
from frappe.utils.pdf import get_pdf
from frappe.www.printview import get_print_style

from erpnext import get_company_currency
from erpnext.accounts.party import get_party_account_currency
from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import (
    execute as get_ageing,
)
from erpnext.accounts.report.general_ledger.general_ledger import execute as get_soa
from erpnext.accounts.report.accounts_receivable.accounts_receivable import (
    execute as get_xtc_soa,
)
import functools
from frappe.contacts.doctype.address.address import get_address_display
from frappe.email.smtp import get_default_outgoing_email_account


class XTCStatementOfAccounts(Document):
    def validate(self):
        if not self.subject:
            self.subject = "Statement Of Accounts for {{ customer.name }}"
        if not self.body:
            self.body = "Hello {{ customer.name }},<br>PFA your Statement Of Accounts as on date {{ doc.to_date }}."

        validate_template(self.subject)
        validate_template(self.body)

        if not self.customers:
            frappe.throw(_("Customers not selected."))

        if self.enable_auto_email:
            if self.start_date and getdate(self.start_date) >= getdate(today()):
                self.to_date = self.start_date


def get_report_pdf(doc, consolidated=True):
    statement_dict = {}
    ageing = ""
    base_template_path = "frappe/www/printview.html"
    template_path = (
        "xtc/xtc/doctype/xtc_statement_of_accounts/xtc_statement_of_accounts.html"
    )

    last_customer = doc.customers[-1]
    for entry in doc.customers:
        # frappe.publish_realtime("download_pdf_tool", dict(progress=[entry.idx, len(doc.customers)]), user=frappe.session.user)
        presentation_currency = get_party_account_currency(
            "Customer", entry.customer, doc.company
        ) or get_company_currency(doc.company)
        if doc.letter_head:
            from frappe.www.printview import get_letter_head

            letter_head = get_letter_head(doc, 0)
        addr_list = get_customer_primary_address("Customer", entry.customer)

        payment_terms = frappe.db.get_value("Customer", entry.customer, "payment_terms")
        if entry.customer:
            filters = frappe._dict(
                {
                    "to_date": doc.to_date,
                    "company": doc.company,
                    "party_type": "Customer",
                    "party": [entry.customer],
                    "customer_name": frappe.db.get_value(
                        "Customer", entry.customer, "customer_name"
                    ),
                    "customer_address": (
                        frappe.render_template(
                            "xtc/xtc/doctype/xtc_statement_of_accounts/address_list.html",
                            addr_list,
                        )
                        if addr_list
                        else ""
                    ),
                    "customer_payment_terms": payment_terms,
                    "currency": presentation_currency,
                    "report_date": doc.to_date,
                    "ageing_based_on": "Due Date",
                    "customer": entry.customer,
                    "include_ageing": doc.include_ageing,
                    "range1": 30,
                    "range2": 60,
                    "range3": 90,
                    "range4": 120,
                }
            )

            col, res, third_arg, chart, fifth_arg, skip_total_row = get_xtc_soa(filters)

            for x in res:
                x["po_no"] = (
                    not x["voucher_type"] == "Sales Invoice"
                    and ""
                    or cstr(
                        frappe.db.get_value("Sales Invoice", x["voucher_no"], "po_no")
                    )
                )

            filters["total_range_1"] = sum(x.get("range1", 0) for x in res)
            filters["total_range_2"] = sum(x.get("range2", 0) for x in res)
            filters["total_range_3"] = sum(x.get("range3", 0) for x in res)
            filters["total_range_4"] = sum(x.get("range4", 0) for x in res)
            filters["outstanding_total"] = sum(x.get("outstanding", 0) for x in res)

            terms_and_conditions = frappe.db.get_value(
                "Terms and Conditions", doc.terms_and_conditions, "terms"
            )
            # if last_customer==entry:
            # 	terms_and_conditions=frappe.db.get_value("Terms and Conditions", doc.terms_and_conditions, "terms")
            # else:
            # 	terms_and_conditions=None

            html = frappe.render_template(
                template_path,
                {
                    "filters": filters,
                    "data": res,
                    "letter_head": letter_head if doc.letter_head else None,
                    "terms_and_conditions": terms_and_conditions,
                },
            )

            html = frappe.render_template(
                base_template_path,
                {
                    "body": html,
                    "css": get_print_style(),
                    "title": "Statement For " + entry.customer,
                },
            )
            statement_dict[entry.customer] = html

    if not bool(statement_dict):
        return False
    elif consolidated:
        delimiter = (
            '<div style="page-break-before: always;"></div>'
            if doc.include_break
            else ""
        )
        result = delimiter.join(list(statement_dict.values()))
        return get_pdf(result, {"orientation": doc.orientation})
    else:
        for customer, statement_html in statement_dict.items():
            statement_dict[customer] = get_pdf(
                statement_html, {"orientation": doc.orientation}
            )
        return statement_dict


def get_customers_based_on_territory_or_customer_group(
    customer_collection, collection_name
):
    fields_dict = {
        "Customer Group": "customer_group",
        "Territory": "territory",
    }
    collection = frappe.get_doc(customer_collection, collection_name)
    selected = [
        customer.name
        for customer in frappe.get_list(
            customer_collection,
            filters=[["lft", ">=", collection.lft], ["rgt", "<=", collection.rgt]],
            fields=["name"],
            order_by="lft asc, rgt desc",
        )
    ]
    return frappe.get_list(
        "Customer",
        fields=["name", "email_id"],
        filters=[[fields_dict[customer_collection], "IN", selected]],
    )


def get_customers_based_on_sales_person(sales_person):
    lft, rgt = frappe.db.get_value("Sales Person", sales_person, ["lft", "rgt"])
    records = frappe.db.sql(
        """
		select distinct parent, parenttype
		from `tabSales Team` steam
		where parenttype = 'Customer'
			and exists(select name from `tabSales Person` where lft >= %s and rgt <= %s and name = steam.sales_person)
	""",
        (lft, rgt),
        as_dict=1,
    )
    sales_person_records = frappe._dict()
    for d in records:
        sales_person_records.setdefault(d.parenttype, set()).add(d.parent)
    if sales_person_records.get("Customer"):
        return frappe.get_list(
            "Customer",
            fields=["name", "email_id"],
            filters=[["name", "in", list(sales_person_records["Customer"])]],
        )
    else:
        return []


def get_recipients_and_cc(customer, doc):
    recipients = []
    for clist in doc.customers:
        if clist.customer == customer:
            recipients.append(clist.billing_email)
            if doc.primary_mandatory and clist.primary_email:
                recipients.append(clist.primary_email)
            if clist.additional_email_id:
                aditional_email_id = (clist.additional_email_id).split(",")
                if aditional_email_id:
                    if len(recipients) > 0 and recipients[0] != "":
                        recipients = recipients + aditional_email_id
                    else:
                        recipients = aditional_email_id
    cc = []
    if doc.cc_to != "":
        try:
            cc = [frappe.get_value("User", doc.cc_to, "email")]
        except Exception:
            pass

    return recipients, cc


def get_context(customer, doc):
    template_doc = copy.deepcopy(doc)
    del template_doc.customers
    template_doc.to_date = format_date(template_doc.to_date)
    return {
        "doc": template_doc,
        "customer": frappe.get_doc("Customer", customer),
        "frappe": frappe.utils,
    }


@frappe.whitelist()
def fetch_customers(customer_collection, collection_name, primary_mandatory):
    customer_list = []
    customers = []

    if customer_collection == "Sales Person":
        customers = get_customers_based_on_sales_person(collection_name)
        if not bool(customers):
            frappe.throw(_("No Customers found with selected options."))
    else:
        if customer_collection == "Sales Partner":
            customers = frappe.get_list(
                "Customer",
                fields=["name", "email_id"],
                filters=[["default_sales_partner", "=", collection_name]],
            )
        else:
            customers = get_customers_based_on_territory_or_customer_group(
                customer_collection, collection_name
            )

    for customer in customers:
        primary_email = customer.get("email_id") or ""
        billing_email = get_customer_emails(customer.name, 1, billing_and_primary=False)

        if int(primary_mandatory):
            if primary_email == "":
                continue

        customer_list.append(
            {
                "name": customer.name,
                "primary_email": primary_email,
                "billing_email": billing_email,
            }
        )
    return customer_list


@frappe.whitelist()
def get_customer_emails(customer_name, primary_mandatory, billing_and_primary=True):
    """Returns first email from Contact Email table as a Billing email
    when Is Billing Contact checked
    and Primary email- email with Is Primary checked"""
    billing_email = frappe.db.sql(
        """
		SELECT
			email.email_id
		FROM
			`tabContact Email` AS email
		JOIN
			`tabDynamic Link` AS `link`
		ON
			email.parent=`link`.parent
		JOIN
			`tabContact` AS contact
		ON
			contact.name=`link`.parent
		WHERE
			`link`.link_doctype='Customer'
			and `link`.link_name=%s
			and contact.is_billing_contact=1
			{mcond}
		ORDER BY
			contact.creation desc
		""".format(
            mcond=get_match_cond("Contact")
        ),
        customer_name,
    )

    if len(billing_email) == 0 or (billing_email[0][0] is None):
        if billing_and_primary:
            frappe.throw(
                _("No billing email found for customer: {0}").format(customer_name)
            )
        else:
            return ""

    if billing_and_primary:
        primary_email = frappe.get_value("Customer", customer_name, "email_id")
        if primary_email is None and int(primary_mandatory):
            frappe.throw(
                _("No primary email found for customer: {0}").format(customer_name)
            )
        return [primary_email or "", billing_email[0][0]]
    else:
        return billing_email[0][0] or ""


@frappe.whitelist()
def download_statements(document_name):
    doc = frappe.get_doc("XTC Statement Of Accounts", document_name)
    print("000", document_name)
    report = get_report_pdf(doc, consolidated=True)
    if report:
        frappe.local.response.filename = doc.name + ".pdf"
        frappe.local.response.filecontent = report
        frappe.local.response.type = "download"


@frappe.whitelist()
def send_emails(document_name, from_scheduler=False):
    doc = frappe.get_doc("XTC Statement Of Accounts", document_name)
    report = get_report_pdf(doc, consolidated=False)
    default_outgoing_account = get_default_outgoing_email_account(
        raise_exception_not_set=True
    )
    sender_email_id = frappe.db.get_value(
        "Email Account", default_outgoing_account.name, "email_id"
    )
    if report:
        for customer, report_pdf in report.items():
            attachments = [{"fname": customer + ".pdf", "fcontent": report_pdf}]

            recipients, bcc = get_recipients_and_cc(customer, doc)
            if not recipients:
                continue
            context = get_context(customer, doc)
            subject = frappe.render_template(doc.subject, context)
            message = frappe.render_template(doc.body, context)
            frappe.enqueue(
                queue="short",
                method=frappe.sendmail,
                recipients=recipients,
                sender=sender_email_id,
                bcc=bcc,
                subject=subject,
                message=message,
                now=True,
                reference_doctype="XTC Statement Of Accounts",
                reference_name=document_name,
                attachments=attachments,
            )

        if doc.enable_auto_email and from_scheduler:
            new_to_date = getdate(today())
            if doc.frequency == "Weekly":
                new_to_date = add_days(new_to_date, 7)
            else:
                new_to_date = add_months(
                    new_to_date, 1 if doc.frequency == "Monthly" else 3
                )
            doc.add_comment(
                "Comment",
                "Emails sent on: " + frappe.utils.format_datetime(frappe.utils.now()),
            )
            doc.db_set("to_date", new_to_date, commit=True)
        return True
    else:
        return False


@frappe.whitelist()
def send_auto_email():
    selected = frappe.get_list(
        "XTC Statement Of Accounts",
        filters={"to_date": format_date(today()), "enable_auto_email": 1},
    )
    for entry in selected:
        send_emails(entry.name, from_scheduler=True)
    return True


def get_customer_primary_address(doctype, docname):
    filters = [
        ["Dynamic Link", "link_doctype", "=", doctype],
        ["Dynamic Link", "link_name", "=", docname],
        ["Dynamic Link", "parenttype", "=", "Address"],
    ]
    address_list = frappe.get_list(
        "Address", filters=filters, fields=["*"], order_by="creation asc"
    )
    address_list = [a.update({"display": get_address_display(a)}) for a in address_list]

    address_list = sorted(
        address_list,
        key=functools.cmp_to_key(
            lambda a, b: (int(a.is_primary_address - b.is_primary_address))
            or (1 if a.modified - b.modified else 0)
        ),
        reverse=True,
    )
    if len(address_list) > 0:
        return address_list[0]
    else:
        return None
