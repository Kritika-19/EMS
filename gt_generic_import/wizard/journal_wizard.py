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

class JournalWizard(models.TransientModel):
    _name = 'journal.wizard'
    _description = 'Journal Wizard'

    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")

    @api.multi
    def import_journal(self):
        account_journal_browse_obj = self.env['account.move'].browse(self._context.get('active_ids'))
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
            partner_id_search = self.env['res.partner']
            if self.select_file == 'csv' and len(row) != 9:
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            
            account_id_search = self.env['account.account'].search([('code', '=', int(row[8]) or "_____________")])
            if not account_id_search:
                raise ValidationError("Account '%s' is not founded" % int(row[8]))
            
            if row[1] != "":
                partner_id_search = self.env['res.partner'].search([('name', '=', row[1] or "_____________")])
                if not partner_id_search:
                    raise ValidationError("Partner '%s' is not founded" % row[1])
            
            currency__find = self.env['res.currency'].search([('name', '=', row[7] or "_____________")])
            if not currency__find:
                raise ValidationError("Currency '%s' is not founded" % row[7])
            
            search_analytic = self.env['account.analytic.account'].search([('name', '=', row[2] or "_____________")])
            if not search_analytic:
                raise ValidationError("Analytic Account '%s' is not founded" % row[2])
            
            dt = datetime.strptime(row[3], "%d-%m-%Y")
            account_line = {
                            'name': row[0] or '/',
                            'account_id': account_id_search.id,
                            'partner_id': partner_id_search and partner_id_search.id or False,
                            'analytic_account_id': search_analytic.id,
                            'amount_currency': row[6] or "",
                            'date': dt,
                            'move_id': account_journal_browse_obj.id,
                            'company_currency_id': currency__find.id,
                            'debit': float(row[4] or 0),
                            'credit': float(row[5] or 0),
                            }
            my_list.append((0,0,account_line))
        account_journal_browse_obj.write({'line_ids':my_list})
        
class AccountMove(models.Model):
    _inherit = "account.move"
    
    @api.multi
    def assert_balanced(self):
        if not self.ids:
            return True
        prec = self.env['decimal.precision'].precision_get('Account')

        self._cr.execute("""\
            SELECT      move_id
            FROM        account_move_line
            WHERE       move_id in %s
            GROUP BY    move_id
            HAVING      abs(sum(debit) - sum(credit)) > %s
            """, (tuple(self.ids), 10 ** (-max(5, prec))))
        if len(self._cr.fetchall()) != 0:
            if len(self._cr.fetchall()) != 0 == True:
                raise UserError(_("Cannot create unbalanced journal entry."))
        return True
    
class AccountJournal(models.Model):
    _inherit = "account.journal"

    _sql_constraints = [
        ('code_company_uniq', 'unique (code, name, company_id)', 'The code and name of the journal must be unique per company !'),
    ]































