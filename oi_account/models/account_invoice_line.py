'''
Created on Sep 17, 2018

@author: Zuhair Hammadi
'''
from odoo import models, api

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        company_id = self.invoice_id.company_id.id or self.env.user.company_id.id
        return super(AccountInvoiceLine, self.with_context(force_company = company_id))._onchange_product_id()