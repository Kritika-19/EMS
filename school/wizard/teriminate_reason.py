# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.exceptions import ValidationError


class TerminateReason(models.TransientModel):
    _name = "terminate.reason"

    reason = fields.Text('Reason')

    @api.multi
    def save_terminate(self):
        '''Override method to raise warning when fees payment of student is
        remaining when student is terminated'''
        student = self._context.get('active_id')
        student_obj = self.env['student.student'].browse(student)
        student_fees = self.env['student.payslip']. \
            search([('student_id', '=', student_obj.id),
                    ('state', 'in', ['confirm', 'pending'])])
        if student_fees:
            raise ValidationError(_('''You cannot terminate student because
                payment of fees of student is remaining!'''))
        return super(TerminateReason, self).save_terminate()

    @api.multi
    def save_terminate(self):
        '''Method to terminate student and change state to terminate'''
        self.env['student.student'
        ].browse(self._context.get('active_id')
                 ).write({'state': 'terminate',
                          'terminate_reason': self.reason,
                          'active': False})
        student_obj = self.env['student.student']. \
            browse(self._context.get('active_id'))
        student_obj.standard_id._compute_total_student()
        user = self.env['res.users']. \
            search([('id', '=', student_obj.user_id.id)])
        student_reminder = self.env['student.reminder']. \
            search([('stu_id', '=', student_obj.id)])
        for rec in student_reminder:
            rec.active = False
        if user:
            user.active = False