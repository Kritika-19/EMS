from odoo import models, fields, api, tools, _

class StudentAttendance(models.Model):
    _name = 'student.attendance'
    _description = 'Student Attendance'
    _rec_name = 'study_year_id'
    
    study_year_id = fields.Many2one('academic.year', string="Study Year")
    date = fields.Date(string='Date')
    day_name = fields.Char(string='Day Name')
    hour = fields.Float(string='Hour')
    absent_type = fields.Float(string='Absent Type')
    note = fields.Char(string='Note')
    student_id = fields.Many2one('student.student', string='Student')
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    