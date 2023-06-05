frappe.ui.form.on('Batch', {
	refresh:function(frm) {

		// frm.remove_custom_button('Label Print');
		// let buttonlabel = __("Batch")+ ' ' +frm.doc.batch_id;
		frm.add_custom_button(('W/S label'),function(){
			let url = `/api/method/xtc.label_api.get_icecream_label_print_pdf`;
			let args = {
			  doctype: frm.doc.doctype,
			  docname:frm.doc.name,
			  print_format: 'Ice Cream Printing Label'
		};
		open_url_post(url, args, true);
	});
}
});