frappe.ui.form.on("Payroll Entry", {
  refresh: function (frm) {
    frm.add_custom_button(__("DBS SAL"), function () {
      frappe.set_route("query-report", "DBS SAL file", {
        payroll_entry: frm.doc.name,
      });
    });
  },

  start_date: function (frm) {
    update_custom_remarks(frm);
  },
  end_date: function (frm) {
    update_custom_remarks(frm);
  },
});

function update_custom_remarks(frm) {
    if (frm.doc.start_date && frm.doc.end_date) {
      const formatDate = (dateStr) => {
        const date = new Date(dateStr);
        const day = String(date.getDate()).padStart(2, "0"); // Ensure 2-digit format
        const month = String(date.getMonth() + 1).padStart(2, "0"); // Month is 0-indexed
        const year = date.getFullYear();
        return `${day}/${month}/${year}`;
      };
  
      const startDate = formatDate(frm.doc.start_date);
      const endDate = formatDate(frm.doc.end_date);
  
      frm.set_value(
        "custom_remarks",
        `Salary paid from ${startDate} - ${endDate}`
      );
    } else {
      frm.set_value("custom_remarks", "");
    }
  }
  
