import time
import base64
from datetime import date, datetime
from odoo import models, fields, api, tools, _
from odoo.modules import get_module_resource
from odoo.exceptions import except_orm
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from . import school


class StudentStudent(models.Model):
    _inherit = 'student.student'

    ################################ Others ################################

    mother_name_english = fields.Char('Mother Full English Name')
    mother_name_arabic = fields.Char('Mother Full Arabic Name')
    mother_passport = fields.Char('Mother Passport No')
    mother_nationality = fields.Many2one('res.country', string='Nationality')
    mother_mobile = fields.Char('Mother Mobile No')
    mother_email = fields.Char('Mother Email')
    mother_job_description = fields.Text('Mother Job Description')

    ################################ Home Address ################################

    home_country_id = fields.Many2one('res.country', string='Country')
    home_city = fields.Char()
    home_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
    home_street = fields.Char(string='Street Name')
    home_building_no = fields.Char(sting='Building No')
    zip = fields.Char(change_default=True)
    coordinates = fields.Char(string='Coordinates')

    ################################ Emergency Info ################################

    emergency_name = fields.Char(string='Name')
    emergency_relationship = fields.Many2one('relationship', string='Relationship')
    emergency_contact1 = fields.Char(string='1st Contact No')
    emergency_contact2 = fields.Char(string='2nd Contact No')

    ################################ Student State ################################

    student_state = fields.Char(string='Student State')
    student_state_date = fields.Date(string='Date')
    last_year_record_state = fields.Char(string='Last Year Record State')
    current_record_state = fields.Char(string='Current Record State')
    transfer_school = fields.Char(string='Transfer School')
    transfer_date = fields.Char(string='Transfer Date')
    last_result = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string='Last Result')

    ################################ Information Join To School ################################

    adopt_policy = fields.Boolean(string='Adopt a policy of tuition fees for students according to grade levels')
    join_study_year = fields.Many2one("academic.year", string='Join Study Year')
    join_class = fields.Many2one("school.standard", string='Join Class')

    ################################ Waiting For Student Entering ################################

    complete_application_form = fields.Boolean(string='Complete Application Form')
    place_and_date_boolean = fields.Boolean(string='Place and Date of Issue')
    place_and_date_char = fields.Char(string='Place and Date of Issue')
    expiry_date_boolean = fields.Boolean(string='Expiry Date')
    expiry_date_char = fields.Char(string='Expiry Date')
    valid_residence_boolean = fields.Boolean(string='Valid Residence')
    expiry_residence_char = fields.Char(string='Valid Residence')
    photo_to_deputy = fields.Boolean(string='Photo to Deputy')
    stamped_signed_by_school = fields.Boolean(string='Stamped And Signed By School')
    authenticated_by_local_education_authority = fields.Boolean(string='Authenticated by Local Education Authority')
    awaiting = fields.Text(string='Awaiting')
    ###################### Binary fields #############################
    copies_of_child_id = fields.Binary('Copies of Child ID Showing')
    copies_of_child_birth = fields.Binary('Copies of Child Birth Certificate')
    passport_size_photo = fields.Binary('Passport Size Photographs of Child')
    health_form = fields.Binary('Complete Data and Health Forms When Child Is Accepted')
    tranfer_latter = fields.Binary('Transfer Latter/Certificate stating child Previous Class')
    ###################### Curriculum #############################
    curriculum = fields.Selection([('new_student', 'New Student'), ('transferred', 'Transferred')], string='Curriculum')
    curr_school_name = fields.Char(string='School Name')
    curr_educational_regions = fields.Char(string='Educational Regions')
    curr_last_result = fields.Selection([('pass', 'Pass'), ('fail', 'Fail')], string='Last School Result')
    curr_detail = fields.Text(string='Details of The Previous Curriculum if Possible')
    family_members = fields.Char(string='Family Members')
    student_order = fields.Char(string='Student Order')
    health_status = fields.Char(string='Health Status')
    cause_of_leakage = fields.Char(string='Cause')
    type_of_help = fields.Char(string='Type Of Help')
    family_income = fields.Char(string='Family Income')
    receipt_card_relief = fields.Char(string='Receipt Card Relief')
    social_status = fields.Char(string='Social Status')

    ################################ SMS ################################

    sms_mobile1 = fields.Char('Mobile1')
    sms_mobile2 = fields.Char('Mobile2')
    sms_text = fields.Text('SMS Text')
    sent_msg_ids = fields.One2many('sms.tab', 'student_id', string='Messages sent')

    ################################ Study History ################################

    study_history_ids = fields.One2many('study.history.tab', 'student_id', string='Messages sent')

    ################################ Academic Performance ################################

    academic_per_ids = fields.One2many('academic.performance', 'student_id', string='Academic Performance')

    ################################ Attendance ################################

    attendance_ids = fields.One2many('student.attendance', 'student_id', string='Attendance')

    ################################ Offence ################################

    offence_ids = fields.One2many('offence', 'student_id', string='Offence')

    ################################ Notification ################################

    notification_ids = fields.One2many('notification', 'student_id', string='Notification')

    ################################ Immunization Info ################################

    tetanus = fields.Char(string='Tetanus')
    dephtheria = fields.Char(string='Dephtheria')
    polio = fields.Char(string='Polio')
    mmr = fields.Char(string='Measles,Mumps,Rubella (MMR)')
    name_medication = fields.Text(string='Name of Medication')
    dose = fields.Text(string='Dose')
    medicine_for_school = fields.Boolean(string='Will you send medicine for the school to keep?')
    medicine_carry_child = fields.Boolean(string='Do you prefer to have your child carry the medicine with him?')
    medicine_notes = fields.Text(string='Please state any significant medical restriction or pertinent medical info')

    ################################ Student Details ################################
    student_number = fields.Char(string='Student Number')
    student_type = fields.Many2one('student.type', string='Student Type')
    student_reference_no = fields.Char(string='Reference No')
    student_first_name = fields.Char(string='Student First English Name')
    student_first_name_arabic = fields.Char(string='Student First Arabic Name')
    student_father_full_name = fields.Char(string='Father Full English Name')
    student_father_full_name_arabic = fields.Char(string='Father Full Arabic Name')
    student_id_number = fields.Char(string='ID Number')
    # student_id_issued_place = fields.Char(string='Issued Place')
    student_id_issued_place = fields.Many2one('res.country', string='Issued Place')
    student_id_issued_date = fields.Date(string='Issued Date')
    student_id_expiry_date = fields.Date(string='Expiry Date')
    student_passport_no = fields.Char(string='Passport No')
    # student_passport_issued_place = fields.Char(string='Issued Place')
    student_passport_issued_place = fields.Many2one('res.country', string='Issued Place')
    student_passport_issued_date = fields.Date(string='Issued Date')
    student_passport_expiry_date = fields.Date(string='Expiry Date')
    student_name_in_passport_arabic = fields.Char(string='Name in passport')
    student_name_in_passport_english = fields.Char(string='Name in passport English')
    student_nationality = fields.Many2one('res.country', string='Nationality')
    student_first_language = fields.Many2one('mother.toungue', string="Student's First Language")
    english_knowledge = fields.Selection([('fluent', 'Fluent'), ('adequate', 'Adequate'), ('nil', 'Nil')],
                                         string='Knowledge Of English')
    # student_birth_place = fields.Char(string='Place')
    student_birth_place = fields.Many2one('res.country', string='Place')
    father_education_level = fields.Many2one('education.level', string='Father Education Level')
    mother_education_level = fields.Many2one('education.level', string='Mother Education Level')
    father_employment_place = fields.Char(string='Father Employment Place')
    mother_employment_place = fields.Char(string='Mother Employment Place')
    father_work_tel_no = fields.Char(string='Father Work Tel No')
    mother_work_tel_no = fields.Char(string='Mother Work Tel No')
    father_mobile_no = fields.Char(string='Father Mobile No')
    mother_mobile_no = fields.Char(string='Mother Mobile No')
    father_email = fields.Char(string='Father Email')
    mother_email = fields.Char(string='Mother Email')
    home_address = fields.Text(string='Home Address')
    home_tel_no = fields.Char(string='Home Tel No')
    classification1 = fields.Many2one('classification', string='Student Classification 1')
    classification2 = fields.Many2one('classification', string='Student Classification 2')
    is_registered_noor = fields.Boolean(string='Is Registered Noor')
    noor_registered_no = fields.Char(string='Noor Registered No')
    ################################ Current Registration ################################
    branch = fields.Many2one('student.branch', string='Branch')
    previously_registered = fields.Boolean(string='Previously Registered')
    arabic_previous_school = fields.Char(string='Arabic Previous School')
    previously_school = fields.Many2one('school.school', string='Previous School')
    previously_class = fields.Many2one('school.standard', string='Previous Class')

    ################################ Student Payslip ################################

    fee_structure_id = fields.Many2one('student.fees.structure', string="Fee Structure")
    line_ids = fields.One2many('new.student.fees.structure.line', 'new_student_id', string='Fee Structure Lines')

    @api.onchange('fee_structure_id', 'discount_ids', 'tax_ids')
    def onchange_fee_structure_id(self):
        list = []
        line_obj = self.env['new.student.fees.structure.line']
        for structure_line in self.fee_structure_id.line_ids:
            vals = {'name': structure_line.name, 'code': structure_line.code, 'type': structure_line.type,
                    'amount': structure_line.amount, 'sequence': structure_line.sequence,
                    'line_ids': structure_line.line_ids.ids or False,
                    'account_id': structure_line.account_id.id or False, 'company_id': structure_line.company_id.id,
                    'currency_id': structure_line.currency_id.id or False,
                    'currency_symbol': structure_line.currency_symbol, 'arabic_name': structure_line.arabic_name,
                    'duration': structure_line.duration,
                    'new_student_id': self.id, 'classes': structure_line.classes.id or False,
                    }
            created_obj = line_obj.create(vals)
            created_obj.discount_ids = self.discount_ids.ids
            created_obj.tax_ids = self.tax_ids.ids
            list.append(created_obj.id)

        self.line_ids = list

    @api.onchange('standard_id')
    def onchange_standard_standard_id(self):
        structure_obj = self.env['student.fees.structure'].search([('classes', '=', self.standard_id.standard_id.id)])
        for rec in self:
            if structure_obj:
                rec.fee_structure_id = structure_obj.id
            else:
                rec.fee_structure_id = False


class NewStudentFeesStructureLine(models.Model):
    '''Student Fees Structure Line'''
    _name = 'new.student.fees.structure.line'
    _description = 'New Student Fees Structure Line'
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
    new_student_id = fields.Many2one('student.student', string='Student')
    discount_ids = fields.Many2many('ems.discount', 'student_structure_discount_rel', 'structure_line_id',
                                    'discount_id', string='Discount')
    tax_ids = fields.Many2many('account.tax', 'structure_line_taxes_rel', 'structure_line_id', 'tax_id', string="Tax")

    @api.onchange('company_id')
    def set_currency_company(self):
        for rec in self:
            rec.currency_id = rec.company_id.currency_id.id
