# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
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

from odoo.exceptions import UserError, ValidationError
from odoo import exceptions, fields, models ,api, _
from odoo.tools import pycompat, DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta,date
from tempfile import TemporaryFile
from collections import Counter
from xlrd import open_workbook
from calendar import monthrange
import collections
import calendar
import base64
import copy
import xlrd
import csv
import sys
import io

class PurchaseWizard(models.TransientModel):
    _name = 'purchase.wizard'
    _description = 'Purchase Wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")
    name = fields.Char('File name')
    state_stage = fields.Selection([('draft', 'Draft'), ('purchase', 'Purchase')], string='Import State')

    @api.multi
    def import_purchase_order(self):
        line_vals ={}
        date_planned = datetime.now()
        payment_term = False
        fiscal_position = False
        incoterm = False
        salesperson_obj = self.env['res.users']
        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']
        file_data = False
        
        if self.select_file and self.data_file and self.state_stage:
            if self.select_file == 'csv' :
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)),quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.select_file == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or sequence'))
        
        for row in file_data:
            ids =[]
            if self.select_file == 'csv' and len(row) != 13:
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            tax_search = self.env['account.tax'].search([('name', '=', row[8]),('type_tax_use', '=', 'sale')])
            
            if row[0] != "":
                partner = self.env['res.partner'].search([('name', '=', row[0] or "_____________")])
                if not partner:
                    raise ValidationError("Vendor '%s' is not founded" % row[0])
            else:
                raise ValidationError("Please Assign Vendor Name.")
            
            if row[1] != "":
                currency = self.env['res.currency'].search([('name', '=', row[1] or "_____________")])
                if not currency:
                    raise ValidationError("Currency '%s' is not founded" % row[1])
            else:
                raise ValidationError("Please Assign Currency.")
            
            if row[4] != "":
                uom = self.env['product.uom'].search([('name', '=', row[4] or "_____________")])
                if not uom:
                    raise ValidationError("UOM '%s' is not founded" % row[4])
            else:
                raise ValidationError("Please Assign UOM.")
            
            if row[10] != "":
                payment_term = self.env['account.payment.term'].search([('name', '=', row[10] or "_____________")])
                if not payment_term:
                    raise ValidationError("Payment Terms '%s' is not founded" % row[10])
                
            if row[11] != "":
                fiscal_position = self.env['account.fiscal.position'].search([('name', '=', row[11] or "_____________")])
                if not fiscal_position:
                    raise ValidationError("Fiscal Position '%s' is not founded" % row[11])
            
            if row[12] != "":
                incoterm = self.env['stock.incoterms'].search([('name', '=', row[12] or "_____________")])
                if not incoterm:
                    raise ValidationError("Incoterms '%s' is not founded" % row[12])
            
            dt = datetime.strptime(row[7], "%d-%m-%Y")
            if row[9] != "":
                date_planned = datetime.strptime(row[9], "%d-%m-%Y")
            purchase_vals = {
                            'partner_id': partner.id or False,
                            'currency_id': currency and currency.id or False,
                            'date_order': dt,
                            'partner_ref': row[8] or "",
                            'date_planned': date_planned or datetime.now(),
                            'payment_term_id': payment_term and payment_term.id or False,
                            'fiscal_position_id': fiscal_position and fiscal_position.id or False,
                            'incoterm_id': fiscal_position and incoterm.id or False,
                            }
            
            purchase = purchase_obj.create(purchase_vals)
            if row[2] != "":
                for pro in row[2].split(";"):
                    product = self.env['product.product'].search([('id', '=', pro or "_____________")])
                    if not product:
                        raise ValidationError("Product '%s' is not founded" % pro)
            
                    line_vals ={
                                "order_id":purchase.id,
                                'name': product.name,
                                'date_planned':datetime.now(),
                                'product_id': product.id,
                                'product_qty':  1,
                                'product_uom': product.uom_id.id,
                                'price_unit':  1,
                                'taxes_id': [(6, 0, tax_search.ids)]
                                }
                    purchase_line_rec = purchase_line_obj.create(line_vals)
                    ids.append(purchase_line_rec.id)
                
            else:
                raise ValidationError("Please Assign Product.")
            
            if row[3] != "" and type(row[3]) in [str]:
                i = 0
                for id in ids:
                    list = row[3].split(";")
                    order_line = self.env["purchase.order.line"].browse(id)
                    order_line.product_qty = list[i]
                    i = i+1
            else:
                for id in ids:
                    order_line = self.env["purchase.order.line"].browse(id)
                    order_line.product_qty = row[3]
                     
            if row[5] != "" and type(row[5]) in [str]:
                j = 0
                for id in ids:
                    list = row[5].split(";")
                    order_line = self.env["purchase.order.line"].browse(id)
                    order_line.price_unit = list[j]
                    j = j+1
            else:
                for id in ids:
                    order_line = self.env["purchase.order.line"].browse(id)
                    order_line.price_unit = row[5]
            
            if self.state_stage == 'purchase':
                purchase.button_confirm()
                        
        return True









































