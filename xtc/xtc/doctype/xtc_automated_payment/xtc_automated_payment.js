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
    frm.page.add_menu_item(__("Make Bank csv"), () => {
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

    frm.page.add_menu_item(__("Send Supplier Payment Advice"), () => {
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

    frm.page.add_menu_item(__("Make Bank Summary"), () => {
      return frm
        .call({
          method: "make_bank_summary",
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
        frm.refresh();
      });
  },
});
