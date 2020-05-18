from odoo import models, fields, api, tools, _

class SMSTab(models.Model):
    _name = 'sms.tab'
    _description = 'SMS Tab'
    _rec_name = 'date'
    
    date = fields.Date(string='Date')
    sms_text = fields.Text(string='SMS Text')
    mobile = fields.Char('Mobile')
    student_id = fields.Many2one('student.student', string='Student')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    