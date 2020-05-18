import time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning as UserError
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


class ParentRelation(models.Model):
    '''Defining a Parent relation with child'''
    _name = "parent.relation"
    _description = "Parent-child relation information"

    name = fields.Char("Relation name", required=True)


class SchoolParent(models.Model):
    ''' Defining a Teacher information '''
    _name = 'school.parent'
    _description = 'Parent Information'

    @api.depends('sub_line_ids')
    def _get_invoiced(self):
        invoices = self.env['account.invoice'].search([('partner_id', '=', self.partner_id.id)])
        self.invoice_count = len(invoices.ids)

    @api.onchange('student_id')
    def onchange_student_id(self):
        self.standard_id = [(6, 0, [])]
        self.stand_id = [(6, 0, [])]
        standard_ids = [student.standard_id.id
                        for student in self.student_id]
        if standard_ids:
            stand_ids = [student.standard_id.standard_id.id
                         for student in self.student_id]
            self.standard_id = [(6, 0, standard_ids)]
            self.stand_id = [(6, 0, stand_ids)]

    ################################ Guardian Details ################################

    son_of_employee = fields.Boolean(string='Son of Employee')
    is_black_list = fields.Boolean(string='Is Black List')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    # guardian_black_list_date = fields.Date(string='Date')
    guardian_id_number = fields.Char(string='ID Number')
    # guardian_id_issued_place = fields.Char(string='Issued Place')
    guardian_id_issued_place = fields.Many2one('res.country', string='Issued Place')
    guardian_id_expiry_date = fields.Date(string='Expiry Date')
    guardian_arabic_name = fields.Char(string='Arabic Name')
    # guardian_name = fields.Char(string='Guardian Name')
    guardian_relationship_student = fields.Many2one('relationship', string='Relationship')
    guardian_nationality = fields.Many2one('res.country', string='Nationality')
    lang_id = fields.Many2one('res.lang', 'Language')
    guardian_passport_no = fields.Char(string='Passport No')
    # guardian_passport_issued_place = fields.Date(string='Issued Place')
    guardian_passport_issued_place = fields.Many2one('res.country', string='Issued Place')
    guardian_passport_expiry_date = fields.Date(string='Expiry Date')
    guardian_address = fields.Text(string='Address')
    guardian_work_address = fields.Text(string='Work Address')
    guardian_home_tel = fields.Char(string='Home Tel')
    guardian_mobile1 = fields.Char(string='Mobile No1')
    guardian_mobile2 = fields.Char(string='Mobile No2')
    guardian_email = fields.Char(string='Email')
    guardian_work = fields.Char(string='Work')
    guardian_document = fields.Binary(string='Document')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        if self.employee_id:
            self.guardian_id_number = self.employee_id.identification_id
            self.guardian_passport_no = self.employee_id.passport_id
            self.guardian_nationality = self.employee_id.country_id.id
            self.guardian_work_address = self.employee_id.address_id.name
            self.title = self.employee_id.address_home_id.title.id

    ########################### Subscription fields #############################

    invoice_count = fields.Integer(string='# of Invoices', compute='_get_invoiced', readonly=True)
    is_subscription = fields.Boolean(string="is a Subscription", default=True)
    subscription_amount = fields.Float(string="Subscription Amount", readonly=True)
    periodicity = fields.Selection([('month', 'Month'),
                                    ('quarterly', 'Quarterly'),
                                    ('half_year', 'Half Yearly'),
                                    ('year', 'Year'),
                                    ], string="Periodicity", default='month')
    property_account_receivable_id = fields.Many2one('account.account', 'Account Receivable')
    property_account_payable_id = fields.Many2one('account.account', 'Account Payable')
    subscription_duration = fields.Integer(string='Payment Duration', compute='compute_periodicity', default=12)
    issue_date = fields.Date(string='Start Date')
    # Muhammad Jawaid Iqbal
    # remove Subscription to Payment
    end_date = fields.Date(compute="subscription_issudate", store='True', string='End Payment Date')
    reminder_days = fields.Integer(string='Reminder Days')
    cc_in_mail = fields.Char(string='Cc in Mail')
    sub_line_ids = fields.One2many('subscription.line', 'subscription_id')
    check_inv = fields.Boolean(string='Check Invoice', copy=False, default=False)
    renew_so = fields.Many2one('sale.order')
    currency_id = fields.Many2one('res.currency', string='Currency')
    currency_symbol = fields.Char(related='currency_id.symbol', string='Symbol')
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 change_default=True, readonly=True,
                                 default=lambda obj_c: obj_c.env['res.users'].
                                 browse([obj_c._uid])[0].company_id)

    ########################### Subscription fields #############################

    partner_id = fields.Many2one('res.partner', string='User ID', ondelete="cascade", delegate=True, required=True)
    relation_id = fields.Many2one('parent.relation', string="Relation with Child")
    student_id = fields.Many2many('student.student', 'students_parents_rel', 'students_parent_id', 'student_id',
                                  string='Children')
    standard_id = fields.Many2many('school.standard', 'school_standard_parent_rel', 'class_parent_id', 'class_id',
                                   string='Academic Class')
    stand_id = fields.Many2many('standard.standard', 'standard_standard_parent_rel', 'standard_parent_id',
                                'standard_id', string='Academic Class')
    teacher_id = fields.Many2one('school.teacher', string='Teacher', related="standard_id.user_id", store=True)

    total = fields.Float(string="Total", compute='compute_new_line_ids')
    invoiced = fields.Float(string="Invoiced", compute='compute_new_line_ids')
    non_invoiced = fields.Float(string="Non Invoiced", compute='compute_new_line_ids')

    new_line_ids = fields.One2many('parent.student.fees.structure.line', 'new_parent_id', string='Fee Structure Lines')
    journal_id = fields.Many2one('account.journal', string='Journal', required=True)

    ########################### Subscription Codes #############################

    @api.multi
    def action_view_invoice(self):
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        invoices = self.env['account.invoice'].search([('partner_id', '=', self.partner_id.id)])
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif invoices:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.one
    @api.depends('new_line_ids')
    def compute_new_line_ids(self):
        total_amount = 0
        invoiced = 0
        non_invoiced = 0
        for data in self.new_line_ids:
            total_amount += data.amount
            if data.inv_state == 'invoiced':
                invoiced += data.amount
            if data.inv_state == 'non_invoiced':
                non_invoiced += data.amount
        self.total = total_amount
        self.invoiced = invoiced
        self.non_invoiced = non_invoiced

    @api.one
    @api.depends('periodicity')
    def compute_periodicity(self):
        if self.periodicity == 'month':
            self.subscription_duration = 12
        if self.periodicity == 'quarterly':
            self.subscription_duration = 4
        if self.periodicity == 'half_year':
            self.subscription_duration = 2
        if self.periodicity == 'year':
            self.subscription_duration = 1

    @api.one
    @api.depends('issue_date', 'periodicity', 'subscription_duration')
    def subscription_issudate(self):
        mnth = self.subscription_duration
        if type(self.issue_date) is bool:
            return

        mydate = datetime.strptime(self.issue_date, "%Y-%m-%d")
        self.end_date = mydate + relativedelta(years=1, days=-1)

    @api.multi
    def generate_sub_invoice_lines(self):
        amount = 0
        if self.is_subscription == True:
            total_sub = int(self.subscription_duration)
            self._cr.execute("delete from subscription_line where subscription_id =  %s" % (self.id))
            per_sub_amount = self.total / self.subscription_duration
            if type(self.issue_date) is bool:
                return
            mydate = datetime.strptime(self.issue_date, "%Y-%m-%d")

            if self.periodicity == 'month':
                add_months = 1
            if self.periodicity == 'quarterly':
                add_months = 3
            if self.periodicity == 'half_year':
                add_months = 6
            if self.periodicity == 'year':
                add_months = 12

            for i in range(1, total_sub + 1):
                sub_start_date = mydate
                sub_end_date = sub_start_date + relativedelta(months=add_months, days=-1)
                mydate = sub_end_date + relativedelta(days=1)
                self.update({'check_inv': True})
                sub_liens = {
                    'subscription_id': self.id,
                    'subscription_no': i,
                    'sub_start_date': sub_start_date,
                    'sub_end_date': sub_end_date,
                    'sub_amount': per_sub_amount

                }
                emi_line_id = self.env['subscription.line'].create(sub_liens)
                emi_line_id.sub_invoices()

        else:
            raise UserError('Please first check the is_subscription')

        if self.subscription_duration == 0:
            raise UserError('Please enter the Subscription Duration')

    #         for line in self.new_line_ids:
    #             line.inv_state = 'invoiced'

    @api.multi
    def action_cancel(self):
        for state_change in self.sub_line_ids:
            state_change.subscription_status = True
        self.write({'state': 'cancel'})

    ########################### Subscription Codes #############################

    @api.model
    def create(self, vals):
        parent_id = super(SchoolParent, self).create(vals)
        parent_grp_id = self.env.ref('school.group_school_parent')
        emp_grp = self.env.ref('base.group_user')
        parent_group_ids = [emp_grp.id, parent_grp_id.id]
        if vals.get('parent_create_mng'):
            return parent_id
        user_vals = {'name': parent_id.name,
                     'login': parent_id.guardian_email,
                     'email': parent_id.guardian_email,
                     'partner_id': parent_id.partner_id.id,
                     'groups_id': [(6, 0, parent_group_ids)]
                     }
        self.env['res.users'].create(user_vals)
        return parent_id

    @api.onchange('state_id')
    def onchange_state(self):
        self.country_id = False
        if self.state_id:
            self.country_id = self.state_id.country_id.id

    @api.onchange('student_id')
    def onchange_student_student_id(self):
        list = []
        line_obj = self.env['parent.student.fees.structure.line']
        for student in self.student_id:
            for structure_line in student.line_ids:
                vals = {'name': structure_line.name, 'code': structure_line.code, 'type': structure_line.type,
                        'amount': structure_line.amount, 'sequence': structure_line.sequence,
                        'line_ids': structure_line.line_ids.ids,
                        'account_id': structure_line.account_id.id, 'company_id': structure_line.company_id.id,
                        'currency_id': structure_line.currency_id.id,
                        'currency_symbol': structure_line.currency_symbol, 'arabic_name': structure_line.arabic_name,
                        'duration': structure_line.duration,
                        'new_student_id': student.id, 'classes': structure_line.classes.id
                        }
                created_obj = line_obj.create(vals)
                created_obj.discount_ids = structure_line.discount_ids.ids
                created_obj.tax_ids = structure_line.tax_ids.ids
                list.append(created_obj.id)

        self.new_line_ids = list


class NewStudentFeesStructureLine(models.Model):
    '''Student Fees Structure Line'''
    _name = 'parent.student.fees.structure.line'
    _description = 'Parent Student Fees Structure Line'
    _order = 'sequence'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    type = fields.Selection([('month', 'Monthly'),
                             ('year', 'Yearly'),
                             ('range', 'Range')],
                            string='Duration', required=True)
    amount = fields.Float(string='Amount', digits=(16, 2))
    sequence = fields.Integer(string='Sequence')
    line_ids = fields.One2many('student.payslip.line.line', 'slipline1_id', string='Calculations')
    account_id = fields.Many2one('account.account', string="Account")
    company_id = fields.Many2one('res.company', string='Company',
                                 change_default=True,
                                 default=lambda obj_c: obj_c.env['res.users'].
                                 browse([obj_c._uid])[0].company_id)
    currency_id = fields.Many2one('res.currency', string='Currency')
    currency_symbol = fields.Char(related="currency_id.symbol", string='Symbol')

    arabic_name = fields.Char(string='Arabic Name')
    classes = fields.Many2one('standard.standard', string='Class', required=True)
    academic_year = fields.Many2one('academic.year', string='Academic Years')
    duration = fields.Char(string='Duration')
    new_parent_id = fields.Many2one('school.parent', string='Parent')
    new_student_id = fields.Many2one('student.student', string='Student')
    discount_ids = fields.Many2many('ems.discount', 'parent_structure_discount_rel', 'structure_line_id', 'discount_id',
                                    string='Discount')
    tax_ids = fields.Many2many('account.tax', 'parent_structure_line_taxes_rel', 'structure_line_id', 'tax_id',
                               string="Tax")
    inv_state = fields.Selection([('invoiced', 'Invoiced'), ('non_invoiced', 'Non Invoiced')],
                                 string='Invoice Status', readonly=True, default='non_invoiced')

    @api.onchange('company_id')
    def set_currency_company(self):
        for rec in self:
            rec.currency_id = rec.company_id.currency_id.id
