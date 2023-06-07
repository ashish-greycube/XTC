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
  setup: function (frm) {
    frm.set_query("supplier", () => {
      return {
        query:
          "xtc.xtc.doctype.xtc_automated_payment.xtc_automated_payment.supplier_query",
        filters: {
          supplier_group: frm.doc.supplier_group,
        },
      };
    });

    frm.set_query("contact", "suppliers", function (doc, cdt, cdn) {
      let child = locals[cdt][cdn];

      return {
        query: "frappe.contacts.doctype.contact.contact.contact_query",
        filters: {
          link_doctype: "Supplier",
          link_name: child.supplier,
        },
      };
    });
  },

  add_custom_buttons: function (frm) {
    frm.add_custom_button(
      __("Draft Payment Entry"),
      () => {
        return frm
          .call({
            method: "make_payment_entry",
            doc: frm.doc,
            args: {},
            freeze: true,
          })
          .then((r) => {
            frappe.timeout(0.5).then(() => {
              frm.reload_doc();
              frappe.msgprint(__("Draft Payment Entries have been created."));
            });
          });
      },
      __("Tools")
    );

    frm.add_custom_button(
      __("Download Bank csv"),
      () => {
        return frm
          .call({
            method: "download_bank_csv",
            doc: frm.doc,
            args: {},
            freeze: true,
          })
          .then((r) => {
            frappe.tools.downloadify(
              r.message,
              null,
              `BankPaymentSummary-${frm.doc.name}`
            );
          });
      },
      __("Tools")
    );

    frm.add_custom_button(
      __("Email Bank Summary"),
      () => {
        return frm
          .call({
            method: "send_bank_summary",
            doc: frm.doc,
            args: {},
            freeze: true,
          })
          .then((r) => {
            frm.reload_doc();
          });
      },
      __("Tools")
    );

    frm.add_custom_button(
      __("Email Supplier Payment Advice"),
      () => {
        return frm
          .call({
            method: "send_supplier_payment_advice_emails",
            doc: frm.doc,
            args: {},
            freeze: true,
          })
          .then((r) => {
            frm.reload_doc();
          });
      },
      __("Tools")
    );

    if (
      frm.doc.docstatus == 1 &&
      frm.doc.payment_entry_status === "Completed"
    ) {
      frm.add_custom_button(
        "Submit & Close Payment",
        () => {
          //
          frm
            .call({
              method: "close_payment",
              doc: frm.doc,
            })
            .then((r) => {
              frm.reload_doc();
            });
        },
        __("Tools")
      );
    }
  },

  refresh: function (frm) {
    if (frm.doc.docstatus == 1) frm.trigger("add_custom_buttons");

    frm.fields_dict.suppliers.grid.update_docfield_property(
      "email_sent",
      "read_only",
      0
    );
  },

  mode_of_payment: function (frm) {
    if (frm.doc.mode_of_payment) {
      frappe.call({
        method:
          "xtc.xtc.doctype.xtc_automated_payment.xtc_automated_payment.get_default_bank_account",
        args: { mode_of_payment: frm.doc.mode_of_payment },
        callback: function (r) {
          if (!r.exc) {
            frm.set_value("paid_from", r.message);
          }
        },
      });
    }
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
    frm.trigger("set_total");
  },

  set_total: function (frm) {
    let total_amount = 0;
    for (const itr of frm.doc.payment_details) {
      total_amount += itr.amount_to_pay;
    }
    frm.set_value("total_amount", total_amount);

    // set supplier totals
    for (const d of frm.doc.suppliers) {
      d.amount_to_pay = frm.doc.payment_details
        .filter((t) => t.supplier == d.supplier)
        .reduce((total, t) => total + t.amount_to_pay, 0);
    }
    frm.refresh_field("suppliers");
  },
});

frappe.ui.form.on("XTC Automated Payment Detail", {
  amount_to_pay: function (frm) {
    frm.trigger("set_total");
  },

  payment_details_remove: function (frm) {
    let suppliers = frm.doc.payment_details.map((r) => r.supplier);
    frm.doc.suppliers = frm.doc.suppliers.filter((t) =>
      suppliers.includes(t.supplier)
    );
    frm.refresh_field("suppliers");
    frm.trigger("set_total");
  },
});

frappe.ui.form.on("Request for Quotation Supplier", {
  suppliers_remove: function (frm) {
    debugger;
    let suppliers = frm.doc.suppliers.map((r) => r.supplier);
    frm.doc.payment_details = frm.doc.payment_details.filter((t) =>
      suppliers.includes(t.supplier)
    );
    frm.refresh_field("payment_details");
    frm.trigger("set_total");
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
