// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Supplier", {
  supplier_party_account_type_cf: function (frm) {
    let account_type = frm.doc.supplier_party_account_type_cf || "";

    frm.set_df_property(
      "supplier_party_bank_code_cf",
      "reqd",
      account_type == "A" ? 1 : 0
    );

    frm.set_df_property(
      "supplier_party_bank_code_cf",
      "hidden",
      account_type == "F" ? 1 : 0
    );

    if (account_type === "F") {
      frm.set_value("supplier_party_bank_code_cf", null);
    }
  },

  validate: function (frm) {
    let account_id = frm.doc.supplier_party_account_id_cf || "";
    if (account_id) {
      switch (frm.doc.supplier_party_account_type_cf) {
        case "A":
          if (
            !frappe.utils.validate_type(account_id, "digits") ||
            account_id.length > 12
          ) {
            frappe.throw(
              __(
                "Please set a valid Account Number (number upto 12 digits) for Supplier Account ID."
              )
            );
          }
          break;
        case "E":
          if (!frappe.utils.validate_type(account_id, "email")) {
            frappe.throw(
              __("Please set a valid email for Supplier Account ID.")
            );
          }
          break;
        case "M":
          if (!/^\d{8}$/.test(account_id))
            frappe.throw(
              __(
                "Please set a valid mobile number (XXXXXXXX) of 8 digits for Supplier Account ID."
              )
            );
          break;
        default:
          break;
      }
    }
  },
});
