frappe.ui.form.on('Payroll Entry', {
    refresh: function(frm) {
        frm.add_custom_button(__('DBS SAL'), function() {
            frappe.set_route('query-report', 'DBS SAL file', {
                payroll_entry: frm.doc.name
            });
        });
    }
});
