# Copyright (c) 2023, GreyCube Technologies and Contributors
# See license.txt

import frappe
import unittest

class TestXTCAutomatedPayment(unittest.TestCase):
	pass


def send_supplier_payment_advice_emails():
	frappe.get_doc("XTC Automated Payment","XTCPAY-5").send_supplier_payment_advice_emails()
	