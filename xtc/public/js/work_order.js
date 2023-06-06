frappe.ui.form.on('Work Order', {

    refresh: function(frm) {
        frappe.db.get_list('Batch', {
            fields: ['name'],
            filters: {
                reference_name: frm.doc.name
            }
        }).then(function(batch_list) {
            if (batch_list && batch_list.length > 0) {
                let batch_docname = batch_list[0].name; 
                frm.add_custom_button("Batch" +" " +batch_docname, function() {
                    let url = `/api/method/xtc.label_api.get_icecream_label_print_pdf`;
                    let args = {
                        doctype: frm.doc.doctype,
                        docname: frm.doc.name,
                        print_type:'indirectpdf'
                    };
                    open_url_post(url, args, true);
                });
            }
            else{
                frm.add_custom_button("No Batch", function(){
                frappe.msgprint("No batch found for this work order to print label")
            })
            }
        });
    }
});