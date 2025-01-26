import frappe


@frappe.whitelist()
def make_sales_invoice_from_sales_order(
    source_name, target_doc=None, ignore_permissions=False
):
    from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice

    doclist = make_sales_invoice(source_name, target_doc, ignore_permissions)
    doclist.posting_date = frappe.db.get_value(
        "Sales Order", source_name, "delivery_date"
    )
    doclist.set_posting_time = 1
    doclist.due_date = doclist.posting_date

    return doclist


@frappe.whitelist()
def make_sales_invoice_from_delivery_note(source_name, target_doc=None):
    from erpnext.stock.doctype.delivery_note.delivery_note import make_sales_invoice

    doc = make_sales_invoice(source_name, target_doc)
    doc.posting_date = frappe.db.get_value("Delivery Note", source_name, "posting_date")
    doc.due_date = doc.posting_date
    doc.set_posting_time = 1

    return doc
