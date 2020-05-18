from odoo import models, fields, api, tools, _

class Relationship(models.Model):
    _name = 'relationship'
    _description = 'Relationship'

    name = fields.Char(string='Relationship')