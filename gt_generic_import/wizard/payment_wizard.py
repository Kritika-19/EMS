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

class PaymentWizard(models.TransientModel):
    _name = 'payment.wizard'
    _description = 'Payment Wizard'

    payment_type = fields.Selection([('customer_py', 'Customer Payment'), ('supp_py', 'Supplier Payment')],string='Payment')
    data_file = fields.Binary(string="File")

    @api.multi
    def import_payment(self,vals):
        if self.data_file == 'csv':
            csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",delimiter=",")
            csv_reader_data = iter(csv_reader_data)
            next(csv_reader_data)
            file_data = csv_reader_data
        else:
            file_datas = base64.decodestring(self.data_file)
            workbook = xlrd.open_workbook(file_contents=file_datas)
            sheet = workbook.sheet_by_index(0)
            result = []
            data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
            data.pop(0)
            file_data = data

        for row in file_data:
            if row[0] != "":
                partner = self.env['res.partner'].search([('name', '=', row[0] or "_____________")])
                if not partner:
                    raise ValidationError("Customer/Vendor '%s' is not founded" % row[0])
            else:
                raise ValidationError("Please Assign Customer/Vendor Name.")
            
            if row[2] != "":
                account = self.env['account.journal'].search([('name', '=', row[2] or "_____________")])
                if not account:
                    raise ValidationError("PAYMENT JOURNAL '%s' is not founded" % row[2])
            else:
                raise ValidationError("Please Assign PAYMENT JOURNAL.")

            payment_vals = {
                            'partner_type': self.payment_type == 'customer_py' and 'customer' or 'supplier',
                            'partner_id': partner.id,
                            'payment_date': datetime.now(),
                            'journal_id': account.id,
                            'amount': row[1],
                            'communication': row[4],
                            'payment_method_id': 2,
                            'state': 'draft',
                            'payment_type': self.payment_type == 'customer_py' and 'inbound' or 'outbound',
                            }

            payment = self.env['account.payment'].create(payment_vals)
            payment.post()











            