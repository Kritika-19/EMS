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

class InventoryWizard(models.TransientModel):
    _name = 'inventory.wizard'
    _description = 'Inventory Wizard'

    inv_name = fields.Char(string='Inventory Name')
    loc_name = fields.Many2one('stock.location',string='Location')
    file_type = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select')
    imp_product_by = fields.Selection([('barcode', 'Barcode'), ('code', 'Code'), ('name', 'Name')], string='Import Product By')
    ser_no_lot_expi = fields.Boolean(string="Import Serial/Lot number with Expiry Date")
    data_file = fields.Binary(string="File")

    @api.multi
    def import_inventory(self):
        if self.file_type and self.data_file:
            if self.file_type == 'csv':
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.file_type == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or picking type'))
        
        product_obj = self.env['product.product']
        inventory_obj = self.env['stock.inventory']
        inventory_fields = inventory_obj.fields_get()
        inventory_def_val = inventory_obj.default_get(inventory_fields)
        new_inventory_val = inventory_def_val.copy()
        new_inventory_val.update({
                                'name': self.inv_name,
                                'state': 'confirm',
                                'location_id': self.loc_name.id,
                                })
        final_created_id = inventory_obj.create(new_inventory_val)
        for row in file_data:
            if self.file_type == 'csv' and len(row) != 4:
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            prod_lot_obj = self.env['stock.production.lot']
            new_lot_serial = self.env['stock.production.lot']
            prod_lot_fields = prod_lot_obj.fields_get()
            prod_lot_obj_def_val = prod_lot_obj.default_get(prod_lot_fields)
            new_inventory_line_val_ids = prod_lot_obj_def_val.copy()
            inventory_line_obj = self.env['stock.inventory.line']
            inventory_line_fields = inventory_line_obj.fields_get()
            inventory_line_def_val = inventory_line_obj.default_get(inventory_line_fields)
            new_inventory_line_val = inventory_line_def_val.copy()
            date = datetime.strptime(row[3], "%d-%m-%Y")
            
            if self.imp_product_by == "code":
                product_id = product_obj.search([('default_code', '=', row[0] or "_____________")])
                if not product_id:
                    raise ValidationError("Product '%s' is not founded" % row[0])
            elif self.imp_product_by == "barcode":
                product_id = product_obj.search([('barcode', '=', int(row[0]) or "_____________")])
                if not product_id:
                    raise ValidationError("Product '%s' is not founded" % row[0])
            elif self.imp_product_by == "name":
                product_id = product_obj.search([('name', '=', row[0] or "_____________")])
                if not product_id:
                    raise ValidationError("Product '%s' is not founded" % row[0])
            else:
                raise exceptions.Warning(_('Please select product by'))
            
            stock_prod_lot_obj = self.env['stock.production.lot'].search([('name','=',row[2] or "_____________")])
            if self.ser_no_lot_expi == True and stock_prod_lot_obj.id == False:
                new_inventory_line_val_ids.update({
                                                'name': int(row[2]) or '',
                                                'product_id': product_id.id,
                                                'life_date': date or '',
                                                })
                new_lot_serial = prod_lot_obj.create(new_inventory_line_val_ids)
            
            new_inventory_line_val.update({
                                        'inventory_id': final_created_id.id,
                                        'product_id': product_id.id,
                                        'product_qty': row[1] or '',
                                        'location_id': self.loc_name.id,
                                        'prod_lot_id': stock_prod_lot_obj.id or new_lot_serial.id or False,
                                        })
            final_line = inventory_line_obj.create(new_inventory_line_val)
        final_created_id.action_done()
                




















