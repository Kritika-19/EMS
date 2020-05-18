from odoo import api, fields, models, _
import time
from datetime import datetime, date, time, timedelta
from odoo.exceptions import ValidationError, Warning as UserError
from dateutil.relativedelta import relativedelta
from dateutil import relativedelta
from dateutil.rrule import rrule, MONTHLY
import datetime as dt
import pytz
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


class subscription_line(models.Model):
    _name = 'subscription.line'

    subscription_id = fields.Many2one('school.parent', string='Subscription ID')
    subscription_no = fields.Integer(string='Subscription No', readonly=True)
    sub_start_date = fields.Date(string='From Date', readonly=True)
    sub_end_date = fields.Date(string='To Date', readonly=True)
    sub_amount = fields.Float(string='Amount', digits=(5, 2), readonly=True)
    subscription_status = fields.Boolean("Check State")
    invoice_id = fields.Many2one('account.invoice')
    amount_paid = fields.Float(compute='_compute_amount_paid', string='Amount Paid')
    status = fields.Selection([('paid', 'Paid'), ('not_paid', 'Not Paid'), ('partially_paid', 'Partially Paid')],
                              default='not_paid', compute='_compute_amount_paid', string='Invoice Status')

    @api.depends('invoice_id')
    def _compute_amount_paid(self):
        for record in self:
            if record.invoice_id:
                record.amount_paid = sum(
                    record.invoice_id.payment_ids.filtered(lambda s: s.state == 'posted').mapped('amount'))
                if record.sub_amount == record.amount_paid:
                    record.status = 'paid'
                elif record.amount_paid > 0 and record.amount_paid < record.sub_amount:
                    record.status = 'partially_paid'

    @api.one
    def sub_invoices(self):
        line_list = []
        invoice_obj = self.env['account.invoice']
        inv_fields = invoice_obj.fields_get()
        default_value = invoice_obj.default_get(inv_fields)

        invoice_line = self.env['account.invoice.line']
        line_f = invoice_line.fields_get()
        default_line = invoice_line.default_get(line_f)

        default_value.update({'partner_id': self.subscription_id.partner_id.id, 'date_invoice': self.sub_start_date})
        invoice = invoice_obj.new(default_value)
        invoice._onchange_partner_id()
        default_value.update({'account_id': invoice.account_id.id, 'date_due': self.sub_end_date})

        inv_id = invoice.create(default_value)

        #         if self.subscription_id.end_date == self.sub_end_date:
        #             self.subscription_id.action_done()

        for invoice_lst in self.subscription_id.new_line_ids:
            if invoice_lst.inv_state == 'non_invoiced':
                discount_amount = 0.0
                for discount in invoice_lst.discount_ids:
                    discount_amount += discount.amount
                if discount_amount > 100:
                    raise UserError('Discount is exceeding 100% so please adjust the Discount into Student Page.')
                tax_ids = [tax.id for tax in invoice_lst.tax_ids]
                default_line.update({
                    'name': invoice_lst.new_student_id.name,
                    'quantity': 1.000,
                    'price_unit': invoice_lst.amount / self.subscription_id.subscription_duration,
                    'account_id': invoice_lst.account_id.id or False,
                    'invoice_line_tax_ids': [(6, 0, tax_ids)],
                    'discount': discount_amount,
                    'fee_type': invoice_lst.name,
                    'student_id': invoice_lst.new_student_id.id,
                })
                inv_line = invoice_line.new(default_line)
                inv_line._onchange_product_id()
                default_line.update({'invoice_id': inv_id.id,
                                     'account_id': inv_line.with_context(
                                         {'journal_id': self.subscription_id.journal_id.id})._default_account()})
                created_line = invoice_line.create(default_line)
                line_list.append(created_line.id)
            # inv_id.signal_workflow('invoice_open')
        #         inv_id.write({'amount_total': self.subscription_id.total})
        inv_id.invoice_line_ids = line_list
        inv_id.action_invoice_open()
        inv_id.compute_taxes()
        self.invoice_id = inv_id.id

        template_obj = self.env.ref('account.email_template_edi_invoice', False)
        # template_obj.send_mail(inv_id.id)
        return True

    @api.multi
    def view_sub_invoice(self):
        invoice_id = self.invoice_id

        view_ref = self.env['ir.model.data'].get_object_reference('account', 'invoice_form')
        view_id = view_ref[1] if view_ref else False
        res = {
            'type': 'ir.actions.act_window',
            'name': _('Customer Invoice'),
            'res_model': 'account.invoice',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'res_id': invoice_id.id,
            'target': 'current'
        }
        return res

    @api.model
    def subscription_email_details_scheduler(self):
        search_ids = self.env['subscription.line'].search([('invoice_id', '!=', False), ])
        for due in search_ids:
            if due.subscription_id.is_subscription:
                remider_days = due.subscription_id.reminder_days
                due_date = due.sub_end_date
                mydate = datetime.strptime(due_date, "%Y-%m-%d").date()
                mydate = mydate - timedelta(days=remider_days)
                curr_date = datetime.today().date()
                if curr_date == mydate:
                    if due.subscription_id.student_id.partner_id.email and due.subscription_id.student_id.partner_id.email.strip():
                        template = self.env.ref('school.subscription_email_months_details')
                        mail_id = template.send_mail(due.id)
                        mail_now = self.env['mail.mail'].browse(mail_id)
                        mail_now.send()
        return True
