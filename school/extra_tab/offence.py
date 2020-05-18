from odoo import models, fields, api, tools, _

class Offence(models.Model):
    _name = 'offence'
    _description = 'Offence'
    _rec_name = 'subject_ids'
    
    subject_ids = fields.Many2many('subject.subject', 'subject_student_inh_rel','teacher_id', 'student_id', string='Subjects')
    date = fields.Date(string='Date')
    offence_type = fields.Char(string='Offence Type')
    teacher_id = fields.Many2one('school.teacher', string='Teacher')
    study_year_id = fields.Many2one('academic.year', string="Study Year")
    student_id = fields.Many2one('student.student', string='Student')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    