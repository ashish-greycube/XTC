import frappe
from frappe import _
from frappe.utils import get_site_url
from frappe.utils.pdf import get_pdf

@frappe.whitelist()
def get_icecream_label_print_pdf(doctype,docname, print_format="Ice Cream Printing Label"):

     return get_label_print_pdf(doctype,docname, print_format)

@frappe.whitelist()
def get_label_print_pdf(doctype,docname, print_format="Ice Cream Printing Label"):

     if doctype=='Batch':
          item_code=frappe.db.get_value(doctype,docname,'item')
          item_name=frappe.db.get_value(doctype,docname,'item_name')
          batch_id=frappe.db.get_value(doctype,docname,'batch_id')
          expiry_date = frappe.db.get_value(doctype,docname,'expiry_date')
          manufacturing_date= frappe.db.get_value(doctype,docname,'manufacturing_date')
    
     elif doctype=='Work Order':

          item_code = frappe.get_value(doctype, docname, 'production_item')
          batches = frappe.get_list('Batch', fields=['name'], filters={'reference_name': docname})
          if batches:
            batch = batches[0]
            batch_doc = frappe.get_doc('Batch', batch.name)
            batch_id = batch_doc.name
            item_name = frappe.db.get_value('Batch', batch_id, 'item_name')
            expiry_date = frappe.db.get_value('Batch', batch_id, 'expiry_date') 
            manufacturing_date = frappe.db.get_value('Batch', batch_id, 'manufacturing_date')
            
          else:
            frappe.throw(_("No Batch found for the Work Order."))


     item=frappe.get_doc('Item',item_code)
     nutrition_information_cf=item.get('nutrition_information_cf')
     description=item.get('description')
     ingredients_cf=item.get('ingredients_cf')
     font_size_item_name_cf=item.get('font_size_item_name_cf')
     font_size_description_cf=item.get('font_size_description_cf')
     font_size_ingredients_cf=item.get('font_size_description_cf')
     is_product_halal_cf=item.get('is_product_halal_cf')

     barcodes = []

     for barcode in item.get('barcodes'):
        if barcode.get('barcode'):
            barcodes.append(barcode.get('barcode'))


     label_settings = frappe.get_single('XTC Label Settings')
     halal_logo = label_settings.get('halal_logo')

     args = {
         
          "item_code": item_code,
          "item_name":item_name,
          "description_":description,
          "ingredients_cf":ingredients_cf,
          "nutrition_information_cf":nutrition_information_cf,
          "batch_id":batch_id,
          "expiry_date_":expiry_date,
          "manufacturing_date":manufacturing_date,
          "barcodes": barcodes,
          "halal_logo": halal_logo,
          "is_product_halal_cf":is_product_halal_cf,
          "font_size_item_name_cf":str(font_size_item_name_cf) + "pt",
          "font_size_description_cf":str(font_size_description_cf) + "pt",
          "font_size_ingredients_cf":str(font_size_ingredients_cf) + "pt"
          
     }
     html = frappe.get_template("xtc/xtc/print_format/ice_cream_label_print_template/ice_cream_printing.html").render(args)

     options={
        "page-width": "120mm",
        "page-height": "50mm",
        "margin-left":"19mm",
        "margin-right":"0mm"        
}
     frappe.local.response.filename = "{name}.pdf".format(
        name=docname.replace(" ", "-").replace("/", "-")
    )
     frappe.local.response.filecontent = get_pdf(html,options)
     frappe.local.response.type = "pdf"