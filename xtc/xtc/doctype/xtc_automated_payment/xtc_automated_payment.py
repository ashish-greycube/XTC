# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import pandas as pd
from frappe.utils import getdate, cint, flt, get_link_to_form
from frappe.contacts.doctype.address.address import get_address_display
from frappe.core.doctype.communication.email import make
from erpnext import get_default_company
from erpnext.accounts.doctype.payment_entry.payment_entry import (
    get_payment_entry,
)
import re
import operator
from frappe.desk.query_report import get_report_result
import itertools


class XTCAutomatedPayment(Document):
    def validate(self):
        for d in self.payment_details:
            if not d.payment_date:
                d.payment_date = self.payment_date
            if d.amount_to_pay > d.outstanding_amount:
                frappe.throw(
                    _(
                        "Paid amount {} cannot be greater than outstanding amount {}."
                    ).format(d.amount_to_pay, d.outstanding_amount)
                )
        self.total_amount = sum([flt(d.amount_to_pay) for d in self.payment_details])

        # sort payments by supplier, invoice_no
        self.payment_details = sorted(
            self.payment_details, key=lambda x: x.supplier + x.purchase_invoice
        )

        for idx, d in enumerate(self.payment_details):
            d.idx = idx

        self.suppliers = sorted(self.suppliers, key=lambda x: x.supplier)

        for idx, d in enumerate(self.suppliers):
            d.idx = idx

    @frappe.whitelist()
    def close_payment(self):
        for d in frappe.get_all(
            "Payment Entry",
            filters={
                "docstatus": 0,
                "name": ("in", [d.payment_entry for d in self.payment_details]),
            },
        ):
            frappe.get_doc("Payment Entry", d).submit()
        self.db_set("payment_entry_status", "Closed", commit=True, notify=True)
        frappe.db.commit()
        frappe.msgprint(_("Payment Entries submitted."))

    def validate_suppliers(self):
        for d in frappe.get_all(
            "Supplier",
            filters={"name": ("in", [d.supplier for d in self.suppliers])},
            fields=[
                "name",
                "supplier_name",
                "supplier_party_account_type_cf",
                "supplier_party_bank_code_cf",
                "supplier_party_account_id_cf",
                "supplier_party_name_cf",
            ],
        ):
            invalid = []
            if d.supplier_party_account_type_cf == "A":
                if (
                    not d.supplier_party_bank_code_cf
                    or not d.supplier_party_bank_code_cf.isnumeric()
                    or not d.supplier_party_account_id_cf.isnumeric()
                    or len(d.supplier_party_account_id_cf) > 12
                ):
                    invalid.append(
                        "Bank Code: %s, Account Number: %s"
                        % (
                            d.supplier_party_bank_code_cf or "",
                            d.supplier_party_account_id_cf,
                        )
                    )
            elif d.supplier_party_account_type_cf == "E":
                if not frappe.utils.validate_email_address(
                    d.supplier_party_account_id_cf
                ):
                    invalid.append("Email: %s" % d.supplier_party_account_id_cf)
            elif d.supplier_party_account_type_cf == "M":
                if not re.match("^\d{8}$", d.supplier_party_account_id_cf or ""):
                    invalid.append(
                        "Mobile: %s" % (d.supplier_party_account_id_cf or "")
                    )
            if not d.supplier_party_name_cf:
                invalid.append("Party name is blank")

            if invalid:
                msg = "Invalid supplier details for {0}:<br>{1}".format(
                    d.supplier_name, ", ".join(invalid)
                )
                frappe.throw(msg)

    def on_submit(self):
        self.validate_suppliers()

        supplier_emails = [
            d.supplier_name
            for d in self.suppliers
            if d.send_email and not d.get("email_id")
        ]
        if supplier_emails:
            frappe.throw(
                _("Please set email id for suppliers: %s" % ", ".join(supplier_emails))
            )

    def on_cancel(self):
        payment_entry = [
            d.payment_entry for d in self.payment_details if d.payment_entry
        ]
        if payment_entry:
            msg = _("Please cancel these linked Payment Entries: {0}").format(
                ", ".join(
                    get_link_to_form("Payment Entry", d) for d in set(payment_entry)
                )
            )
            frappe.throw(msg)
        self.set_payment_entry_status()

    @frappe.whitelist()
    def _get_accounts_payable(self):
        df = self.get_invoices()

        if not len(df):
            frappe.msgprint("No payments found matching selected criteria.")
            return

        # clear existing voucher if exists in payment details
        #  as same voucher may appear multiple times with based_on_payment_terms
        vouchers = set(df["voucher_no"].tolist())
        if self.get("payment_details"):
            self.payment_details = [
                d for d in self.payment_details if not d.purchase_invoice in vouchers
            ]

        for _, d in df.iterrows():
            self.append(
                "payment_details",
                {
                    "supplier_name": d.supplier_name,
                    "supplier": d.party,
                    "purchase_invoice": d.voucher_no,
                    "due_date": d.due_date,
                    "posting_date": d.posting_date,
                    "invoiced_amount": d.invoiced,
                    "outstanding_amount": d.outstanding,
                    "paid_amount": d.paid,
                    "amount_to_pay": d.outstanding,
                    "payment_date": self.payment_date,
                },
            )

        # sort again
        self.payment_details = sorted(
            self.payment_details, key=lambda cdn: (cdn.supplier, cdn.purchase_invoice)
        )

    def get_invoices(self):
        filters = frappe._dict(
            {
                "company": self.company,
                "report_date": self.to_due_date or frappe.utils.today(),
                "ageing_based_on": "Due Date",
                "range1": 30,
                "range2": 60,
                "range3": 90,
                "range4": 120,
                "based_on_payment_terms": cint(self.based_on_payment_terms),
                "supplier_group": self.supplier_group
                if not self.supplier_group == "All Supplier Groups"
                else None,
                "supplier": self.supplier,
            }
        )
        accounts_payable = frappe.get_doc("Report", "Accounts Payable")
        _columns, data, *other = get_report_result(accounts_payable, filters)

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame.from_records(data)
        # filter
        df = df[df["voucher_type"] == "Purchase Invoice"]
        if self.from_due_date:
            df = df[df["due_date"] >= getdate(self.from_due_date)]
        if self.to_due_date:
            df = df[df["due_date"] <= getdate(self.to_due_date)]
        if self.max_amount:
            df = df[df["outstanding"] <= self.max_amount]
        if self.min_amount:
            df = df[df["outstanding"] >= self.min_amount]

        # remove on hold purchase invoices
        if len(df):
            not_on_hold = frappe.db.sql_list(
                """
                select name from `tabPurchase Invoice`
                where name in ({}) and on_hold = 0
            """.format(
                    ",".join(f"'{d}'" for d in df["voucher_no"].to_list())
                )
            )
            df = df[df["voucher_no"].isin(not_on_hold)]

        # sort by purchaser, posting_date
        df.sort_values(by=["party", "voucher_no"], inplace=True)

        return df

    @frappe.whitelist()
    def make_payment_entry(self):
        if not sum(
            d.amount_to_pay for d in self.payment_details if not d.payment_entry
        ):
            frappe.throw(_("No supplier payments to create Payment Entry."))

        for supplier in set(
            d.supplier for d in self.payment_details if not d.payment_entry
        ):
            payments = list(p for p in self.payment_details if p.supplier == supplier)

            pe = get_payment_entry(
                "Purchase Invoice",
                payments[0].purchase_invoice,
                reference_date=self.payment_date,
            )
            pe.reference_no = self.name
            pe.paid_amount = sum([d.amount_to_pay for d in payments])
            pe.mode_of_payment = self.mode_of_payment
            pe.paid_from = self.paid_from

            pe.references = []
            payments = sorted(payments, key=operator.attrgetter("purchase_invoice"))

            # for d in payments:
            for pi, grp in itertools.groupby(
                payments, key=operator.attrgetter("purchase_invoice")
            ):
                pe.append(
                    "references",
                    {
                        "reference_doctype": "Purchase Invoice",
                        "reference_name": pi,
                        "allocated_amount": sum([d.amount_to_pay for d in grp]),
                    },
                )

            pe.validate()
            pe.insert()
            # pe.submit()

            # update link in child table
            for d in payments:
                frappe.db.set_value(
                    "XTC Automated Payment Detail", d.name, "payment_entry", pe.name
                )
        self.set_payment_entry_status()

    def set_payment_entry_status(self):
        self.load_from_db()
        pending = [d for d in self.payment_details if not d.payment_entry]
        if len(pending) == len(self.payment_details):
            self.db_set("payment_entry_status", "Pending")
        elif not pending:
            self.db_set("payment_entry_status", "Completed")
        else:
            self.db_set("payment_entry_status", "Partially Completed")

    @frappe.whitelist()
    def download_bank_csv(self):
        bank_file_header = (
            (
                "Second Party Account Type",
                "Second Party Bank Code",
                "Second Party Account ID",
                "Second Party Name",
                "Amount",
                "Particular ID",
            ),
        )
        data = frappe.db.sql(
            """
                select 
                    ts.supplier_party_account_type_cf,
                    ts.supplier_party_bank_code_cf,
                    ts.supplier_party_account_id_cf,
                    ts.supplier_party_name_cf, 
                    tpe.paid_amount,
                    REPLACE(tpe.name,"-",'')
                from `tabPayment Entry` tpe 
                inner join (
                    select 
                        txapd.supplier , txapd.payment_entry 
                    from `tabXTC Automated Payment` txap 
                    inner join `tabXTC Automated Payment Detail` txapd on txapd.parent = txap.name
                        and txapd.payment_entry is not null
                    where txap.name = %s
                    group by supplier , payment_entry 
                ) t on t.payment_entry = tpe.name 
                inner join tabSupplier ts on ts.name = tpe.party
        """,
            (self.name),
        )
        if not data:
            frappe.throw(_("No payment records exist."))

        return bank_file_header + data

    @frappe.whitelist()
    def send_bank_summary(self):
        """email bank payment summary to session user"""
        settings = frappe.get_cached_doc("XTC Payment Settings")

        file_name = "Bank Payment Summary_{}_{}".format(self.name, self.payment_date)
        out = frappe.attach_print(
            self.doctype,
            self.name,
            file_name=file_name,
            print_format=settings.bank_payment_summary_format,
        )

        # attach_file(out, file_name, self.doctype, self.name)

        email_template = frappe.get_doc(
            "Email Template", settings.bank_payment_summary_email_template
        )
        args = {}
        args[
            "recipients"
        ] = settings.email_address_email_bank_summary or frappe.db.get_value(
            "User", frappe.session.user, "email"
        )
        args["subject"] = frappe.render_template(
            email_template.subject, {"doc": self.as_dict()}
        )
        args["message"] = frappe.render_template(
            email_template.response, {"doc": self.as_dict()}
        )
        args["attachments"] = [out]
        frappe.sendmail(**args)

        frappe.db.commit()
        frappe.msgprint(_("Bank Summary email has been queued."))

    @frappe.whitelist()
    def send_supplier_payment_advice_emails(self):
        """email bank payment advice to each suppplier in child table"""
        settings = frappe.get_cached_doc("XTC Payment Settings")

        for supplier in self.suppliers:
            if not cint(supplier.send_email) or cint(supplier.email_sent):
                continue

            supplier_details = supplier.as_dict()

            supplier_details["payment_details"] = frappe.db.sql(
                """
            select 
                coalesce(tpi.bill_no,'-') bill_no , coalesce(tpi.bill_date,'-') bill_date , 
                txapd.*
            from `tabXTC Automated Payment Detail` txapd 
            inner join `tabPurchase Invoice` tpi on tpi.name = txapd.purchase_invoice 
            where txapd.supplier = %s and txapd.parent = %s
            """,
                (supplier.supplier, self.name),
                as_dict=True,
            )
            address = frappe.db.get_value(
                "Supplier", supplier.supplier, "supplier_primary_address"
            )
            supplier_details["address_display"] = get_address_display(address)
            supplier_details["total_amount"] = sum(
                [d.get("amount_to_pay") for d in supplier_details["payment_details"]]
            )
            self.supplier_details = supplier_details

            file_name = "{}_Payment Advice_{}_{}".format(
                supplier.supplier, self.name, self.payment_date
            )

            out = frappe.attach_print(
                self.doctype,
                self.name,
                file_name=file_name,
                print_format=settings.supplier_payment_advice_format,
                doc=self,
            )
            # with open(f"{self.name}_test.pdf", "wb") as f:
            #     f.write(out["fcontent"])
            # attach_file(out, file_name, self.doctype, self.name)

            email_template = frappe.get_doc(
                "Email Template", settings.supplier_payment_advice_email_template
            )

            context = {"doc": self.as_dict(), "supplier_details": supplier_details}

            frappe.sendmail(
                recipients=supplier.email_id,
                subject=frappe.render_template(email_template.subject, context=context),
                message=frappe.render_template(
                    email_template.response, context=context
                ),
                attachments=[out],
            )
            supplier.db_set("email_sent", 1)
        frappe.db.commit()
        frappe.msgprint(_("Supplier Payment Advice emails have been queued."))


def attach_file(content, file_name, doctype, docname):
    _file = frappe.get_doc(
        {
            "doctype": "File",
            "file_name": file_name,
            "attached_to_doctype": doctype,
            "attached_to_name": docname,
            "is_private": 0,
            "content": content,
        }
    )
    _file.save(ignore_permissions=True)


@frappe.whitelist()
def supplier_query(doctype, txt, searchfield, start, page_len, filters):
    return frappe.db.sql(
        """
        select
            ts.name , fn.name
        from `tabSupplier` ts
            inner join (
                select tsg.name from `tabSupplier Group` tsg
                inner join `tabSupplier Group` tsg2 on tsg2.name = %(supplier_group)s
                and tsg.lft >= tsg2.lft and tsg.rgt <= tsg2.rgt
            ) fn on ts.supplier_group = fn.name and ts.name like %(txt)s
    limit %(start)s, %(page_len)s
            """,
        {
            "txt": "%" + txt + "%",
            "start": start,
            "page_len": page_len,
            "supplier_group": filters.get("supplier_group") or "All Supplier Groups",
        },
    )


@frappe.whitelist()
def get_default_bank_account(mode_of_payment):
    paid_from = frappe.db.get_value(
        "Mode of Payment Account",
        {"parent": mode_of_payment, "company": get_default_company()},
        fieldname=["default_account"],
    )
    if not paid_from:
        frappe.throw(
            _("Please set the default account for Mode of Payment {}.").format(
                mode_of_payment
            )
        )
    return paid_from


def before_cancel_payment_entry(doc, method):
    auto_payment = frappe.db.sql(
        """
        select parent from `tabXTC Automated Payment Detail` 
        where payment_entry = %s
    """,
        (doc.name),
    )
    frappe.db.sql(
        """
        update `tabXTC Automated Payment Detail`
        set payment_entry = null
        where payment_entry=%s
    """,
        (doc.name),
    )
    for d in auto_payment:
        frappe.get_doc("XTC Automated Payment", d[0]).set_payment_entry_status()
