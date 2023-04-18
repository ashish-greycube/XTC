import frappe

def validate(doc, method):
    if frappe.conf.get("override_email_id"):
        for d in doc.recipients:
            d.recipient = frappe.conf.get("override_email_id")