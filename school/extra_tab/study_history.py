from odoo import models, fields, api, tools, _

class StudyHistoryTab(models.Model):
    _name = 'study.history.tab'
    _description = 'Study History Tab'
    _rec_name = 'study_year_id'
    
    study_year_id = fields.Many2one('academic.year', string="Study Year")
    class_id = fields.Many2one('school.standard', string="Class Name")
    division_id = fields.Many2one('standard.division', string="Division")
    school_id = fields.Many2one('school.school', string="School Name")
    region_id = fields.Many2one('school.region', string="School Name")
    average_grade = fields.Char(string="Average Grade")
    result = fields.Char(string="Result")
    note = fields.Char(string="Note")
    status = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string='Status')
    student_id = fields.Many2one('student.student', string='Student')
    
class Region(models.Model):
    _name = 'school.region'
    _description = 'School Region'
    
    name = fields.Char(string="School Region")
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    