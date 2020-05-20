import time
from collections import OrderedDict
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools.misc import formatLang
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
from odoo.addons import decimal_precision as dp
import math
from lxml import etree
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    partner_id = fields.Many2one('res.partner', string='Parent', change_default=True,
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 track_visibility='always')
    user_id = fields.Many2one('res.users', string='User', track_visibility='onchange',
                              readonly=True, states={'draft': [('readonly', False)]},
                              default=lambda self: self.env.user, copy=False)
    student_line_ids = fields.One2many('student.invoice.line', 'account_id', compute='depends_invoice_line_ids',
                                       string='Student Separate Fee')

    # account.payment.group JI

    pay_now_journal_id = fields.Many2one(
        'account.journal',
        'Pay now Journal',
        help='If you set a journal here, after invoice validation, the invoice'
             ' will be automatically paid with this journal. As manual payment'
             'method is used, only journals with manual method are shown.',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )

    @api.multi
    def _get_tax_factor(self):
        self.ensure_one()
        return (self.amount_total and (
                self.amount_untaxed / self.amount_total) or 1.0)

    open_move_line_ids = fields.One2many(
        'account.move.line',
        compute='_compute_open_move_lines'
    )

    @api.multi
    def _compute_open_move_lines(self):
        for rec in self:
            rec.open_move_line_ids = rec.move_id.line_ids.filtered(
                lambda r: not r.reconciled and r.account_id.internal_type in (
                    'payable', 'receivable'))

    payment_group_ids = fields.Many2many(
        'account.payment.group',
        compute='_compute_payment_groups',
        string='Payment Groups',
    )

    @api.multi
    @api.depends('payment_move_line_ids')
    def _compute_payment_groups(self):
        """
        El campo en invoices "payment_id" no lo seteamos con los payment groups
        Por eso tenemos que calcular este campo
        """
        for rec in self:
            rec.payment_group_ids = rec.payment_move_line_ids.mapped(
                'payment_id.payment_group_id')

    @api.multi
    def action_view_payment_groups(self):
        if self.type in ('in_invoice', 'in_refund'):
            action = self.env.ref(
                'account_payment_group.action_account_payments_group_payable')
        else:
            action = self.env.ref(
                'account_payment_group.action_account_payments_group')

        result = action.read()[0]

        if len(self.payment_group_ids) != 1:
            result['domain'] = [('id', 'in', self.payment_group_ids.ids)]
        elif len(self.payment_group_ids) == 1:
            res = self.env.ref(
                'account_payment_group.view_account_payment_group_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.payment_group_ids.id
        return result

    @api.multi
    def action_account_invoice_payment_group(self):
        self.ensure_one()
        if self.state != 'open':
            raise ValidationError(_(
                'You can only register payment if invoice is open'))
        return {
            'name': _('Register Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.payment.group',
            'view_id': False,
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': {
                # si bien el partner se puede adivinar desde los apuntes
                # con el default de payment group, preferimos mandar por aca
                # ya que puede ser un contacto y no el commercial partner (y
                # en los apuntes solo hay commercial partner)
                'default_partner_id': self.partner_id.id,
                'to_pay_move_line_ids': self.open_move_line_ids.ids,
                'pop_up': True,
                # We set this because if became from other view and in the
                # context has 'create=False' you can't crate payment lines
                #  (for ej: subscription)
                'create': True,
                'default_communication': self.number,
                'default_company_id': self.company_id.id,
            },
        }

    # account.payment.group JI

    @api.depends('invoice_line_ids')
    def depends_invoice_line_ids(self):
        student_list = []
        total_list = []
        list = []
        line_obj = self.env['student.invoice.line']
        for rec in self:
            line_obj_searched = line_obj.search([('account_id', '=', rec.id)])
            if not line_obj_searched:
                for line in rec.invoice_line_ids:
                    if line.student_id.id not in student_list:
                        student_list.append(line.student_id.id)
                for i in range(0, len(student_list)):
                    student = rec.env['student.student'].browse(student_list[i])
                    vals = {'name': student.id, 'account_id': rec.id}
                    created_obj = line_obj.create(vals)
                    list.append(created_obj.id)
                    i += i
                rec.student_line_ids = self.env['student.invoice.line'].browse(list)
                for stud_line in rec.student_line_ids:
                    amount = 0.0
                    for inv_line in rec.invoice_line_ids:
                        if inv_line.student_id.id == stud_line.name.id:
                            amount += inv_line.price_subtotal
                            stud_line.write({'total_amount': amount})
            elif line_obj_searched:
                rec.student_line_ids = line_obj_searched


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    fee_type = fields.Char(string='Fee Type')
    name = fields.Text(string='Student', required=True)
    price_unit = fields.Monetary(string='Fee Amount', required=True, digits=dp.get_precision('Product Price'))
    student_id = fields.Many2one('student.student', string='Student')


class StudentInvoiceLine(models.Model):
    _name = "student.invoice.line"

    account_id = fields.Many2one('account.invoice', string='Invoice')
    account_payment_id = fields.Many2one('account.payment', string='Payment')
    name = fields.Many2one('student.student', string='Student')
    total_amount = fields.Monetary(string='Total Amount')
    paid_amount = fields.Monetary(string='Paid Amount')
    paying_amount = fields.Monetary(string='Paying Amount', default=0.0)
    current_due_amount = fields.Monetary(string='Current Due Amount', compute='depends_paid_amount')

    currency_id = fields.Many2one("res.currency", related='company_id.currency_id', string="Currency", )
    company_id = fields.Many2one('res.company', string='Company', required=True, index=True,
                                 default=lambda self: self.env.user.company_id)

    @api.onchange('paying_amount')
    def _onchange_paying_amount(self):
        if self.paying_amount:
            if self.paying_amount > self.current_due_amount:
                raise ValidationError(_(
                    'Payment amount {:.0f} cannot exceed your current balance {:.0f} !'.format(self.paying_amount,
                                                                                               self.current_due_amount)))

    @api.one
    @api.depends('paid_amount')
    def depends_paid_amount(self):
        for rec in self:
            rec.current_due_amount = rec.total_amount - rec.paid_amount


class AccountPayment(models.Model):
    _inherit = "account.payment"

    student_line_ids = fields.One2many('student.invoice.line', 'account_payment_id', string='Student Separate Fee')
    temp_amount = fields.Monetary(string="Total Remaining Amount")
    # Muhammad Jawaid Iqbal
    student_id = fields.Many2one('student.student', string='Student')
    total_amount = fields.Monetary(string='Total Amount')
    paid_amount = fields.Monetary(string='Paid Amount')
    current_due_amount = fields.Monetary(string='Current Due Amount')

    @api.onchange('amount')
    def _onchange_paying_amount(self):
        if self.amount:
            if self.amount > self.current_due_amount:
                raise ValidationError(_(
                    'Payment amount {:.0f} cannot exceed your current balance {:.0f} !'.format(self.amount,
                                                                                               self.current_due_amount)))

    @api.onchange('student_id')
    def _onchange_name(self):
        if self.student_id:
            record = self.env['student.invoice.line'].search(
                [('name', '=', self.student_id.id), ('account_id', '=', self._context['invoice_id'])])
            self.total_amount = record.total_amount
            self.current_due_amount = record.current_due_amount
            self.paid_amount = record.paid_amount

    @api.onchange('name')
    def _onchange_account_payment_id(self):
        invoice = self.env['account.invoice'].browse(self._context['invoice_id'])
        return {'domain': {'student_id': [('id', 'in', invoice.student_line_ids.mapped('name').mapped('id'))]}}

    # account.payment.group JI

    payment_group_id = fields.Many2one(
        'account.payment.group',
        'Payment Group',
        ondelete='cascade',
        readonly=True,
    )

    @api.multi
    @api.depends('amount', 'other_currency', 'force_amount_company_currency')
    def _compute_amount_company_currency(self):
        """
        * Si las monedas son iguales devuelve 1
        * si no, si hay force_amount_company_currency, devuelve ese valor
        * sino, devuelve el amount convertido a la moneda de la cia
        """
        _logger.info('Computing amount company currency')
        for rec in self:
            if not rec.other_currency:
                amount_company_currency = rec.amount
            elif rec.force_amount_company_currency:
                amount_company_currency = rec.force_amount_company_currency
            else:
                amount_company_currency = rec.currency_id.with_context(
                    date=rec.payment_date).compute(
                    rec.amount, rec.company_id.currency_id)
            rec.amount_company_currency = amount_company_currency

    @api.multi
    # this onchange is necesary because odoo, sometimes, re-compute
    # and overwrites amount_company_currency. That happends due to an issue
    # with rounding of amount field (amount field is not change but due to
    # rouding odoo believes amount has changed)
    @api.onchange('amount_company_currency')
    def _inverse_amount_company_currency(self):
        _logger.info('Running inverse amount company currency')
        for rec in self:
            if rec.other_currency and rec.amount_company_currency != \
                    rec.currency_id.with_context(
                        date=rec.payment_date).compute(
                        rec.amount, rec.company_id.currency_id):
                force_amount_company_currency = rec.amount_company_currency
            else:
                force_amount_company_currency = False
            rec.force_amount_company_currency = force_amount_company_currency

    payment_group_company_id = fields.Many2one(
        related='payment_group_id.company_id', readonly=True, )

    exchange_rate = fields.Float(
        string='Exchange Rate',
        compute='_compute_exchange_rate',
        # readonly=False,
        # inverse='_inverse_exchange_rate',
        digits=(16, 4),
    )

    @api.multi
    @api.depends(
        'amount', 'other_currency', 'amount_company_currency')
    def _compute_exchange_rate(self):
        for rec in self.filtered('other_currency'):
            rec.exchange_rate = rec.amount and (
                    rec.amount_company_currency / rec.amount) or 0.0

    other_currency = fields.Boolean(
        compute='_compute_other_currency',
    )

    @api.multi
    @api.depends('currency_id', 'company_currency_id')
    def _compute_other_currency(self):
        for rec in self:
            if rec.company_currency_id and rec.currency_id and \
                    rec.company_currency_id != rec.currency_id:
                rec.other_currency = True

    force_amount_company_currency = fields.Monetary(
        string='Payment Amount on Company Currency',
        currency_field='company_currency_id',
        copy=False,
    )

    @api.multi
    @api.depends('payment_type')
    def _compute_payment_type_copy(self):
        for rec in self:
            if rec.payment_type == 'transfer':
                continue
            rec.payment_type_copy = rec.payment_type

    payment_type_copy = fields.Selection(
        selection=[('outbound', 'Send Money'), ('inbound', 'Receive Money')],
        compute='_compute_payment_type_copy',
        inverse='_inverse_payment_type_copy',
        string='Payment Type'
    )

    signed_amount = fields.Monetary(
        string='Payment Amount',
        compute='_compute_signed_amount',
    )

    @api.multi
    @api.onchange('payment_type_copy')
    def _inverse_payment_type_copy(self):
        for rec in self:
            # if false, then it is a transfer
            rec.payment_type = (
                    rec.payment_type_copy and rec.payment_type_copy or 'transfer')

    amount_company_currency = fields.Monetary(
        string='Payment Amount on Company Currency',
        compute='_compute_amount_company_currency',
        inverse='_inverse_amount_company_currency',
        currency_field='company_currency_id',
    )

    signed_amount_company_currency = fields.Monetary(
        string='Payment Amount on Company Currency',
        compute='_compute_signed_amount',
        currency_field='company_currency_id',
    )

    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        readonly=True,
    )

    @api.multi
    @api.depends(
        'amount', 'payment_type', 'partner_type', 'amount_company_currency')
    def _compute_signed_amount(self):
        for rec in self:
            sign = 1.0
            if (
                    (rec.partner_type == 'supplier' and
                     rec.payment_type == 'inbound') or
                    (rec.partner_type == 'customer' and
                     rec.payment_type == 'outbound')):
                sign = -1.0
            rec.signed_amount = rec.amount and rec.amount * sign
            rec.signed_amount_company_currency = (
                    rec.amount_company_currency and
                    rec.amount_company_currency * sign)

    # account.payment.group JI

    @api.onchange('student_line_ids')
    def _onchange_student_line_ids(self):
        if len(self.student_line_ids) > 0:
            payment_amount = sum(self.student_line_ids.mapped('paying_amount'))
            if payment_amount <= self.temp_amount and payment_amount != 0.0:
                self.amount = payment_amount

    def action_validate_invoice_payment(self):
        """ Posts a payment used to pay an invoice. This function only posts the
        payment by default but can be overridden to apply specific post or pre-processing.
        It is called by the "validate" button of the popup window
        triggered on invoice form by the "Register Payment" button.
        """
        if any(len(record.invoice_ids) != 1 for record in self):
            # For multiple invoices, there is account.register.payments wizard
            raise UserError(_("This method should only be called to process a single invoice's payment."))

        if self.amount > self.temp_amount:
            raise UserError(_("Payment Amount should be less than or equal to Total Remaining Amount."))

        for line in self.student_line_ids:
            if line.paying_amount > line.current_due_amount:
                raise UserError(
                    _("Student Fee Amount of Paying Amount should be less than or equal to Current Due Amount."))

        student_total_amount = 0.00
        for line in self.student_line_ids:
            student_total_amount += line.paying_amount
            student_total_amount = (math.ceil(student_total_amount * 100) / 100)

        invoice = self.env['account.invoice'].browse(self._context.get('active_id'))
        for line1 in invoice.student_line_ids:
            amount = 0.0
            for stud_line in self.student_line_ids:
                if stud_line.name == line1.name:
                    amount = line1.paid_amount + stud_line.paying_amount
                    line1.write({'paid_amount': amount, 'paying_amount': 0})

        if student_total_amount != self.amount:
            raise UserError(_("Total Paying Amount of student and Payment Amount should be equal."))

        return self.post()


class ReportPartnerLedger(models.AbstractModel):
    _inherit = 'report.account.report_partnerledger'

    @api.model
    def get_report_values(self, docids, data=None):
        res = super(ReportPartnerLedger, self).get_report_values(docids, data)
        if 'school.parent' == self._context['active_model']:
            obj_parent = self.env['school.parent'].browse(self._context.get('active_id'))
            res.update({'doc_ids': [obj_parent.partner_id.id], 'docs': [obj_parent.partner_id]})
        return res
