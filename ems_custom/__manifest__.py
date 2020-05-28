# -*- encoding: UTF-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today Laxicon Solution.
#    (<http://laxicon.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name': 'School Custom module',
    'summary': """school custom""",
    'version': '11.1.0',
    'author': 'Laxicon Solution',
    'sequence': 1,
    'category': 'School Management',
    'complexity': 'easy',
    'website': 'https://www.laxicon.in',
    'support': 'info@laxicon.in',
    'depends': ['school'],
    'data': [
        'security/ir.model.access.csv',
        'views/discount_view.xml',
        'views/school_standard.xml',
        'views/action_view.xml',
        'views/school_menu.xml',
    ],
    'installable': True,
    'application': True,
}
