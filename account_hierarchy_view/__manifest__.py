# -*- coding: utf-8 -*-

{
    'name': "Account Hierarchy",
    'summary': """
        Provide Odoo 8 like account hierarchy view in odoo 11
    """,
    'description':"""
        Provide Odoo 8 like account hierarchy view in odoo 11

        show credit, debit and balance in account 
        \n
        allow to select account type view
        \n
        
       can view account in hierarchy structure
        \n
        can be save as PDF
    """,
    
    'author': 'ERP Labz',
    'website': 'http://www.erplabz.com',
    'category': 'Accounting',
    'version': '1.3',
    'depends': ['account'],
    'data': [
        'security/security.xml',
        'views/account_view_inherit.xml',
        'views/account_chart.xml',
        'data/account_data.xml',
        'views/account_parent_template_view.xml',
        'views/report_coa.xml',
        'views/coa_menu.xml',
    ],
    
    'qweb': [
        'static/src/xml/account_backend.xml',
    ],
    "images":['static/description/banner.jpg'],
    'license': 'OPL-1',
    'price': 149.0,
    'currency': 'EUR',
    'installable':True,
    
}
