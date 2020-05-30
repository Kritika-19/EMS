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


from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, AccessError
from odoo.addons import decimal_precision as dp
from datetime import datetime, timedelta, date
from odoo import api, fields, models, _
from odoo.tools.misc import formatLang
from werkzeug.urls import url_encode
from odoo.osv import expression
from itertools import groupby
import uuid
import time

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    
#    @api.one
#    @api.depends(
#        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
#        'move_id.line_ids.amount_residual',
#        'move_id.line_ids.currency_id')
#    def _compute_residual(self):
#        residual = 0.0
#        residual_company_signed = 0.0
#        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
#        for line in self.sudo().move_id.line_ids:
#            if line.account_id == self.account_id:
#                residual_company_signed += line.amount_residual
#                if line.currency_id == self.currency_id:
#                    residual += line.amount_residual_currency if line.currency_id else line.amount_residual
#                else:
#                    from_currency = (line.currency_id and line.currency_id.with_context(date=line.date)) or line.company_id.currency_id.with_context(date=line.date)
#                    residual += from_currency.compute(line.amount_residual, self.currency_id)
#        self.residual_company_signed = abs(residual_company_signed) * sign
#        self.residual_signed = abs(residual) * sign
#        self.residual = abs(residual)
#        digits_rounding_precision = self.currency_id.rounding
#        if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
#            self.reconciled = True
#        else:
#            self.reconciled = False
#        self.paid_amount = self.amount_total - self.residual


    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):
        round_curr = self.currency_id.round
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line_ids)
        self.amount_tax = sum(round_curr(line.amount_total) for line in self.tax_line_ids)
        self.amount_total = self.amount_untaxed + self.amount_tax
        amount_total_company_signed = self.amount_total
        amount_untaxed_signed = self.amount_untaxed
        if self.currency_id and self.company_id and self.currency_id != self.company_id.currency_id:
            currency_id = self.currency_id.with_context(date=self.date_invoice)
            amount_total_company_signed = currency_id.compute(self.amount_total, self.company_id.currency_id)
            amount_untaxed_signed = currency_id.compute(self.amount_untaxed, self.company_id.currency_id)
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        self.amount_total_company_signed = amount_total_company_signed * sign
        self.amount_total_signed = self.amount_total * sign
        self.amount_untaxed_signed = amount_untaxed_signed * sign
        self.paid_amount = self.amount_total - self.residual

    
    paid_amount = fields.Monetary(string="Payments", compute='_compute_amount',store=True)
    new_date_invoice = fields.Date(string='New Invoice Date', related='date_invoice')
    new_date_due = fields.Date(string='New Due Date', related='date_due')
    new_company_id = fields.Many2one('res.company', string='New Company',related='company_id')
    
    
class account_move_line(models.Model):
    _inherit = 'account.move.line'

    stat_report = fields.Boolean(string='Statement Report')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
