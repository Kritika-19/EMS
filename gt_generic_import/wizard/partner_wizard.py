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

class PartnerWizard(models.TransientModel):
    _name = 'partner.wizard'
    _description = 'Partner Wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")

    @api.multi
    def import_partner(self):
        partner_obj = self.env['res.partner']
        if self.select_file and self.data_file:
            if self.select_file == 'csv':
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",", delimiter=",")
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
            if self.select_file == 'csv' and len(row) != 19:
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            if row[0] == "" :
                raise ValidationError("Please Assign The Customer Name And Type.")
            search_partner = self.env['res.partner'].search([('name', '=', row[0] or "_____________"),('ref', '=', row[16] or "_____________")])
            search_parent_partner = self.env['res.partner'].search([('name', '=', row[2] or "_____________")])
            search_salesperson = self.env['res.users'].search([('name', '=', row[15] or "_____________")])
            search_cust_payment_term = self.env['account.payment.term'].search([('name', '=', row[17] or "_____________")])
            search_vendar_payment_term = self.env['account.payment.term'].search([('name', '=', row[18] or "_____________")])
            search_country = self.env['res.country'].search([('name', '=', row[8] or "_____________")])
            search_state = self.env['res.country.state'].search([('name', '=', row[6] or "_____________")])
            if not search_salesperson:
                raise ValidationError("Salesperson ids  '%s' not found" % row[15])
            if not search_cust_payment_term:
                raise ValidationError("customer payment  '%s' not found" % row[17])
            if not search_vendar_payment_term:
                raise ValidationError("Vendor payment  '%s' not found" % row[18])
            if not search_country:
                raise ValidationError("Country  '%s' not found" % row[18])
            if not search_state:
                raise ValidationError("State  '%s' not found" % row[6])
            partner_fields = partner_obj.fields_get()
            partner_def_val = partner_obj.default_get(partner_fields)
            new_partner_val = partner_def_val.copy()
            new_partner_val.update({
                                    'name': row[0],
                                    'company_type': row[1] or "",
                                    'parent_id': search_parent_partner and search_parent_partner.id or False,
                                    'street': row[3] or "",
                                    'street2': row[4] or "",
                                    'city': row[5] or "",
                                    'state': search_state and search_state.id or row[6] or False,
                                    'zip': row[7] or "",
                                    'country_id': search_country and search_country.id or row[8] or False,
                                    'website': row[9] or "",
                                    'phone': row[10] or "",
                                    'mobile': row[11] or "",
                                    'email': row[12] or "",
                                    'customer': row[13] or "",
                                    'supplier': row[14] or "",
                                    'user_id': search_salesperson and search_salesperson.id or row[15] or False,
                                    'ref': row[16] or "",
                                    'property_payment_term_id': search_cust_payment_term and search_cust_payment_term.id or False,
                                    'property_supplier_payment_term_id': search_vendar_payment_term and search_vendar_payment_term.id or False,
                                    })
            if search_partner:
                partner_created_id = search_partner.write(new_partner_val)
            else:
                partner_created_id = partner_obj.create(new_partner_val)










































