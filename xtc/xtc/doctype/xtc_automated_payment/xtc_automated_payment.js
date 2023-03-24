// Copyright (c) 2023, GreyCube Technologies and contributors
// For license information, please see license.txt

const bank_file_header = [
  [
    "Second Party Account Type",
    "Second Party Bank Code",
    "Second Party Account ID",
    "Second Party Name",
    "Amount",
    "Particular ID",
  ],
];

frappe.ui.form.on("XTC Automated Payment", {
  refresh: function (frm) {
    frm.page.add_menu_item(__("Download Bank csv"), () => {
      return frm
        .call({
          method: "download_bank_csv",
          doc: frm.doc,
          args: {},
        })
        .then((r) => {
          frappe.tools.downloadify(r.message, null, `Payment_Summary_for_Bank`);
        });
    });

    frm.page.add_menu_item(__("Email Supplier Payment Advice"), () => {
      return frm
        .call({
          method: "send_supplier_payment_advice_emails",
          doc: frm.doc,
          args: {},
        })
        .then((r) => {
          frm.reload_doc();
        });
    });

    frm.page.add_menu_item(__("Email Bank Summary"), () => {
      return frm
        .call({
          method: "send_bank_summary",
          doc: frm.doc,
          args: {},
        })
        .then((r) => {
          frm.reload_doc();
        });
    });
  },
  fetch_accounts_payable: function (frm) {
    return frm
      .call({
        method: "_get_accounts_payable",
        doc: frm.doc,
        args: {},
        freeze: 1,
        freeze_message: __("Fetching Payments", []),
      })
      .then((r) => {
        frm.trigger("set_supplier_detail");
        frm.refresh();
      });
  },
  set_supplier_detail: function (frm) {
    let suppliers = [];

    for (const itr of frm.doc.payment_details) {
      suppliers = frm.doc.suppliers.map((t) => t.supplier);
      if (!suppliers.includes(itr.supplier)) {
        let d = frm.add_child("suppliers", {
          supplier: itr.supplier,
        });
        frm.script_manager.trigger("supplier", d.doctype, d.name);
      }
    }
    frm.refresh_field("suppliers");
  },
});

frappe.ui.form.on("Request for Quotation Supplier", {
  supplier: function (frm, cdt, cdn) {
    var d = locals[cdt][cdn];
    frappe.db
      .get_value("Supplier", d.supplier, [
        "supplier_primary_contact",
        "email_id",
      ])
      .then((r) => {
        if (r.message) {
          frappe.model.set_value(
            cdt,
            cdn,
            "contact",
            r.message.supplier_primary_contact
          );
          frappe.model.set_value(cdt, cdn, "email_id", r.message.email_id);
        }
      });
  },
});
