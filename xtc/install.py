import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    print("Creating fields for XTC Automated Payment:")
    custom_fields = {
        "Supplier": [
            dict(
                fieldname="second_party_account_type_cf",
                label="Second Party Account Type",
                fieldtype="Data",
                insert_after="is_internal_supplier",
            ),
            dict(
                fieldname="second_party_bank_code_cf",
                label="Second Party Bank Code",
                fieldtype="Data",
                insert_after="second_party_account_type_cf",
            ),
            dict(
                fieldname="second_party_account_id_cf",
                label="Second Party Account ID",
                fieldtype="Data",
                insert_after="second_party_bank_code_cf",
            ),
            dict(
                fieldname="second_party_name_cf",
                label="Second Party Name",
                fieldtype="Data",
                insert_after="second_party_account_id_cf",
            ),
        ]
    }

    create_custom_fields(custom_fields, update=True)
