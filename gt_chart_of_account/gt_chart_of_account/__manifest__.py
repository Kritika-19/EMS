# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name' : 'Globalteckz Chart of Accounts',
    'version' : '1.0',
    'author' : 'Globalteckz',
    'category' : 'Extra Tools',
    'description' : """Globalteckz Chart of Accounts""",
    "summary":"",
    'website': 'https://www.globalteckz.com',
    'license': 'Other proprietary',
    'depends' : ['sale','stock','base','account','account_invoicing'],
    'data': [
        'view/account_account_view.xml',
    ],
    'qweb' : [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
