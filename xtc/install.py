import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    print("Creating fields for XTC Automated Payment:")
    custom_fields = {
        "Supplier": [
            dict(
                fieldname="supplier_party_account_type_cf",
                label="Supplier Party Account Type",
                fieldtype="Select",
                options="\nA\nF\nE\nM",
                insert_after="is_internal_supplier",
                description="A - Account Number, F - FPS ID, E - Email Address, M - Mobile Number"),
            dict(
                fieldname="supplier_party_bank_code_cf",
                label="Supplier Party Bank Code",
                fieldtype="Link",
                options="Supplier Party Bank Code",
                insert_after="supplier_party_account_type_cf",
            ),
            dict(
                fieldname="supplier_party_account_id_cf",
                label="Supplier Party Account ID",
                fieldtype="Data",
                insert_after="supplier_party_bank_code_cf",
            ),
            dict(
                fieldname="supplier_party_name_cf",
                label="Supplier Party Name",
                fieldtype="Data",
                insert_after="supplier_party_account_id_cf",
            ),
        ]}

    create_custom_fields(custom_fields, update=True)
