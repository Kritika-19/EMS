from odoo import models, fields, api, tools, _

class AcademicPerformance(models.Model):
    _name = 'academic.performance'
    _description = 'Academic Performance'
    _rec_name = 'date'
    
    date = fields.Date(string='Date')
    teacher_id = fields.Many2one('school.teacher', string='Teacher')
    strength = fields.Integer(string='Strength')
    study_year_id = fields.Many2one('academic.year', string="Study Year")
    student_id = fields.Many2one('student.student', string='Student')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    