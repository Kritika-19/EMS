# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2017-Today Sitaram
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero

MAP_INVOICE_TYPE_PAYMENT_SIGN = {
    'out_invoice': 1,
    'in_refund': -1,
    'in_invoice': -1,
    'out_refund': 1,
}


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    customer_pdc_payment_account = fields.Many2one('account.account', 'PDC Payment Account for Customer')
    vendor_pdc_payment_account = fields.Many2one('account.account', 'PDC Payment Account for Vendors/Suppliers')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()

        res['customer_pdc_payment_account'] = int(
            self.env['ir.config_parameter'].sudo().get_param('customer_pdc_payment_account', default=0))
        res['vendor_pdc_payment_account'] = int(
            self.env['ir.config_parameter'].sudo().get_param('vendor_pdc_payment_account', default=0))

        return res

    @api.model
    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param('customer_pdc_payment_account',
                                                         self.customer_pdc_payment_account.id)
        self.env['ir.config_parameter'].sudo().set_param('vendor_pdc_payment_account',
                                                         self.vendor_pdc_payment_account.id)

        super(ResConfigSettings, self).set_values()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pdc_id = fields.Many2one('sr.pdc.payment', 'Post Dated Cheques')


class AccountMove(models.Model):
    _inherit = "account.move"

    pdc_id = fields.Many2one('sr.pdc.payment', 'Post Dated Cheques')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends(
        'state', 'currency_id', 'invoice_line_ids.price_subtotal',
        'move_id.line_ids.amount_residual',
        'move_id.line_ids.currency_id')
    def _compute_residual(self):
        residual = 0.0
        residual_company_signed = 0.0
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        for line in self._get_aml_for_amount_residual():
            residual_company_signed += line.amount_residual
            if line.currency_id == self.currency_id:
                residual += line.amount_residual_currency if line.currency_id else line.amount_residual
            else:
                from_currency = (line.currency_id and line.currency_id.with_context(
                    date=line.date)) or line.company_id.currency_id.with_context(date=line.date)
                residual += from_currency.compute(line.amount_residual, self.currency_id)
        if self._context.get('pdc'):
            residual = 0
        self.residual_company_signed = abs(residual_company_signed) * sign
        self.residual_signed = abs(residual) * sign
        self.residual = abs(residual)
        digits_rounding_precision = self.currency_id.rounding
        if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
            self.reconciled = True
        else:
            self.reconciled = False

    # When you click on add in invoice then this method called
    @api.multi
    def assign_outstanding_credit(self, credit_aml_id):
        self.ensure_one()
        credit_aml = self.env['account.move.line'].browse(credit_aml_id)
        if not credit_aml.currency_id and self.currency_id != self.company_id.currency_id:
            amount_currency = self.company_id.currency_id._convert(credit_aml.balance, self.currency_id,
                                                                   self.company_id,
                                                                   credit_aml.date or fields.Date.today())
            credit_aml.with_context(allow_amount_currency=True, check_move_validity=False).write({
                'amount_currency': amount_currency,
                'currency_id': self.currency_id.id})
        if credit_aml.payment_id:
            credit_aml.payment_id.write({'invoice_ids': [(4, self.id, None)]})
        if credit_aml.pdc_id:
            credit_aml.pdc_id.write({'invoice_ids': [(4, self.id, None)]})
        return self.register_payment(credit_aml)


class PdcPayment(models.Model):
    _name = "sr.pdc.payment"

    invoice_ids = fields.Many2many('account.invoice', 'account_invoice_pdc_rel', 'pdc_id', 'invoice_id',
                                   string="Invoices", copy=False, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, copy=False)
    state = fields.Selection(
        [('draft', 'Draft'), ('register', 'Registered'), ('return', 'Returned'), ('deposit', 'Deposited'),
         ('bounce', 'Bounced'), ('done', 'Done'), ('cancel', 'Cancelled')], readonly=True, default='draft', copy=False,
        string="Status")
    journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True,
                                 domain=[('type', 'in', ['bank'])])
    company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True)
    amount = fields.Monetary(string='Payment Amount', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True, copy=False)
    due_date = fields.Date(string='Due Date', default=fields.Date.context_today, required=True, copy=False)
    communication = fields.Char(string='Memo')
    cheque_ref = fields.Char('Cheque Reference')
    agent = fields.Char('Agent')
    bank = fields.Many2one('res.bank', string="Bank")
    name = fields.Char('Name')
    payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type',
                                    required=True)
    # Muhammad Jawaid Iqbal 6/1/2020
    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachment')
    journal_items_count = fields.Integer(compute='_compute_journal_items_count', string='Journal Items')
    journal_entry_count = fields.Integer(compute='_compute_journal_entry_count', string='Journal Entries')
    attchment_ids = fields.One2many('ir.attachment', 'payment_id', string='Create Attachment')
    maturity_date = fields.Date()
    vendor_pdc_payment_account_id = fields.Many2one('account.account','Vendor PDC Payment Account')
    customer_pdc_payment_account_id = fields.Many2one('account.account','Customer PDC Payment Account')
    
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            aml_recs = self.env['account.move.line'].search(
                [('partner_id.commercial_partner_id', '=', self.partner_id.commercial_partner_id.id),
                 ('account_id.internal_type', '=', 'receivable' if self.partner_id.customer == True else 'payable')])
            selected_debt = 0.0
            for line in aml_recs:
                selected_debt += line.amount_residual
            sign = -1.0 if self.partner_id.supplier else 1.0
            self.amount = selected_debt * sign

    def _compute_attachment_count(self):
        self.env.cr.execute(
            """select count(id) from ir_attachment where payment_id = {}""".format(self.id))
        rs = self.env.cr.dictfetchone()
        self.attachment_count = rs['count']

    def _compute_journal_items_count(self):
        self.env.cr.execute(
            """select count(id) from account_move_line where partner_id = {} and pdc_id = {}""".format(
                self.partner_id.id, self.id))
        rs = self.env.cr.dictfetchone()
        self.journal_items_count = rs['count']

    def _compute_journal_entry_count(self):
        self.env.cr.execute(
            """select count(id) from account_move where pdc_id = {}""".format(self.id))
        rs = self.env.cr.dictfetchone()
        self.journal_entry_count = rs['count']

    def attachment_on_account_cheque(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachment.Details',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('payment_id', '=', self.id)]
        }

    def action_view_jornal_items(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Items',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.partner_id.id), ('pdc_id', '=', self.id)]
        }

    def action_view_jornal_entry(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entries',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('pdc_id', '=', self.id)]
        }

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        self.ensure_one()
        # Set partner_id domain
        if self.payment_type == 'inbound':
            return {'domain': {'partner_id': [('customer', '=', True)]}}
        else:
            return {'domain': {'partner_id': [('supplier', '=', True)]}}

    @api.onchange('journal_id')
    def _default_currency(self):
        if self.journal_id:
            journal = self.journal_id
            currency_id = journal.currency_id or journal.company_id.currency_id or self.env.user.company_id.currency_id
            self.currency_id = currency_id.id
        else:
            self.currency_id = False

    @api.model
    def default_get(self, fields):
        rec = super(PdcPayment, self).default_get(fields)
        context = dict(self._context or {})

        # Checks on received invoice records
        invoices = self.env['account.invoice'].browse(context.get('active_ids'))
        if any(invoice.state != 'open' for invoice in invoices):
            raise UserError(_("You can only register check for open invoices"))

        total_amount = sum(inv.residual * MAP_INVOICE_TYPE_PAYMENT_SIGN[inv.type] for inv in invoices)
        communication = ' '.join([ref for ref in invoices.mapped('reference') if ref])
        supplier_account_id=False
        customer_account_id = False
        if invoices:
            if invoices.type == 'in_invoice':
                payment_type = 'outbound'
                supplier_account_id = self.env['ir.config_parameter'].sudo().get_param('vendor_pdc_payment_account')
            else:
                payment_type = 'inbound'
                customer_account_id = self.env['ir.config_parameter'].sudo().get_param('customer_pdc_payment_account')
        else:
            payment_type = 'inbound'
            customer_account_id = self.env['ir.config_parameter'].sudo().get_param('customer_pdc_payment_account')
            
        rec.update({
            'payment_type': payment_type,
            'name': invoices.number,
            'amount': abs(total_amount),
            'currency_id': invoices[0].currency_id.id if invoices else False,
            'partner_id': invoices[0].commercial_partner_id.id if invoices else False,
            'communication': communication,
        })
        if supplier_account_id:
            rec.update({'vendor_pdc_payment_account_id':int(supplier_account_id)})
        if customer_account_id:
            rec.update({'customer_pdc_payment_account_id':int(customer_account_id)})    
            
        return rec

    def get_credit_entry(self, partner_id, invoice_ids, move, credit, debit, amount_currency, journal_id, name,
                         account_id, currency_id, payment_date):
        return {
            'partner_id': partner_id.id,
            'invoice_id': invoice_ids.id if len(invoice_ids) == 1 else False,
            'move_id': move.id,
            'debit': debit,
            'credit': credit,
            'amount_currency': amount_currency or False,
            'payment_id': False,
            'journal_id': journal_id.id,
            'name': name,
            'account_id': account_id,
            'currency_id': currency_id or False,
            'date_maturity': payment_date,
            'pdc_id': self.id
        }

    def get_debit_entry(self, partner_id, invoice_ids, move, credit, debit, amount_currency, journal_id, name,
                        account_id, currency_id):
        return {
            'partner_id': partner_id.id,
            'invoice_id': invoice_ids.id if len(invoice_ids) == 1 else False,
            'move_id': move.id,
            'debit': debit,
            'credit': credit,
            'amount_currency': amount_currency or False,
            'payment_id': False,
            'journal_id': journal_id.id,
            'name': name,
            'account_id': account_id,
            'currency_id': currency_id or False,
            'pdc_id': self.id
        }

    @api.multi
    def cancel(self):
        self.state = 'cancel'

    @api.multi
    def register(self):
        inv = self.env['account.invoice'].browse(self._context.get('active_ids'))
        if inv:
            inv.state = 'paid'
        self.state = 'register'
        if self.payment_type == 'inbound':
            self.name = self.env['ir.sequence'].next_by_code('pdc.payment')
        else:
            self.name = self.env['ir.sequence'].next_by_code('pdc.payment.vendor')
        return

    @api.multi
    def return_cheque(self):
        self.state = 'return'
        return

    @api.multi
    def deposit(self):
        vendor_pdc_payment_account_id = self.vendor_pdc_payment_account_id and self.vendor_pdc_payment_account_id.id or self.env['ir.config_parameter'].sudo().get_param('vendor_pdc_payment_account')
        customer_pdc_payment_account_id = self.customer_pdc_payment_account_id and self.customer_pdc_payment_account_id.id or self.env['ir.config_parameter'].sudo().get_param('customer_pdc_payment_account') 
        if customer_pdc_payment_account_id and vendor_pdc_payment_account_id:
            inv = self.env['account.invoice'].browse(self._context.get('active_ids'))
            aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
            if inv:
                inv.state = 'paid'
                custom_currency_id = inv.currency_id
                company_currency_id = inv.company_id.currency_id
                account_id = inv.account_id.id
            else:
                custom_currency_id = self.currency_id
                company_currency_id = self.env.user.company_id.currency_id
                if self.payment_type == 'inbound':
                    account_id = self.partner_id.property_account_receivable_id.id
                else:
                    account_id = self.partner_id.property_account_payable_id.id
            debit, credit, amount_currency, currency_id = aml_obj.with_context(
                date=self.payment_date).compute_amount_fields(self.amount, custom_currency_id, company_currency_id,
                                                              custom_currency_id)
            move = self.env['account.move'].create(self._get_move_vals())
            #################    Credit Entry  ######################
            name = ''
            if inv:
                name += 'PDC Payment: '
                for record in inv:
                    if record.move_id:
                        name += record.number + ', '
                name = name[:len(name) - 2]
            print ("=========context", self._context)
            print ("=========account_id", account_id)
            if self.payment_type == 'inbound':
                credit_entry = self.get_credit_entry(self.partner_id, inv, move, debit, credit, amount_currency,
                                                     self.journal_id, name, account_id, currency_id, self.payment_date)
            else:
                credit_entry = self.get_credit_entry(self.partner_id, inv, move, debit, credit, amount_currency,
                                                     self.journal_id, name, int(vendor_pdc_payment_account_id), currency_id,
                                                     self.payment_date)
            aml_obj.create(credit_entry)
            ################ Debit Entry #############################
            print ("=========inv", inv)
            if self.payment_type == 'inbound':
                debit_entry = self.get_debit_entry(self.partner_id, inv, move, credit, debit, amount_currency,
                                                   self.journal_id, name, int(customer_pdc_payment_account_id), currency_id)
            else:
                debit_entry = self.get_debit_entry(self.partner_id, inv, move, credit, debit, amount_currency,
                                                   self.journal_id, name, account_id, currency_id)
            aml_obj.create(debit_entry)
            move.post()
        else:
            raise UserError(_("Configuration Error: Please define account for the PDC payment."))
        self.state = 'deposit'
        return True

    @api.multi
    def bounce(self):
        vendor_pdc_payment_account_id = self.vendor_pdc_payment_account_id and self.vendor_pdc_payment_account_id.id or self.env['ir.config_parameter'].sudo().get_param('vendor_pdc_payment_account')
        customer_pdc_payment_account_id = self.customer_pdc_payment_account_id and self.customer_pdc_payment_account_id.id or self.env['ir.config_parameter'].sudo().get_param('customer_pdc_payment_account') 
        if customer_pdc_payment_account_id and vendor_pdc_payment_account_id:
            if self.payment_type == 'inbound':
                account_id = self.partner_id.property_account_receivable_id.id
            else:
                account_id = self.partner_id.property_account_payable_id.id
            aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
            debit, credit, amount_currency, currency_id = aml_obj.with_context(
                date=self.payment_date).compute_amount_fields(self.amount, self.currency_id,
                                                              self.env.user.company_id.currency_id, self.currency_id)
            move = self.env['account.move'].create(self._get_move_vals())
            #################    Credit Entry  ######################
            name = ''
            if self.invoice_ids:
                name += 'PDC Payment: '
                for record in self.invoice_ids:
                    if record.move_id:
                        name += record.number + ', '
                name = name[:len(name) - 2]
            if self.payment_type == 'inbound':
                credit_entry = self.get_credit_entry(self.partner_id, self.invoice_ids, move, debit, credit,
                                                     amount_currency,
                                                     self.journal_id, name, int(customer_pdc_payment_account_id), currency_id,
                                                     self.payment_date)
            else:
                credit_entry = self.get_credit_entry(self.partner_id, self.invoice_ids, move, debit, credit,
                                                     amount_currency,
                                                     self.journal_id, name, account_id, currency_id,
                                                     self.payment_date)
            aml_obj.create(credit_entry)
            ################ Debit Entry #############################
            if self.payment_type == 'inbound':
                debit_entry = self.get_debit_entry(self.partner_id, self.invoice_ids, move, credit, debit,
                                                   amount_currency,
                                                   self.journal_id, name, account_id, currency_id)
            else:
                debit_entry = self.get_debit_entry(self.partner_id, self.invoice_ids, move, credit, debit,
                                                   amount_currency,
                                                   self.journal_id, name, int(vendor_pdc_payment_account_id), currency_id)

            aml_obj.create(debit_entry)
            move.post()
            self.state = 'bounce'
            for record in self.invoice_ids:
                record.state = 'open'
        else:
            raise UserError(_("Configuration Error: Please define account for the PDC payment."))
        return True

    @api.multi
    def done(self):
        vendor_pdc_payment_account_id = self.vendor_pdc_payment_account_id and self.vendor_pdc_payment_account_id.id or self.env['ir.config_parameter'].sudo().get_param('vendor_pdc_payment_account')
        customer_pdc_payment_account_id = self.customer_pdc_payment_account_id and self.customer_pdc_payment_account_id.id or self.env['ir.config_parameter'].sudo().get_param('customer_pdc_payment_account') 
        if customer_pdc_payment_account_id and vendor_pdc_payment_account_id:
            aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
            debit, credit, amount_currency, currency_id = aml_obj.with_context(
                date=self.payment_date).compute_amount_fields(self.amount, self.currency_id,
                                                              self.env.user.company_id.currency_id, self.currency_id)
            move = self.env['account.move'].create(self._get_move_vals())
            if self.payment_type == 'inbound':
                account_id = self.journal_id.default_debit_account_id.id
            else:
                account_id = self.journal_id.default_credit_account_id.id
            #################    Credit Entry  ######################
            name = ''
            if self.invoice_ids:
                name += 'PDC Payment: '
                for record in self.invoice_ids:
                    if record.move_id:
                        name += record.number + ', '
                name = name[:len(name) - 2]
            if self.payment_type == 'inbound':
                credit_entry = self.get_credit_entry(self.partner_id, self.invoice_ids, move, debit, credit,
                                                     amount_currency,
                                                     self.journal_id, name, int(customer_pdc_payment_account_id), currency_id,
                                                     self.payment_date)
            else:
                credit_entry = self.get_credit_entry(self.partner_id, self.invoice_ids, move, debit, credit,
                                                     amount_currency,
                                                     self.journal_id, name, account_id, currency_id,
                                                     self.payment_date)
            aml_obj.create(credit_entry)
            ################ Debit Entry #############################
            if self.payment_type == 'inbound':
                debit_entry = self.get_debit_entry(self.partner_id, self.invoice_ids, move, credit, debit,
                                                   amount_currency,
                                                   self.journal_id, name, account_id, currency_id)
            else:
                debit_entry = self.get_debit_entry(self.partner_id, self.invoice_ids, move, credit, debit,
                                                   amount_currency,
                                                   self.journal_id, name, int(vendor_pdc_payment_account_id), currency_id)
            aml_obj.create(debit_entry)
            move.post()
            self.state = 'done'
        else:
            raise UserError(_("Configuration Error: Please define account for the PDC payment."))
        return True

    def _get_move_vals(self, journal=None):
        """ Return dict to create the payment move
        """
        journal = journal or self.journal_id
        return {
            'date': self.payment_date,
            'ref': self.communication or '',
            'company_id': self.company_id.id,
            'journal_id': journal.id,
            'pdc_id': self.id
        }


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    payment_id = fields.Many2one('sr.pdc.payment')
