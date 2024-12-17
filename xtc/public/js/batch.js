frappe.ui.form.on('Batch', {
	refresh:function(frm) {

		// frm.remove_custom_button('Label Print');
		// let buttonlabel = __("Batch")+ ' ' +frm.doc.batch_id;
		
		frm.add_custom_button(('W/S label'),function(){
			let url = `/api/method/xtc.label_api.get_icecream_label_print_pdf`;
			let args = {
			  doctype: frm.doc.doctype,
			  docname:frm.doc.name,
			  print_type:'indirectpdf'
		};
		open_url_post(url, args, true);			
	});
	frm.add_custom_button(('PJS'),function(){
		let args = {
			doctype: frm.doc.doctype,
			docname:frm.doc.name,
			print_type:'directpdf'
	  };			
		  frappe.call({
			  method: 'xtc.label_api.get_icecream_label_print_pdf',
			  args: args,
			  async: false,
			  callback: (r) => {
				  console.log(r.message)
				  printJS({printable:r.message, type:'pdf',   onError: function  (error) {
					alert('Error found => ' + error.message)
				  }})
			  },
			  error: (r) => {
				  console.log(r)
				  // on error
			  }
		  })
	})
}
});