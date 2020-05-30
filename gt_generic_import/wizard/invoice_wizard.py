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

class InvoiceWizard(models.TransientModel):
    _name = 'invoice.wizard'
    _description = 'Invoice Wizard'

    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validate')],'State')
    type = fields.Selection([('out_invoice', 'Customer'), ('in_invoice', 'Vendor')], string='Type')

    @api.multi
    def import_customer_invoice(self):
        inv_result = {}
        payment_term = False
        fiscal_position = False
        team = False
        user = False
        invoice_obj = self.env['account.invoice']
        invoice_line_obj = self.env['account.invoice.line']
        file_data = False
        
        if self.select_file and self.data_file and self.type:
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
            raise exceptions.Warning(_('Please select file and type of file or sequence properly'))
        
        for row in file_data:
            ids =[]
            inv_line_obj = self.env['account.invoice.line']
            inv_obj = self.env['account.invoice']
            l_vals = {}
            if self.select_file == 'csv' and len(row) != 17:
                raise ValidationError("You can let empty cell in csv file or please use xls file.")
            
            taxes_ids = self.env['account.tax'].search([('name', '=', row[9] or "_____________"),('type_tax_use', '=', 'sale')])
            dt = datetime.strptime(row[10], "%d-%m-%Y")
            
            if row[1] != "":
                partner = self.env['res.partner'].search([('name', '=', row[1] or "_____________")])
                if not partner:
                    raise ValidationError("Customer '%s' not found"%row[1])
            else:
                raise ValidationError("Please Assign Partner.")
            
            currency = self.env['res.currency'].search([('name', '=', row[2] or "_____________")])
            if not currency:
                raise ValidationError("currency  '%s' not found"%row[2])
            
            uom = self.env['product.uom'].search([('name', '=', row[5] or "_____________")])
            if not uom:
                raise ValidationError("UOM  '%s' not found"%row[5])
            
            if row[11] != "":
                account = self.env['account.account'].search([('name', '=', row[11] or "_____________")])
                if not account:
                    raise ValidationError("Account '%s' not found"%row[11])
            else:
                raise ValidationError("Please Assign Account.")
            
            if row[12] != "":
                payment_term = self.env['account.payment.term'].search([('name', '=', row[12] or "_____________")])
                if not payment_term:
                    raise ValidationError("Payment Terms '%s' is not founded" % row[12])
            
            if row[13] != "":
                fiscal_position = self.env['account.fiscal.position'].search([('name', '=', row[13] or "_____________")])
                if not fiscal_position:
                    raise ValidationError("Fiscal Position '%s' is not founded" % row[13])
                
            if row[14] != "":
                team = self.env['crm.team'].search([('name', '=', row[14] or "_____________")])
                if not team:
                    raise ValidationError("Team '%s' is not founded" % row[14])
                
            if row[15] != "":
                user = self.env['res.users'].search([('name', '=', row[15] or "_____________")])
                if not user:
                    raise ValidationError("User '%s' is not founded" % row[15])
            
            if row[16] != "":
                sale_order = self.env['sale.order'].search([('name', '=', row[16] or "_____________")])
                if not sale_order:
                    raise ValidationError("Sales User  '%s' not found"%row[16])
                
                if self.state == "validate":
                    sale_order.action_confirm_custom(state="validate")
            elif row[16] == "":
                if self.type == "out_invoice":
                    invoice = inv_obj.create({
                        'type': 'out_invoice',
                        'reference': False,
                        'account_id': account and account.id,
                        'partner_id': partner and partner.id,
                        'currency_id': currency and currency.id or False,
                        'payment_term_id': payment_term and payment_term.id or False,
                        'fiscal_position_id': fiscal_position and fiscal_position.id or False,
                        'team_id': team and team.id or False,
                        'user_id': user and user.id or False,
                        'comment': row[0],
                    })
                elif self.type == "in_invoice":
                    invoice = inv_obj.create({
                        'type': 'in_invoice',
                        'reference': False,
                        'account_id': account and account.id,
                        'partner_id': partner and partner.id,
                        'currency_id': currency and currency.id or False,
                        'payment_term_id': payment_term and payment_term.id or False,
                        'fiscal_position_id': fiscal_position and fiscal_position.id or False,
                        'team_id': team and team.id or False,
                        'user_id': user and user.id or False,
                        'comment': row[0],
                    })
                
                if row[3] != "":
                    for pro in row[3].split(";"):
                        product = self.env['product.product'].search([('id', '=', pro or "_____________")])
                        if not product:
                            raise ValidationError("Product '%s' is not founded" % pro)
                        
                        account_id = False
                        if product.id:
                            account_id = product.property_account_income_id.id or product.categ_id.property_account_income_categ_id.id
                        if not account_id:
                            inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                            account_id = fiscal_position.map_account(inc_acc).id if inc_acc else False
                        if not account_id:
                            raise UserError(
                                _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                        (line.product.name,))
                        l_vals = {
                        'name':  _('Down Payment'),
                        'product_id': product.id,
                        'account_id': account_id,
                        'price_unit': product.list_price,
                        }
                        inv_line_rec = inv_line_obj.create(l_vals)
                        ids.append(inv_line_rec.id)
                invoice.invoice_line_ids = ids
                
                if row[4] != "" and type(row[4]) in [str]:
                    i = 0
                    for id in ids:
                        list = row[4].split(";")
                        order_line = self.env["account.invoice.line"].browse(id)
                        order_line.quantity = list[i]
                        i = i+1
                else:
                    for id in ids:
                        order_line = self.env["account.invoice.line"].browse(id)
                        order_line.quantity = row[4]
                if row[7] != "" and type(row[7]) in [str]:
                    j = 0
                    for id in ids:
                        list = row[7].split(";")
                        order_line = self.env["account.invoice.line"].browse(id)
                        order_line.price_unit = list[j]
                        j = j+1
                else:
                    for id in ids:
                        order_line = self.env["account.invoice.line"].browse(id)
                        order_line.price_unit = row[7]
            
                if self.state == "validate":
                    invoice.action_invoice_open()
        return True
    
class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    
    @api.multi
    def action_confirm_custom(self, state):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))
        self._action_confirm()
        if self.env['ir.config_parameter'].sudo().get_param('sale.auto_done_setting'):
            self.action_done()
            
        ids =[]
        inv_line_obj = self.env['account.invoice.line']
        inv_obj = self.env['account.invoice']
        l_vals = {}
        for order in self:
            for line in order.order_line:
                account_id = False
                if line.product_id.id:
                    account_id = line.product_id.property_account_income_id.id or line.product_id.categ_id.property_account_income_categ_id.id
                if not account_id:
                    inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
                    account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
                if not account_id:
                    raise UserError(
                        _('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
                        (line.product_id.name,))
                
                taxes = line.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                if order.fiscal_position_id and taxes:
                    tax_ids = order.fiscal_position_id.map_tax(taxes, line.product_id, order.partner_shipping_id).ids
                else:
                    tax_ids = taxes.ids
                l_vals = {
                'name':  _('Down Payment'),
                'origin': order.name,
                'account_id': account_id,
                'price_unit': line.price_unit,
                'uom_id': line.product_id.uom_id.id,
                'product_id': line.product_id.id,
                'sale_line_ids': [(6, 0, [line.id])],
                'invoice_line_tax_ids': [(6, 0, tax_ids)],
                'analytic_tag_ids': [(6, 0, line.analytic_tag_ids.ids)],
                'account_analytic_id': order.analytic_account_id.id or False,
                }
                inv_line_rec = inv_line_obj.create(l_vals)
                ids.append(inv_line_rec.id)
            invoice = inv_obj.create({
                'name': order.client_order_ref or order.name,
                'origin': order.name,
                'type': 'out_invoice',
                'reference': False,
                'account_id': order.partner_id.property_account_receivable_id.id,
                'partner_id': order.partner_invoice_id.id,
                'partner_shipping_id': order.partner_shipping_id.id,
                'currency_id': order.pricelist_id.currency_id.id,
                'payment_term_id': order.payment_term_id.id,
                'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
                'team_id': order.team_id.id,
                'user_id': order.user_id.id,
                'comment': order.note,
            })
            invoice.invoice_line_ids = ids
            if state == "validate":
                invoice.action_invoice_open()
        return True









































