import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def execute():
    custom_fields = {
        "Item": [
            dict(
                fieldname="ingredients_cf",
                label="Ingredients",
                fieldtype="Small Text",
                insert_after="description",
            ),
            dict(
                fieldname="custom_section_break",
                label="Nutrition Information",
                fieldtype="Section Break",
                insert_after="ingredients_cf",
            ),        
            dict(
                fieldname="nutrition_information_cf",
                label="Nutrition Information",
                fieldtype="Table",
                options="Nutrition Information",
                insert_after="custom_section_break",
                description="To create sub nutrition, put '- ' in front of name ex : '- Trans Fat'"
                
            ),
            dict(
                fieldname="section_label_print_settings_cf",
                label="Label Print Settings",
                fieldtype="Section Break",
                insert_after="nutrition_information_cf",  
            ), 
            dict(
                fieldname="is_product_halal_cf",
                label="Is Halal Product?",
                fieldtype="Check",
                insert_after="section_label_print_settings_cf",
                default=0,  
            ),
            dict(
                fieldname="col_break_font_size_cf",
                label="",
                fieldtype="Column Break",
                insert_after="is_product_halal_cf",  
            ), 
            dict(
                fieldname="font_size_item_name_cf",
                label="Item Name Font Size(pt)",
                fieldtype="Int",
                insert_after="col_break_font_size_cf",
                default="8",  
            ), 
            dict(
                fieldname="font_size_description_cf",
                label="Description Font Size(pt)",
                fieldtype="Int",
                insert_after="font_size_item_name_cf",
                default="7",  
            ),
            dict(
                fieldname="font_size_ingredients_cf",
                label="Ingredients Font Size(pt)",
                fieldtype="Int",
                insert_after="font_size_description_cf",
                default="6",  
            )     
        ]   
    }

    create_custom_fields(custom_fields, update=True)