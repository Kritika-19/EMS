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
    'name' : 'Odoo all import for BOM, Sales, Purchase, Invoice, Inventory, Customer/Supplier Payment, Bank Statement, Journal Entry, Picking, Product, Customer.',
    'version' : '1.0',
    'author' : 'Globalteckz',
    'category' : 'Extra Tools',
    'description' : """
Import BOM,
import all in one
all in one
one
all
all import
import all
Import sales
Import Sales order
Import purchase
Import purchase order
Import invoice
Import products
Import Inventory
Import Payments
Import Bank Statement 
import statement
Import Journal entry
Import Picking
Import stock
import stock with serial number
import sales order line
import purchase order line
import serial number
import lot
Import Customer 
Import Supplier
excel bom
Import excel bom
xls bom
Import xls bom
csv bom
Import csv bom
excel sales
import excel sales
xls sales
import xls sales
csv sales
import csv sales
excel sales order
import excel sales order
xls sales order
import xls sales order
csv sales order
import csv sales order
excel purchase
import excel purchase
xls purchase
import xls purchase
csv purchase
import csv purchase
excel purchase order
import excel purchase order
xls purchase order
import xls purchase order
csv purchase order
import csv purchase order
excel invoice
import excel invoice
xls invoice
import xls invoice
csv invoice
import csv invoice
excel products
xls products
csv products
import excel products
import xls products
import csv products
excel inventory
xls inventory
csv inventory
import excel inventory
import xls inventory
import csv inventory
excel payments
xls payments
csv payments
import excel payments
import xls payments
import csv payments
excel bank statement
xls bank statement
csv bank statement
import excel bank statement
import xls bank statement
import csv bank statement
excel statement
xls statement
csv statement
import excel statement
import xls statement
import csv statement
excel journal entry
xls journal entry
csv journal entry
import excel journal entry
import xls journal entry
import csv journal entry
excel picking
xls picking
csv picking
import excel picking
import xls picking
import csv picking
excel stock
xls stock
csv stock
import excel stock
import xls stock
import csv stock
excel stock with serial number
xls stock with serial number
csv stock with serial number
import excel stock with serial number
import xls stock with serial number
import csv stock with serial number
excel sales order line
xls sales order line
csv sales order line
import excel sales order line
import xls sales order line
import csv sales order line
excel purchase order line
xls purchase order line 
csv purchase order line 
import excel purchase order line
import xls purchase order line 
import csv purchase order line 
excel serial number
xls serial number
csv serial number
import excel serial number
import xls serial number
import csv serial number
excel lot
xls lot
csv lot
import excel lot
import xls lot
import csv lot
excel customer
xls customer
csv customer 
import excel customer
import xls customer
import csv customer 
excel supplier
xls supplier
csv supplier
import excel supplier
import xls supplier
import csv supplier
import all csv
with different scenario as per your business requirements
""",
    "summary":"This Module can be used to import your BOM, Sales, Purchase, Invocing, products,inventory, payments",
    'website': 'https://www.globalteckz.com',
    "price": "99.00",
    "currency": "EUR",
    'license': 'Other proprietary',
    'images': ['static/description/Banner.jpg'],
    'depends' : ['sale_management','sale','stock','account_check_printing','purchase','base','mrp', 'account','account_invoicing','l10n_us'],
    'data': [
        'view/import_data_view.xml',
    ],
    'qweb' : [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
