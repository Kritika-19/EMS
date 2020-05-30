'''
Created on Sep 16, 2018

@author: Zuhair Hammadi
'''
from odoo import models, api, fields

class Partner(models.Model):
    _inherit = "res.partner"
    
    @api.model
    def _account_domain(self, internal_type):
        company_id = self._context.get('force_company') or self.env.user.company_id.id
        return [('internal_type', '=', internal_type), ('deprecated', '=', False), ('company_id', '=', company_id)]    

    @api.model
    def _account_payable_domain(self):
        return self._account_domain('payable')
    
    @api.model
    def _account_receivable_domain(self):
        return self._account_domain('receivable')

    property_account_payable_id = fields.Many2one('account.account', domain= _account_payable_domain)
    property_account_receivable_id = fields.Many2one('account.account', domain= _account_receivable_domain)    