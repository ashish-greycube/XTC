# Copyright (c) 2023, Greycube and contributors
# For license information, please see license.txt

import frappe
from xtc.xtc.report import csv_to_columns
from datetime import datetime

def execute(filters=None):
    posting_date_header = get_posting_date_header(filters)
    custom_organization_id_header = get_custom_organization_id_header(filters)
    company_header = get_company_header(filters)
    return get_columns(), get_data(filters, posting_date_header, custom_organization_id_header, company_header)

def get_columns():
    cols = f"""
,header,Data,,100
,dynamic_column,Data,,100
,originating_account_number,Data,,150
,account_currency,Data,,150
,blank_column,Data,,10
,account_currency_2,Data,,120
,blank_column,Data,,10
,posting_date,Data,,120
,blank_column,Data,,10
,blank_column,Data,,10
,employee_bank_account,Data,,120
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,employee_account_id,Data,,120
,blank_column,Data,,10
,bank_code,Text,,120
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,rounded_total,Data,,120
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,transaction_code,Data,,60
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,employee_account_type,Data,,100
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,purpose,Data,,100
,blank_column,Data,,10
,delivery_method,Data,,60
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,email_1,Data,,140
,email_2,Data,,30
,email_3,Data,,30
,email_4,Data,,30
,email_5,Data,,30
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,blank_column,Data,,10
,email_body,Data,,10
"""
    return csv_to_columns(cols)

def get_data(filters, posting_date_header, custom_organization_id_header, company_header):

    header_row = {
        "header": "HEADER",
        "dynamic_column": posting_date_header,
        "originating_account_number": custom_organization_id_header,
        "account_currency": company_header
    }


    data = frappe.db.sql(
        """
SELECT 
    'PAYMENT' AS header,
    'SAL' AS dynamic_column,
    acc.custom_originating_account_number as originating_account_number,
    acc.account_currency as account_currency,'' as blank_column,acc.account_currency as account_currency_2,'' as blank_column, 
    DATE_FORMAT(pe.posting_date, '%%d%%m%%Y') as posting_date,'' as blank_column,'' as blank_column,
    IFNULL(emp.custom_employee_bank_account_name, '') AS employee_bank_account, '' as blank_column, '' as blank_column, '' as blank_column, '' as blank_column,
    IFNULL(emp.custom_employee_account_id, '') AS employee_account_id,  '' as blank_column, IFNULL(CASE WHEN emp.custom_employee_account_type = 'B' THEN emp.custom_bank_code ELSE '' END, '') AS bank_code,
    '' as blank_column,'' as blank_column,'' as blank_column,'' as blank_column,'' as blank_column,'' as blank_column,'' as blank_column,'' as blank_column,'' as blank_column,
    IFNULL(ss.rounded_total, 0) AS rounded_total,'' as blank_column,'' as blank_column,'' as blank_column,'' as blank_column, '22' AS transaction_code,'' as blank_column,
    '' as blank_column,'' as blank_column,'' as blank_column,'' as blank_column,IFNULL(emp.custom_employee_account_type, '') AS employee_account_type,'' as blank_column,
    '' as blank_column,'' as blank_column,'CXSALA' AS purpose,'' as blank_column, IFNULL(CASE WHEN emp.prefered_email != '' THEN 'E' ELSE '' END, '') AS delivery_method,
    '' as blank_column, '' as blank_column, '' as blank_column, '' as blank_column, '' as blank_column, '' as blank_column, '' as blank_column, '' as blank_column,
    IFNULL(emp.prefered_email, '') AS email_1,'' as email_2,'' as email_3,'' as email_4,'' as email_5,'' as blank_column,'' as blank_column,'' as blank_column,
    '' as blank_column,'' as blank_column, ss.custom_email_body_for_bank_file as email_body
FROM 
    `tabPayroll Entry` pe
INNER JOIN 
    `tabAccount` acc ON acc.name = pe.payroll_payable_account
INNER JOIN 
    `tabPayroll Employee Detail` ped ON ped.parent = pe.name
INNER JOIN 
    `tabEmployee` emp ON emp.name = ped.employee
LEFT JOIN 
    `tabSalary Slip` ss ON ss.employee = ped.employee AND ss.payroll_entry = pe.name
{conditions}
GROUP BY
    acc.custom_originating_account_number,
    acc.account_currency,
    pe.posting_date,
    emp.custom_employee_bank_account_name,
    emp.custom_employee_account_id,
    emp.custom_bank_code,
    emp.prefered_email,
    emp.custom_employee_account_type
ORDER BY 
    emp.custom_employee_bank_account_name ASC
                         """.format(
            conditions=get_conditions(filters)
        ),
        filters,
        as_dict=True,
    )

    total_rounded_sum = sum(row.get("rounded_total", 0) for row in data)

    footer_row = {
        "header": "TRAILER", 
        "dynamic_column": len(data), 
        "originating_account_number": total_rounded_sum,
    }

    # data.append(footer_row)
    
    return [header_row] + data + [footer_row] 


def get_posting_date_header(filters):
    """
    Fetch the posting_date of the first matching Payroll Entry to use as the header.
    Format the date as DDMMYYYY.
    """
    posting_date = frappe.db.get_value("Payroll Entry", filters.get("payroll_entry"), "posting_date")
    if posting_date:
        formatted_date = posting_date.strftime("%d%m%Y")
        return formatted_date
    return " "

def get_custom_organization_id_header(filters):
    """
    Fetch the custom_organization_id of the Company linked to the Payroll Entry.
    """
    company = frappe.db.get_value("Payroll Entry", filters.get("payroll_entry"), "company")
    if company:
        custom_organization_id = frappe.db.get_value("Company", company, "custom_organization_id")
        if custom_organization_id:
            return custom_organization_id
    return " "

def get_company_header(filters):
    """
    Set Company in the header
    """
    company = frappe.db.get_value("Payroll Entry", filters.get("payroll_entry"), "company")
    if company:
        return company
    return " "

def get_conditions(filters):
    conditions = []

    if filters.get("payroll_entry"):
        conditions.append("pe.name = %(payroll_entry)s")

    return " where " + " and ".join(conditions) if conditions else ""
