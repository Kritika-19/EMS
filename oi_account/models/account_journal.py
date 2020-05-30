'''
Created on Sep 13, 2018

@author: Zuhair Hammadi
'''
from odoo import models, fields

class AccountJournal(models.Model):
    _inherit = "account.journal"

    update_posted = fields.Boolean(default = True)