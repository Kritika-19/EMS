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


class StudentStudent(models.Model):
    _inherit = 'student.student'

    @api.onchange('fee_structure_id', 'discount_ids', 'tax_ids')
    def onchange_fee_structure_id(self):
        list = []
        line_obj = self.env['new.student.fees.structure.line']
        for structure_line in self.fee_structure_id.structure_line_ids:
            vals = {'name': structure_line.name, 'code': structure_line.code, 'type': structure_line.type,
                    'amount': structure_line.amount, 'sequence': structure_line.sequence,
                    # 'line_ids': structure_line.line_ids.ids or False,
                    'account_id': structure_line.account_id.id or False, 'company_id': structure_line.company_id.id,
                    'currency_id': structure_line.currency_id.id or False,
                    'currency_symbol': structure_line.currency_symbol, 'arabic_name': structure_line.arabic_name,
                    'duration': structure_line.duration,
                    'new_student_id': self.id,
                    'classes': structure_line.classes.id or False,
                    }
            created_obj = line_obj.create(vals)
            created_obj.discount_ids = self.discount_ids.ids
            created_obj.tax_ids = self.tax_ids.ids
            list.append(created_obj.id)

        self.line_ids = list
