// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

frappe.ui.form.on("Payment Entry", {
  refresh: function (frm) {
    frm.ignore_doctypes_on_cancel_all = ["XTC Automated Payment"];
  },
});
