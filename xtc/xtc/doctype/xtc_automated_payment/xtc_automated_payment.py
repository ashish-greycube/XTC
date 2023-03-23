# Copyright (c) 2023, GreyCube Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
import pandas as pd
from frappe.utils import getdate
from frappe.contacts.doctype.address.address import get_address_display


class XTCAutomatedPayment(Document):
    def validate(self):
        for d in self.payment_details:
            if not d.payment_date:
                d.payment_date = self.payment_date

    @frappe.whitelist()
    def _get_accounts_payable(self):
        df = self.get_invoices()

        if not len(df):
            frappe.msgprint("No payments found matching selected criteria.")

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

    def get_invoices(self):
        from erpnext.accounts.report.accounts_receivable.accounts_receivable import (
            ReceivablePayableReport,
        )

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
                "second_party_account_type_cf",
                "second_party_bank_code_cf",
                "second_party_account_id_cf",
                "second_party_name_cf",
            ],
        )

        supplier_details = {d.name: d for d in supplier_details}

        data = []
        for d in self.payment_details:
            supplier = supplier_details.get(d.supplier)
            data.append(
                [
                    supplier.second_party_account_type_cf,
                    supplier.second_party_bank_code_cf,
                    supplier.second_party_account_id_cf,
                    supplier.second_party_name_cf,
                    d.amount_to_pay,
                    self.name,
                ]
            )
        return bank_file_header + data

    @frappe.whitelist()
    def make_bank_summary(self):
        out = frappe.attach_print(
            self.doctype,
            self.name,
            file_name="Bank Payment Summary_{}_{}".format(self.name, self.payment_date),
            print_format="Bank Payment Summary",
        )
        _file = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": out["fname"],
                "attached_to_doctype": self.doctype,
                "attached_to_name": self.name,
                "is_private": 0,
                "content": out["fcontent"],
            }
        )
        _file.save(ignore_permissions=True)
        # send_email

    @frappe.whitelist()
    def send_supplier_payment_advice_emails(self):
        payment_details = self.payment_details

        for supplier in set([d.supplier for d in payment_details]):
            self.payment_details = list(
                filter(lambda x: x.supplier == supplier, payment_details)
            )
            address = frappe.db.get_value(
                "Supplier", supplier, "supplier_primary_address"
            )
            self.address_display = self.payment_details[0].supplier_name
            if address:
                self.address_display = get_address_display(address)

            out = frappe.attach_print(
                self.doctype,
                self.name,
                file_name="{}_Payment Advice_{}_{}".format(
                    supplier, self.name, self.payment_date
                ),
                print_format="Supplier Payment Advice",
                doc=self,
            )

            _file = frappe.get_doc(
                {
                    "doctype": "File",
                    "file_name": out["fname"],
                    "attached_to_doctype": self.doctype,
                    "attached_to_name": self.name,
                    "is_private": 0,
                    "content": out["fcontent"],
                }
            )
            _file.save(ignore_permissions=True)
            break

        return

        email_template = frappe.get_doc("Email Template", "Supplier Payment Advice")
        frappe.sendmail(
            recipients=supplier_email,
            subject=email_template.subject,
            message=frappe.render_template(email_template.response, self),
            attachments=[out],
        )
