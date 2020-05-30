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

class BankAccountWizard(models.TransientModel):
    _name = 'bank.wizard'
    _description = 'Bank Account Wizard'

    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")

    @api.multi
    def import_bank_ac(self):
        account_journal_browse_obj = self.env['account.bank.statement'].browse(self._context.get('active_ids'))
        file_data = False
        if self.select_file and self.data_file:
            if self.select_file == 'csv' :
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",delimiter=",")
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
        
        my_list = []
        for row in file_data:
            if self.select_file == 'csv' and len(row) != 5:
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            if row[0] == "" or row[3] == "":
                raise ValidationError("Please Assign The Label And Date.")
            partner_id_search = self.env['res.partner'].search([('name', '=', row[2] or "_____________")])
            dt = datetime.strptime(row[0], "%d-%m-%Y")
            account_line = {
                            'name': row[3] and row[3] or '/',
                            'partner_id': partner_id_search and partner_id_search.id or False,
                            'amount': row[4] or "",
                            'ref': row[1] or "",
                            'date': dt,
                            }
            my_list.append((0,0,account_line))
        account_journal_browse_obj.write({'line_ids':my_list})








































