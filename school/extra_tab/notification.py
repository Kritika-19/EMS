from odoo import models, fields, api, tools, _

class Notification(models.Model):
    _name = 'notification'
    _description = 'Notification'
    _rec_name = 'study_year_id'
    
    study_year_id = fields.Many2one('academic.year', string="Study Year")
    description1 = fields.Char(string='Description 1')
    description2 = fields.Char(string='Description 2')
    status = fields.Char(string='Status')
    student_id = fields.Many2one('student.student', string='Student')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    