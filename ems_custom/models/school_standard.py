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


class StudentFeesStructureLine(models.Model):
    '''Student Fees Structure Line'''
    _inherit = 'student.fees.structure.line'

    classes = fields.Many2one('standard.standard', string='Class', required=False)
