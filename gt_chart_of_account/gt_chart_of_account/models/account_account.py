# -*- coding: utf-8 -*-
##############################################################################
#
#    Globalteckz Pvt Ltd
#    Copyright (C) 2013-Today(www.globalteckz.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import fields, models ,api, _
from tempfile import TemporaryFile
from odoo.exceptions import UserError, ValidationError
from datetime import  datetime
from odoo.exceptions import UserError
from odoo import api, exceptions, fields, models, _

import base64
import copy
import datetime
import io
from datetime import datetime
from dateutil.relativedelta import relativedelta
from datetime import datetime, timedelta
from datetime import date
from calendar import monthrange
from datetime import date
from dateutil.relativedelta import relativedelta
import xlrd
import collections
from collections import Counter
from xlrd import open_workbook
import csv
import base64
import sys
from odoo.tools import pycompat
import datetime
import calendar

class AccountAccount(models.Model):
    _inherit = 'account.account'
    
    parent_id = fields.Many2one('account.account', string='Parent Category')

class ResCompany(models.Model):
    _inherit = "res.company"
    
    









   