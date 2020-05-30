'''
Created on Sep 17, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields, api

class ProductCategory(models.Model):
    _inherit = "product.category"
    
    @api.model
    def _account_domain(self):
        company_id = self._context.get('force_company') or self.env.user.company_id.id
        return [('internal_type', '=', 'other'), ('deprecated', '=', False), ('company_id', '=', company_id)]        

    property_account_income_categ_id = fields.Many2one('account.account', domain = _account_domain)
    
    property_account_expense_categ_id = fields.Many2one('account.account', domain = _account_domain)