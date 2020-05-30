# -*- encoding: UTF-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today Laxicon Solution.
#    (<http://laxicon.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from odoo import api, fields, models, _


class SchoolStandard(models.Model):
    ''' Defining a standard related to school '''
    _inherit = 'school.standard'

    class_code = fields.Char(string="Code", copy=False)
    arabic_name = fields.Char(string="Arabic Name")
    stage = fields.Selection([('enable', 'Enable'), ('disable', 'Disable')], string="State", default="enable")


class StudentFeesStructure(models.Model):
    '''Fees structure'''
    _inherit = 'student.fees.structure'

    # line_ids = fields.One2many('student.fees.structure.line', 'fee_struct_id', string='Fees Structure')
    structure_line_ids = fields.One2many('fee.structure.line', 'student_fee_id', string='Fees Structure')
    academic_year = fields.Many2one('academic.year', string='Academic Years')


class StudentFeesStructureLine(models.Model):
    '''Student Fees Structure Line'''
    _inherit = 'student.fees.structure.line'

    classes = fields.Many2one('standard.standard', string='Class', required=False)
    # fee_struct_id = fields.Many2one('student.fees.structure', string="Structure")


class FeeStructureLine(models.Model):
    _name = "fee.structure.line"

    name = fields.Char(related='structre_line_id.name', string="name")
    structre_line_id = fields.Many2one('student.fees.structure.line', string="Fees Head")
    student_fee_id = fields.Many2one('student.fees.structure', string="Fee structure")
    amount = fields.Float(string="Amount")
    code = fields.Char(related='structre_line_id.code', string='Code')
    account_id = fields.Many2one(related='structre_line_id.account_id', string="Account")
    company_id = fields.Many2one(related='structre_line_id.company_id', string='Company', change_default=True, default=lambda obj_c: obj_c.env['res.users'].browse([obj_c._uid])[0].company_id)
    currency_id = fields.Many2one(related='structre_line_id.currency_id', string='Currency')
    currency_symbol = fields.Char(related="currency_id.symbol", string='Symbol')
    arabic_name = fields.Char(related='structre_line_id.arabic_name', string='Arabic Name')
    academic_year = fields.Many2one(related='structre_line_id.academic_year', string='Academic Years')
