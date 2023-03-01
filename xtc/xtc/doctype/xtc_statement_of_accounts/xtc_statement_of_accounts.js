// Copyright (c) 2023, GreyCube Technologies and contributors
// For license information, please see license.txt

frappe.ui.form.on('XTC Statement Of Accounts', {
	view_properties: function(frm) {
		frappe.route_options = {doc_type: 'Customer'};
		frappe.set_route("Form", "Customize Form");
	},
	refresh: function(frm){
		if(!frm.doc.__islocal) {
			frm.add_custom_button(__('Send Emails'), function(){
				if (frm.is_dirty()) frappe.throw(__("Please save before proceeding."))
				frappe.call({
					method: "xtc.xtc.doctype.xtc_statement_of_accounts.xtc_statement_of_accounts.send_emails",
					args: {
						"document_name": frm.doc.name,
					},
					callback: function(r) {
						if(r && r.message) {
							frappe.show_alert({message: __('Emails Queued'), indicator: 'blue'});
						}
						else{
							frappe.msgprint(__('No Records for these settings.'))
						}
					}
				});
			});
			frm.add_custom_button(__('Download'), function(){
				if (frm.is_dirty()) frappe.throw(__("Please save before proceeding."))
				
				let url = frappe.urllib.get_full_url(
					'/api/method/xtc.xtc.doctype.xtc_statement_of_accounts.xtc_statement_of_accounts.download_statements?'
					+ 'document_name='+encodeURIComponent(frm.doc.name))
				var w = window.open(
					frappe.urllib.get_full_url(url)
					
				  );
				  if (!w) {
					frappe.msgprint(__("Please enable pop-ups"));
					return;
				  }
														  
				// return $.ajax({
				// 	url: url,
				// 	type: 'GET',
				// 	async: true,
				// 	success: function(result) {
				// 		if(jQuery.isEmptyObject(result)){
				// 			frappe.msgprint(__('No Records for these settings.'));
				// 		}
				// 		else{
				// 			window.location = result;
				// 			console.log(result)
				// 			// btn_download.prop("disabled", false);
				// 		}
				// 	},
				// }).always(function() {
				// 	btn_download.prop("disabled", false);
				// });						
		

			});
		}
	},
	onload: function(frm) {
		if(frm.doc.__islocal){
			frm.set_value('to_date', frappe.datetime.get_today());
		}
	},
	customer_collection: function(frm){
		frm.set_value('collection_name', '');
		if(frm.doc.customer_collection){
			frm.get_field('collection_name').set_label(frm.doc.customer_collection);
		}
	},
	frequency: function(frm){
		if(frm.doc.frequency != ''){
			frm.set_value('start_date', frappe.datetime.get_today());
		}
		else{
			frm.set_value('start_date', '');
		}
	},
	fetch_customers: function(frm){
		if(frm.doc.collection_name){
			frappe.call({
				method: "xtc.xtc.doctype.xtc_statement_of_accounts.xtc_statement_of_accounts.fetch_customers",
				args: {
					'customer_collection': frm.doc.customer_collection,
					'collection_name': frm.doc.collection_name,
					'primary_mandatory': frm.doc.primary_mandatory
				},
				callback: function(r) {
					if(!r.exc) {
						if(r.message.length){
							frm.clear_table('customers');
							for (const customer of r.message){
								var row = frm.add_child('customers');
								row.customer = customer.name;
								row.primary_email = customer.primary_email;
								row.billing_email = customer.billing_email;
							}
							frm.refresh_field('customers');
						}
						else{
							frappe.throw(__('No Customers found with selected options.'));
						}
					}
				},
				freeze: true,
				freeze_message: __('Fetching Customers.....')				
			});
		}
		else {
			frappe.throw('Enter ' + frm.doc.customer_collection + ' name.');
		}
	}
});

frappe.ui.form.on('XTC Statement Of Accounts Customer', {
	customer: function(frm, cdt, cdn){
		var row = locals[cdt][cdn];
		if (!row.customer){
			return;
		}
		frappe.call({
			method:'xtc.xtc.doctype.xtc_statement_of_accounts.xtc_statement_of_accounts.get_customer_emails',
			args: {
				'customer_name': row.customer,
				'primary_mandatory': frm.doc.primary_mandatory
			},
			callback: function(r){
				if(!r.exe){
					if(r.message.length){
						frappe.model.set_value(cdt, cdn, "primary_email", r.message[0])
						frappe.model.set_value(cdt, cdn, "billing_email", r.message[1])
					}
					else {
						return
					}
				}
			}
		})
	}
});
