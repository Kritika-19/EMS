from odoo import models, fields, api, tools, _

class Classification(models.Model):
    _name = 'classification'
    _description = 'Classification'
    
    name = fields.Char(string='Classification')