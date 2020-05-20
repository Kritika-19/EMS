import time
import math

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _

class EMSDiscount(models.Model):
    _name = 'ems.discount'
    _description = 'EMS Discount'
    
    name = fields.Char(string='Discount Name', required=True, translate=True)
    arabic_name = fields.Char(string='Arabic Name', translate=True)
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    amount = fields.Float(required=True, digits=(16, 4))
    account_id = fields.Many2one('account.account',string='Discount Account')
    description = fields.Char(string='Label on Invoices', translate=True)
    
    @api.model
    def create(self, vals):
        res = super(EMSDiscount, self).create(vals)
        if res.amount < 0 or res.amount > 100 :
            raise UserError('Discount should be greater than 0/zero and less than 100.')
        return res

    @api.multi
    def write(self, vals):
        if vals.get('amount') < 0 or vals.get('amount') > 100:
            raise UserError('Discount should be greater than 0/zero and less than 100.')
        return super(EMSDiscount, self).write(vals)



























