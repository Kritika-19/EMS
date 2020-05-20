{
    'name': 'Account Report',
    'version': '1.0',
    'website' : '',
    'category': 'Base',
    'summary': 'Account Reports',
    'description': """""",
    'author': 'Shoaib Anwar',
    'depends': ['sale_management',
                'account',
                ],
    'data': [
        'security/ir.model.access.csv',
        'views/bank_statement.xml',
        'views/sale_order.xml',
        'views/custom_move_line.xml',
        'views/generalledger_view.xml',
        'report/report_view.xml',
        'report/sale_report.xml',
        'report/custom_report_statement.xml',
    ],
    'qweb' : [
    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

