from . import __version__ as app_version

app_name = "xtc"
app_title = "XTC"
app_publisher = "GreyCube Technologies"
app_description = "XTC customizations"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "admin@greycube.in"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/xtc/css/xtc.css"
# app_include_js = "/assets/xtc/js/xtc.js"
# app_include_css = "/assets/xtc/css/print.min.css"
app_include_js = "/assets/xtc/js/print.min.js"
# include js, css files in header of web template
# web_include_css = "/assets/xtc/css/xtc.css"
# web_include_js = "/assets/xtc/js/xtc.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "xtc/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Supplier": "public/js/supplier.js",
    "Payment Entry": "public/js/payment_entry.js",
    "Batch":"public/js/batch.js",
    "Work Order":"public/js/work_order.js"
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

jenv = {
	"methods": [
		"get_qr_code:xtc.utils.jinja.get_qr_code"
	]
}


# Installation
# ------------



# before_install = "xtc.install.before_install"
after_migrate = "xtc.install.after_install"


# Uninstallation
# ------------

# before_uninstall = "xtc.uninstall.before_uninstall"
# after_uninstall = "xtc.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "xtc.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
    "Email Queue": {"validate": "xtc.override_email.validate"},
    "Payment Entry": {
        "before_cancel": "xtc.xtc.doctype.xtc_automated_payment.xtc_automated_payment.before_cancel_payment_entry"
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"xtc.tasks.all"
# 	],
# 	"daily": [
# 		"xtc.tasks.daily"
# 	],
# 	"hourly": [
# 		"xtc.tasks.hourly"
# 	],
# 	"weekly": [
# 		"xtc.tasks.weekly"
# 	]
# 	"monthly": [
# 		"xtc.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "xtc.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
    "erpnext.selling.doctype.sales_order.sales_order.make_sales_invoice": "xtc.xtc.doc_events.make_sales_invoice_from_sales_order",
    "erpnext.stock.doctype.delivery_note.delivery_note.make_sales_invoice": "xtc.xtc.doc_events.make_sales_invoice_from_delivery_note",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "xtc.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "{doctype_1}",
        "filter_by": "{filter_by}",
        "redact_fields": ["{field_1}", "{field_2}"],
        "partial": 1,
    },
    {
        "doctype": "{doctype_2}",
        "filter_by": "{filter_by}",
        "partial": 1,
    },
    {
        "doctype": "{doctype_3}",
        "strict": False,
    },
    {"doctype": "{doctype_4}"},
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"xtc.auth.validate"
# ]

# override_email_send = "xtc.override_email_send"
