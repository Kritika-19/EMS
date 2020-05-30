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

class OpeningAccountMoveWizard(models.TransientModel):
    _inherit = 'account.opening'

    data_file = fields.Binary(string="File")

    @api.multi
    def import_journal(self):
        account_journal_browse_obj = self
        file_data = False
        if self.data_file:
            file_datas = base64.decodestring(self.data_file)
            workbook = xlrd.open_workbook(file_contents=file_datas)
            sheet = workbook.sheet_by_index(0)
            result = []
            data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
            data.pop(0)
            file_data = data
        else:
            raise exceptions.Warning(_('Please select file.'))
        
        my_list = []
        for row in file_data:
            partner_id_search = self.env['res.partner']
            account_id_search = self.env['account.account'].search([('code', '=', int(row[1]) or "_____________")])
            if not account_id_search:
                raise ValidationError("Account '%s' is not founded" % int(row[1]))
            
            if row[2] != "":
                partner_id_search = self.env['res.partner'].search([('name', '=', row[2] or "_____________")])
                if not partner_id_search:
                    raise ValidationError("Partner '%s' is not founded" % row[2])
            
            account_line = {
                            'name': row[0] or '/',
                            'account_id': account_id_search.id,
                            'partner_id': partner_id_search and partner_id_search.id or False,
                            'move_id': account_journal_browse_obj.id,
                            'debit': float(row[4] or 0),
                            'credit': float(row[5] or 0),
                            }
            my_list.append((0,0,account_line))
        account_journal_browse_obj.write({'opening_move_line_ids':my_list})































