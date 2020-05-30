# -*- coding: utf-8 -*-
{
    'name': "Accounting Extension",

    'summary': 'Extension in Accounting',
    
    'description' : """
        * enable accounting features
        * enable canceling entries by defaults 
        * contacts (Account Receivable / Account Payable) company domain
        * product (Income Account / Expense Account) company domain  
        * invoice multiple company account & journal check 
    """,

    "author": "Openinside",
    "license": "OPL-1",
    'website': "https://www.open-inside.com",
    "price" : 0.0,
    "currency": 'EUR',
    'category': 'Accounting',
    'version': '11.0.1.1.0',

    # any module necessary for this one to work correctly
    'depends': ['account', 'account_cancel'],

    # always loaded
    'data': [
        'security/group.xml',
        'view/account_journal.xml',
        'view/product_template.xml',
        'view/product_category.xml',
        'view/action.xml',
        'view/menu.xml'
        
    ],    
    'pre_init_hook' : 'pre_init_hook',
    'odoo-apps' : True      
}