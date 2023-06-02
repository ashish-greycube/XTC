import frappe
import pyqrcode
from frappe.utils import get_url_to_form,cstr
from pyqrcode import QRCode

@frappe.whitelist()
def get_qr_code(doctype,docname,scale):
    # qr_text=get_url_to_form(doctype,docname)
    qr_text=cstr(docname)
    label=pyqrcode.create(qr_text).png_as_base64_str(scale=scale, quiet_zone=1)
    return label
