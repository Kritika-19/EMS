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

class ProductWizard(models.TransientModel):
    _name = 'product.wizard'
    _description = 'Product Wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")

    @api.multi
    def import_product_order(self):
        product_main_obj = self.env['product.product']
        file_data = False

        if self.select_file and self.data_file:
            if self.select_file == 'csv':
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar="," ,delimiter=",")
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
            raise exceptions.Warning(_('Please select file and type of file or picking type'))
        
        for row in file_data:
            tax_list = []
            if self.select_file == 'csv' and len(row) != 14:
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            if row[0] == "" or row[3] == "":
                raise ValidationError("Please Assign The Product Name And Type.")
            search_product = product_main_obj.search([('name','=',row[0] or "_____________")])
            uom_ids = self.env['product.uom'].search([('name', '=', row[5] or "_____________")])
            uom_po_ids = self.env['product.uom'].search([('name', '=', row[6] or "_____________")])
            tax_id = self.env['account.tax'].search([('name', '=', row[15] or "_____________")])
            tax_list.append(tax_id.id)
            if not uom_ids:
                raise ValidationError("Uom ids  '%s' is not founded" % row[5])
            
            if not uom_po_ids:
                raise ValidationError("Purchase Uom ids  '%s' is not founded" % row[6])
            
            categ_id_ids = self.env['product.category'].search([('name','=',row[2] or "_____________")])
            if not categ_id_ids:
                raise ValidationError("categ_ids  '%s' is not founded" % row[2])
            
            if not tax_id:
                raise ValidationError("Tax id  '%s' is not founded" % row[15])
            
            product_obj = self.env['product.product']
            product_fields = product_obj.fields_get()
            pro_def_val = product_obj.default_get(product_fields)
            new_pro_up = pro_def_val.copy()
            if row[4] != "" :
                new_pro_up.update({
                                'name': row[0],
                                'default_code': row[1] or "",
                                'type' : row[3],
                                'list_price': row[7] or "",
                                'standard_price': row[8] or "",
                                'categ_id': categ_id_ids.id,
                                'uom_id' : uom_ids.id,
                                'uom_po_id' : uom_po_ids.id,
                                'weight' : row[9] != "" and float(row[9]) or "",
                                'volume' : row[10] != "" and float(row[10]) or "",
                                'barcode' : row[4] != "" and row[4] or "",
                                'taxes_id' : [( 6, 0, tax_list)],
#                                 'latin_name': row[14] or "",
                                })
            elif row[4] == "" :
                new_pro_up.update({
                                'name': row[0],
                                'default_code': row[1] or "",
                                'type' : row[3],
                                'list_price': row[7] or "",
                                'standard_price': row[8] or "",
                                'categ_id': categ_id_ids.id,
                                'uom_id' : uom_ids.id,
                                'uom_po_id' : uom_po_ids.id,
                                'weight' : row[9] != "" and float(row[9]) or "",
                                'volume' : row[10] != "" and float(row[10]) or "",
                                'taxes_id' : [( 6, 0, tax_list)],
#                                 'latin_name': row[14] or "",
                                })
            
            if search_product:
                product_created_id = search_product.write(new_pro_up)
                if search_product.type in ['product'] and row[11] != '' and row[12] != '':    
                    product = self.env['product.product'].search([('name', '=', row[0] or "_____________")])
                    stock_location = self.env['stock.location'].search([('id', '=', int(row[12]) or "_____________")])
                    if not stock_location:
                        raise ValidationError("Stock Location '%s' is not founded" % row[12])
                    if row[13] == '':
                        self.env['stock.quant']._update_available_quantity(product, stock_location, float(row[11]))
                    elif row[13] != '':
                        lot = self.env['stock.production.lot'].search([('id', '=', int(row[13]) or "_____________")])
                        if not lot:
                            raise ValidationError("Production Lot id '%s' is not founded" % row[13])
                        self.env['stock.quant']._update_available_quantity(product, stock_location, float(row[11]),lot_id=lot)
            else:
                product_created_id = product_main_obj.create(new_pro_up)
                if product_created_id.type in ['product'] and row[11] != '' and row[12] != '':    
                    product = self.env['product.product'].search([('name', '=', row[0] or "_____________")])
                    stock_location = self.env['stock.location'].search([('id', '=', int(row[12]) or "_____________")])
                    if not stock_location:
                        raise ValidationError("Stock Location '%s' is not founded" % row[12])
                    if row[13] == '':
                        self.env['stock.quant']._update_available_quantity(product, stock_location, float(row[11]))
                    elif row[13] != '':
                        lot = self.env['stock.production.lot'].search([('id', '=', int(row[13]) or "_____________")])
                        if not lot:
                            raise ValidationError("Production Lot id '%s' is not founded" % row[13])
                        self.env['stock.quant']._update_available_quantity(product, stock_location, float(row[11]),lot_id=lot)






































