'''
Created on Sep 17, 2018

@author: Zuhair Hammadi
'''
from odoo import models, api, _
from odoo.exceptions import ValidationError

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.constrains('account_id', 'invoice_line_ids', 'journal_id', 'company_id')
    def _check_company(self):
        for record in self:
            if record.account_id.company_id != record.company_id:
                raise ValidationError(_('Invalid Account for the company'))
            if record.journal_id.company_id != record.company_id:
                raise ValidationError(_('Invalid Journal for the company'))            
            for invoice_line in record.invoice_line_ids:
                if invoice_line.account_id.company_id != record.company_id:
                    raise ValidationError(_('Invalid invoice line account for the company'))
                
    @api.onchange('company_id')
    def _onchange_company_id(self):
        self.journal_id = self.with_context(company_id = self.company_id.id)._default_journal()
        for line in self.invoice_line_ids:
            line._onchange_product_id()