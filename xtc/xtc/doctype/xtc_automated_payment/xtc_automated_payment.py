# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
import pandas as pd
from frappe.utils import getdate, cint, flt
from frappe.contacts.doctype.address.address import get_address_display
from frappe.core.doctype.communication.email import make


class XTCAutomatedPayment(Document):
    def validate(self):
        for d in self.payment_details:
            if not d.payment_date:
                d.payment_date = self.payment_date
            if d.amount_to_pay > d.outstanding_amount:
                frappe.throw(
                    _("Paid amount {} cannot be greater than outstanding amount {}.").format(
                        d.amount_to_pay, d.outstanding_amount))
        self.total_amount = sum([flt(d.amount_to_pay)
                                for d in self.payment_details])

    def on_submit(self):
        supplier_details = frappe.db.sql_list("""
        select supplier_name
                from tabSupplier ts
        where name in ({})
            and (supplier_party_account_type_cf is null or
            supplier_party_bank_code_cf is null or
            supplier_party_account_id_cf is null or
            supplier_party_name_cf is null)
        """.format(",".join(frappe.db.escape(d.supplier) for d in self.suppliers))
        )

        if supplier_details:
            frappe.throw(
                _("Please complete Bank details for suppliers: %s" % ", ".join(supplier_details)))

        supplier_emails = [
            d.supplier_name for d in self.suppliers if not d.get("email_id")]
        if supplier_emails:
            frappe.throw(_("Please set email id for suppliers: %s" %
                         ", ".join(supplier_emails)))

    @frappe.whitelist()
    def _get_accounts_payable(self):
        df = self.get_invoices()

        if not len(df):
            frappe.msgprint("No payments found matching selected criteria.")

        for _, d in df.iterrows():
            if len(
                list(
                    filter(
                        lambda x: x.purchase_invoice == d.voucher_no,
                        self.get("payment_details", []),
                    )
                )
            ):
                continue

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

    def get_invoices(self):
        from erpnext.accounts.report.accounts_receivable.accounts_receivable import (
            ReceivablePayableReport, )

        args = {
            "party_type": "Supplier",
            "naming_by": ["Buying Settings", "supp_master_name"],
        }
        _columns, ap_data, *other = ReceivablePayableReport(
            {
                "company": self.company,
                "report_date": frappe.utils.today(),
                "ageing_based_on": "Due Date",
                "range1": 30,
                "range2": 60,
                "range3": 90,
                "range4": 120,
            }
        ).run(args)

        df = pd.DataFrame.from_records(ap_data)
        # filter
        df = df[df["voucher_type"] == "Purchase Invoice"]
        if self.from_due_date:
            df = df[df["due_date"] >= getdate(self.from_due_date)]
        if self.to_due_date:
            df = df[df["due_date"] <= getdate(self.to_due_date)]
        if self.supplier:
            df = df[df["party"] == self.supplier]
        if self.max_amount:
            df = df[df["outstanding"] <= self.max_amount]
        if self.min_amount:
            df = df[df["outstanding"] >= self.min_amount]

        if self.supplier_group:
            supplier_groups = frappe.db.sql_list(
                """
                select tsg.name from `tabSupplier Group` tsg
                inner join `tabSupplier Group` tsg2 on tsg2.name = %s
                    and tsg.lft >= tsg2.lft and tsg.rgt <= tsg2.rgt
                """,
                (self.supplier_group),
            )
            df = df[df["supplier_group"].isin(supplier_groups)]

        return df

    @frappe.whitelist()
    def download_bank_csv(self):
        bank_file_header = [
            [
                "Second Party Account Type",
                "Second Party Bank Code",
                "Second Party Account ID",
                "Second Party Name",
                "Amount",
                "Particular ID",
            ]
        ]
        suppliers = set([d.supplier for d in self.payment_details])
        supplier_details = frappe.get_all(
            "Supplier",
            filters={"name": ("in", list(suppliers))},
            fields=[
                "name",
                "supplier_party_account_type_cf",
                "supplier_party_bank_code_cf",
                "supplier_party_account_id_cf",
                "supplier_party_name_cf",
            ],
        )

        supplier_details = {d.name: d for d in supplier_details}

        data = []
        for d in self.payment_details:
            supplier = supplier_details.get(d.supplier)
            data.append(
                [
                    supplier.supplier_party_account_type_cf,
                    supplier.supplier_party_bank_code_cf,
                    supplier.supplier_party_account_id_cf,
                    supplier.supplier_party_name_cf,
                    d.amount_to_pay,
                    self.name
                ]
            )
        return bank_file_header + data

    @frappe.whitelist()
    def send_bank_summary(self):
        """email bank payment summary to session user"""
        settings = frappe.get_cached_doc("XTC Settings")

        file_name = "Bank Payment Summary_{}_{}".format(
            self.name, self.payment_date)
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
        args['recipients'] = settings.email_address_email_bank_summary or frappe.db.get_value(
            "User", frappe.session.user, "email")
        args["subject"] = frappe.render_template(
            email_template.subject, {"doc": self.as_dict()})
        args["message"] = frappe.render_template(
            email_template.response,
            {"doc": self.as_dict()})
        args["attachments"] = [out]
        frappe.sendmail(**args)

        frappe.db.commit()
        frappe.msgprint(_("Bank Summary email has been queued."))

    @frappe.whitelist()
    def send_supplier_payment_advice_emails(self):
        """email bank payment advice to each suppplier in child table"""
        settings = frappe.get_cached_doc("XTC Settings")

        _payment_details = self.payment_details

        for supplier in self.suppliers:
            if not cint(supplier.send_email) or cint(supplier.email_sent):
                continue

            payment_details = list(
                filter(
                    lambda x: x.supplier == supplier.supplier,
                    _payment_details))
            address = frappe.db.get_value(
                "Supplier", supplier.supplier, "supplier_primary_address"
            )

            supplier_details = supplier.as_dict()
            supplier_details["payment_details"] = payment_details
            supplier_details["total_amount"] = sum(
                [d.get("amount_to_pay") for d in payment_details]
            )
            supplier_details["address_display"] = get_address_display(address)
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
                "Email Template", settings.supplier_payment_advice_email_template)

            context = {
                "doc": self.as_dict(),
                "supplier_details": supplier_details}

            frappe.sendmail(
                recipients=supplier.email_id,
                subject=frappe.render_template(
                    email_template.subject, context=context),
                message=frappe.render_template(
                    email_template.response, context=context),
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
