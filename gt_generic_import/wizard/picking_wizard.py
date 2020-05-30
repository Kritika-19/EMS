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

class PickingWizard(models.TransientModel):
    _name = 'picking.wizard'
    _description = 'Picking Wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")

    @api.multi
    def import_picking_order(self):

        file_data = False

        if self.select_file and self.data_file:
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
            raise exceptions.Warning(_('Please select file and type of file or picking type'))

        lines = []
        for row in file_data:
            if self.select_file == 'csv' and len(row) != 1:
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            
            if row[0] != "":
                sale = self.env['sale.order'].search([('name', '=', row[0] or "_____________")])
                if not sale:
                    raise ValidationError("Sale Order '%s' is not founded" % row[0])
            else:
                raise ValidationError("Please Assign Sale Order Name.")
            
            sale.action_confirm()
            






































