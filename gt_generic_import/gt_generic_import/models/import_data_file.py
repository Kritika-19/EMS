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

class Invoice_wizard(models.TransientModel):
    _name = 'invoice.wizard'

    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")
    state = fields.Selection([('draft', 'Draft'), ('validate', 'Validate')],'State')
    seq_opt = fields.Selection([('f_sequence', 'File Sequence'), ('s_sequence', 'System Sequence')], string='Sequence Option')
    type = fields.Selection([('out_invoice', 'Customer'), ('in_invoice', 'Vendor')], string='Type')

    @api.multi
    def Import_customer_invoice(self):
        partner_obj = self.env['res.partner']
        currency_obj = self.env['res.currency']
        product_obj = self.env['product.product']
        uom_obj = self.env['product.uom']
        salesperson_obj = self.env['res.users']
        inv_result = {}
        invoice_obj = self.env['account.invoice']
        invoice_obj_fileds = invoice_obj.fields_get()
        inv_default_value = invoice_obj.default_get(invoice_obj_fileds)
        invoice_line_obj = self.env['account.invoice.line']
        line_fields = invoice_line_obj.fields_get()
        file_data = False
        if self.select_file and self.data_file and self.seq_opt and self.type:
            if self.select_file == 'csv' :
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)),quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.select_file == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or seqeuance properly'))
        for row in file_data:

            taxes_ids = self.env['account.tax'].search([('name', '=', row[9]),('type_tax_use', '=', 'sale')])
            dt = datetime.datetime.strptime(row[10], "%d-%m-%Y")
            print ("::::::::::::::::::::::::::::::::::::::::::::::::::::::row[9]:::::::::::::",dt)

            partner = partner_obj.search([('name', 'like', row[1])])
            currency = currency_obj.search([('name', 'like', row[2])])
            product = product_obj.search([('name', 'like', row[3])])
            uom = uom_obj.search([('name', 'like', row[5])])
            salesperson = salesperson_obj.search([('name', 'like', row[8])])
            if not partner:
                raise ValidationError("Customer '%s' not found"%row[1])
            if not product:
                raise ValidationError("Product  '%s' not found"%row[3])
            if not currency:
                raise ValidationError("currency  '%s' not found"%row[2])
            if not salesperson:
                raise ValidationError("Sales User  '%s' not found"%row[8])
            inv_obj_update = inv_default_value.copy()
            inv_obj_update.update({
                'partner_id': partner[0].id or row[0],
                'move_name': self.seq_opt == 'f_sequence' and row[0] or '',
                'name': self.seq_opt == 'f_sequence' and row[0] or '',
                'date_invoice': dt,
                'currency_id': currency and currency.id or False,
                'user_id': salesperson and salesperson[0].id or False,
                'type': self.type =='out_invoice' and 'out_invoice' or 'in_invoice',
            })

            inv_obj = invoice_obj.new(inv_obj_update)
            inv_obj._onchange_partner_id()
            inv_obj_update.update({'account_id': inv_obj.account_id.id , 'journal_id': inv_obj.journal_id.id,'currency_id': inv_obj.currency_id.id})
            line_v1 = invoice_line_obj.with_context({'journal_id': inv_obj.journal_id.id}).default_get(line_fields)
            line_vals = line_v1.copy()
            line_vals.update({'name': row[6], 'product_id': product.id, 'quantity': row[4] and int(row[4]) or 1,
                          'uom_id': product.uom_id.id, 'price_unit': row[7] and int(row[7]) or 1,'invoice_line_tax_ids': [(6,0, taxes_ids.ids)] or False,
                             })
            l2 = [(0, 0, line_vals)]

            line_obj = invoice_line_obj.new(l2[0][2])
            line_obj._onchange_product_id()
            l2[0][2].update({'name': line_obj.name, 'account_id': line_obj.account_id.id ,
                           # 'invoice_line_tax_ids': line_obj.invoice_line_tax_ids and line_obj.invoice_line_tax_ids.ids or taxes_ids.ids or False,
                             'invoice_line_tax_ids': [(6,0, line_obj.invoice_line_tax_ids and line_obj.invoice_line_tax_ids.ids or taxes_ids.ids)] or False,
                             })
            if inv_result.get(row[0]):
                l1 = inv_result[row[0]]['invoice_line_ids']

                inv_result[row[0]].update({'invoice_line_ids': l1 + l2})
            if not inv_result.get(row[0]):
                inv_obj_update.update({'invoice_line_ids': l2})
                inv_result[row[0]] = inv_obj_update

        for invoice_data in inv_result.values():
            invoice_var = invoice_obj.create(invoice_data)
            if self.state == "validate":
                invoice_var.action_invoice_open()
        return True

class Sale_wizard(models.TransientModel):
    _name = 'sale.wizard'

    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")
    name = fields.Char('File name')
    seq_opt = fields.Selection([('f_sequence', 'File Sequence'), ('s_sequence', 'System Sequence')], string='Sequence Option')
    import_state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')],
                               string='Status')
    @api.multi
    def Import_sale_order(self):
        partner_obj = self.env['res.partner']
        currency_obj = self.env['res.currency']
        product_obj = self.env['product.product']
        uom_obj = self.env['product.uom']
        salesperson_obj = self.env['res.users']
        sale_result = {}

        sale_obj = self.env['sale.order']
        sale_obj_fileds = sale_obj.fields_get()
        sale_default_value = sale_obj.default_get(sale_obj_fileds)
        sale_line_obj = self.env['sale.order.line']
        line_fields = sale_line_obj.fields_get()
        file_data = False

        if self.select_file and self.data_file and self.seq_opt:
            if self.select_file == 'csv' :
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)),quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.select_file == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or seqeuance'))

        for row in file_data:
            print ("::::::::::::::::::::::::::::::::::::::::::::::::row[9]::::::::::::::::",row[9])
            dt = datetime.datetime.strptime(row[10], "%d-%m-%Y")

            tax_search = self.env['account.tax'].search([('name','=',row[9]),('type_tax_use','=','sale')])

            print ("::::::::::::::::::::::::::::::::::::::::::::::::tax_search::::::::::::::::", tax_search)



            partner = partner_obj.search([('name', 'like', row[1])])
            currency = currency_obj.search([('name', 'like', row[2])])
            product = product_obj.search([('name', 'like', row[3])])
            salesperson = salesperson_obj.search([('name', 'like', row[8])])
            if not partner:
                raise ValidationError("Customer '%s' not found"%row[1])
            if not product:
                raise ValidationError("Product  '%s' not found"%row[3])
            if not salesperson:
                raise ValidationError("Sales User  '%s' not found"%row[8])
            if not currency:
                raise ValidationError("Currency '%s' not found"%row[2])

            sale_obj_update = sale_default_value.copy()
            sale_obj_update.update({
                'partner_id': partner[0].id or row[0],
                'name': self.seq_opt == 'f_sequence' and row[0] or 'New',
                'currency_id': currency and currency.id or False,
                'user_id': salesperson and salesperson[0].id or False,
                'validity_date': dt,
            })
            sale_obj_new = sale_obj.new(sale_obj_update)
            sale_obj_new.onchange_partner_id()
            sale_obj_update.update({'currency_id': sale_obj_new.currency_id.id})

            line_v1 = sale_line_obj.default_get(line_fields)
            line_vals = line_v1.copy()

            line_vals.update({'name': row[6], 'product_id': product.id, 'quantity': row[4] and int(row[4]) or 1,
                          'uom_id': product.uom_id.id, 'price_unit': row[7] and int(row[7]) or 1,
                          'tax_id': [(6, 0, tax_search.ids)],
                          })
            print ("::::::::::::::::::::::::::::line_vals::::::::::::", line_vals)
            line_obj = sale_line_obj.new(line_vals)
            line_vals.update({'name': line_obj.name, 'tax_id': [(6,0, line_obj.tax_id and line_obj.tax_id.ids or tax_search.ids)] or "",
                             })
            l2 = [(0, 0, line_vals)]
            if sale_result.get(row[0]):
                l1 = sale_result[row[0]]['order_line']
                sale_result[row[0]].update({'order_line': l1 + l2})
            if not sale_result.get(row[0]):
                sale_obj_update.update({'order_line': l2})
                sale_result[row[0]] = sale_obj_update
        for sale_data in sale_result.values():
            sale_var = sale_obj.create(sale_data)
            if self.import_state == "confirm":
                sale_var.action_confirm()
        return True

class Purchase_wizard(models.TransientModel):
    _name = 'purchase.wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")
    name = fields.Char('File name')
    seq_opt = fields.Selection([('f_sequence', 'File Sequence'), ('s_sequence', 'System Sequence')],string='Sequence Option')
    state_stage = fields.Selection([('draft', 'Draft'), ('purchase', 'Purchase')], string='Import State')

    @api.multi
    def Import_purchase_order(self):
        partner_obj = self.env['res.partner']
        currency_obj = self.env['res.currency']
        product_obj = self.env['product.product']
        uom_obj = self.env['product.uom']
        salesperson_obj = self.env['res.users']
        purchase_result = {}

        purchase_obj = self.env['purchase.order']
        purchase_obj_fileds = purchase_obj.fields_get()
        purchase_default_value = purchase_obj.default_get(purchase_obj_fileds)
        purchase_line_obj = self.env['purchase.order.line']
        line_fields = purchase_line_obj.fields_get()
        file_data = False
        if self.select_file and self.data_file and self.seq_opt and self.state_stage:
            if self.select_file == 'csv' :
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)),quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.select_file == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or seqeuance'))
        for row in file_data:
            tax_search = self.env['account.tax'].search([('name', '=', row[8]),('type_tax_use', '=', 'sale')])

            dt = datetime.datetime.strptime(row[9], "%d-%m-%Y")
            print ("::::::::::::::::::::::::::::::::::::::::::::::::::::::row[9]:::::::::::::", dt)

            partner = partner_obj.search([('name', 'like', row[1])])
            currency = currency_obj.search([('name', 'like', row[2])])
            product = product_obj.search([('name', 'like', row[3])])
            uom = uom_obj.search([('name', 'like', row[5])])

            if not partner:
                raise ValidationError("Customer '%s' not found"%row[1])
            if not product:
                raise ValidationError("Product  '%s' not found"%row[3])
            if not currency:
                raise ValidationError("Currency  '%s' not found"%row[2])

            purchase_obj_update = purchase_default_value.copy()
            purchase_obj_update.update({
                'partner_id': partner[0].id or row[0],
                # 'move_name': self.seq_opt == 'f_sequence' and row[0] or '',
                'name': self.seq_opt == 'f_sequence' and row[0] or 'New',
                'currency_id': currency and currency.id or False,
                'state': self.state_stage == 'draft' and 'draft' or 'purchase',
                'date_order': dt,
            })

            purchase_obj = purchase_obj.new(purchase_obj_update)
            purchase_obj.onchange_partner_id()
            purchase_obj_update.update({'currency_id': purchase_obj.currency_id.id})
            line_v1 = purchase_line_obj.default_get(line_fields)
            line_vals = line_v1.copy()
            line_vals.update({'name': row[6], 'date_planned':datetime.datetime.now(),'product_id': product.id, 'product_qty': row[4] and int(row[4]) or 1,
                          'product_uom': product.uom_id.id, 'price_unit': row[7] and int(row[7]) or 1,'taxes_id': [(6, 0, tax_search.ids)]})
            print ("::::::::::::::::::::::::::::::::::::::::purchase::::::line::::::::::::::::",line_vals)
            l2 = [(0, 0, line_vals)]

            line_obj = purchase_line_obj.new(l2[0][2])
            l2[0][2].update({'name': line_obj.name,
                             # 'taxes_id': line_obj.taxes_id and line_obj.taxes_id.ids or False,
                             'taxes_id':  [(6, 0, line_obj.taxes_id and line_obj.taxes_id.ids or tax_search.ids)] or False,
                             })
            if purchase_result.get(row[0]):
                l1 = purchase_result[row[0]]['order_line']

                purchase_result[row[0]].update({'order_line': l1 + l2})
            if not purchase_result.get(row[0]):
                purchase_obj_update.update({'order_line': l2})
                purchase_result[row[0]] = purchase_obj_update


        for purchase_data in purchase_result.values():
            purchase_obj.create(purchase_data)
        return True

class Picking_wizard(models.TransientModel):
    _name = 'picking.wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")
    # seq_opt = fields.Selection([('f_sequence', 'File Sequence'), ('s_sequence', 'System Sequence')],string='Sequence Option')
    picking_type = fields.Many2one('stock.picking.type',string="Picking Type")
    source_loc = fields.Many2one('stock.location',string="Source Location Zone")
    destination_loc = fields.Many2one('stock.location',string="Destination Location Zone")

    @api.multi
    def Import_picking_order(self):

        partner_obj = self.env['res.partner']
        product_obj = self.env['product.product']
        picking_obj = self.env['stock.picking']
        picking_obj_fileds = picking_obj.fields_get()
        picking_default_value = picking_obj.default_get(picking_obj_fileds)
        picking_line_obj = self.env['stock.move']
        line_fields = picking_line_obj.fields_get()
        file_data = False

        if self.select_file and self.data_file and self.picking_type:
            if self.select_file == 'csv' :
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)),quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.select_file == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or picking type'))

        lines = []
        for each in file_data:
            partner = partner_obj.search([('name', 'like', each[1])])
            product = product_obj.search([('name', 'like', each[4])])
            stock_picking_vals = picking_default_value.copy()

            if not partner:
                raise ValidationError("Partner  '%s' not found"%each[1])
            if not product:
                raise ValidationError("Product  '%s' not found"%each[4])

            dt = datetime.datetime.strptime(each[3], "%d-%m-%Y")
            print ("::::::::::::::::::::::::::::::::::::::::::::::::::::::row[10]:::::::::::::", dt)
            print ("::::::::::::::::::::::::::::::::::::::::",stock_picking_vals)
            print (":::::::::::::product:::::::::::::::::::::::::::",product)
            lines = [(0, 0, {
                'product_id': product.id,
                'product_uom_id': 2,
                'product_uom_qty': each[5],
                'name': product.name,
                'product_uom': product.uom_id.id,
            })]
            stock_picking_vals.update({
                'partner_id': partner.id,
                'location_id': self.source_loc.id,
                'location_dest_id': self.destination_loc.id,
                'picking_type_id': self.picking_type.id,
                'move_type': 'direct',
                'origin': each[2],
                'scheduled_date': dt,
                'move_lines': lines
            })
            print ("::::::::::::::::::::::::::::::::created::::::::::::::::",self.env['stock.picking'].create(stock_picking_vals))

class Product_wizard(models.TransientModel):
    _name = 'product.wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")

    @api.multi
    def Import_product_order(self):
        product_main_obj = self.env['product.product']
        file_data = False

        if self.select_file and self.data_file:
            if self.select_file == 'csv':
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",
                                                      delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.select_file == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or picking type'))

        for row in file_data:

            uom_ids = self.env['product.uom'].search([('name', 'like', row[5])])
            uom_po_ids = self.env['product.uom'].search([('name', 'like', row[6])])
            print ("::::::::::::::::::::::::uom_ids::::",uom_po_ids)

            if not uom_ids:
                raise ValidationError("Uom ids  '%s' not found" % row[5])
            if not uom_po_ids:
                raise ValidationError("uom_po_ids  '%s' not found" % row[6])


            categ_id_ids = self.env['product.category'].search([('name','like',row[2])])
            if not categ_id_ids:
                raise ValidationError("categ_ids  '%s' not found" % row[2])

            print ("::::::::::::::::::::::product cat:::::::::::::::::::::::::::::::::::::::::",categ_id_ids)

            product_obj = self.env['product.product']
            product_fields = product_obj.fields_get()
            pro_def_val = product_obj.default_get(product_fields)
            new_pro_up = pro_def_val.copy()
            if row[4] == '':
                new_pro_up.update({
                    'name': row[0],
                    'default_code': row[1],
                    'type' : row[3],
                    'list_price': row[7],
                    'categ_id': categ_id_ids.id and categ_id_ids.id or "",
                    'uom_id' : uom_ids.id,
                    'uom_po_id' : uom_po_ids.id,
                    'weight' : row[9],
                    'volume' : row[10],
                    })
            elif row[4] != '':
                new_pro_up.update({
                    'name': row[0],
                    'default_code': row[1],
                    'type' : row[3],
                    'list_price': row[7],
                    'barcode' : row[4],
                    'categ_id': categ_id_ids.id and categ_id_ids.id or "",
                    'uom_id' : uom_ids.id,
                    'uom_po_id' : uom_po_ids.id,
                    'weight' : row[9],
                    'volume' : row[10],
                    })

            search_product = product_main_obj.search([('name','=',row[0])])
            print ("::::::::::::::::::::::search_product:::::::::::::::::::::::::::::::::::::::::", search_product)
            if search_product:
                product_created_id = search_product.write(new_pro_up)
                print ("::::::::::::::::::::::::::product_updated::::::::::::::::::::::::::::::::",product_created_id)
            else:
                product_created_id = product_main_obj.create(new_pro_up)
                print ("::::::::::::::::::::::::::product_create::::::::::::::::::::::::::::::::", product_created_id)
            if row[11] != '':    
                product = self.env['product.product'].search([('name', 'like', row[0])])
                self.stock_location = self.env.ref('stock.stock_location_stock')
                location_id = self.env['stock.location'].search([('name', 'like', row[11])])
                self.env['stock.quant']._update_available_quantity(product, self.stock_location, row[11])

class Partner_wizard(models.TransientModel):
    _name = 'partner.wizard'

    select_file = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select')
    # crt_upt_file = fields.Selection([('create', 'Create Product'), ('update', 'Update Product')], string='Import Type')
    data_file = fields.Binary(string="File")

    @api.multi
    def Import_partner(self):
        partner_obj = self.env['res.partner']
        if self.select_file and self.data_file:
            if self.select_file == 'csv':
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",
                                                      delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.select_file == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or picking type'))

        for row in file_data:
            search_partner = self.env['res.partner'].search([('name', '=', row[0]),('ref', '=', row[16])])
            search_parent_partner = self.env['res.partner'].search([('name', '=', row[2])])
            print ("::::::::::::::::::::::::::::::::::::::;search person:::::::::::::::::::::::::::::::::::::",search_partner)

            search_salesperson = self.env['res.users'].search([('name', '=', row[15])])

            search_cust_payment_term = self.env['account.payment.term'].search([('name', '=', row[17])])

            search_vendar_payment_term = self.env['account.payment.term'].search([('name', '=', row[18])])

            search_country = self.env['res.country'].search([('name', '=', row[8])])

            search_state = self.env['res.country.state'].search([('name', '=', row[6])])

            # if not search_partner:
            #     raise ValidationError("partner ids  '%s' not found" % row[2])

            if not search_salesperson:
                raise ValidationError("Salesperson ids  '%s' not found" % row[15])

            if not search_cust_payment_term:
                raise ValidationError("customer payment  '%s' not found" % row[17])

            if not search_vendar_payment_term:
                raise ValidationError("Vendar payment  '%s' not found" % row[18])

            if not search_country:
                raise ValidationError("Country  '%s' not found" % row[18])

            if not search_state:
                raise ValidationError("State  '%s' not found" % row[6])

            partner_fields = partner_obj.fields_get()
            partner_def_val = partner_obj.default_get(partner_fields)
            new_partner_val = partner_def_val.copy()
            new_partner_val.update({
                'name': row[0],
                'company_type': row[1],
                # 'parent_id': search_partner.id and search_partner.id or new_partnerr_id.id,
                'parent_id': search_parent_partner and search_parent_partner.id or '',
                'street': row[3],
                'street2': row[4],
                'city': row[5],
                'state': search_state.id and search_state.id or row[6],
                'zip': row[7],
                'country_id': search_country.id and search_country.id or row[8],
                'website': row[9],
                'phone': row[10],
                'mobile': row[11],
                'email': row[12],
                'customer': row[13],
                'supplier': row[14],
                'user_id': search_salesperson.id and search_salesperson.id or row[15],
                'ref': row[16],
                'property_payment_term_id': search_cust_payment_term.id and search_cust_payment_term.id or row[17],
                'property_supplier_payment_term_id': search_vendar_payment_term.id and search_vendar_payment_term.id or
                                                     row[18],
            })
            if search_partner:

                partner_created_id = search_partner.write(new_partner_val)
                print ("::::::::::::::::::::::::::update partner::::::::::::::::::::::::::::::::", partner_created_id)

            else:
                partner_created_id = partner_obj.create(new_partner_val)
                print ("::::::::::::::::::::::::::create partner::::::::::::::::::::::::::::::::", partner_created_id)

class Inventory_wizard(models.TransientModel):
    _name = 'inventory.wizard'

    inv_name = fields.Char(string='Inventory Name')
    loc_name = fields.Many2one('stock.location',string='Location')
    file_type = fields.Selection([('csv', 'CSV File'), ('xls', 'XLS File')], string='Select')
    imp_product_by = fields.Selection([('barcode', 'Barcode'), ('code', 'Code'), ('name', 'Name')],
                               string='Import Product By')
    ser_no_lot_expi = fields.Boolean(string="Import Serial/Lot number with Expiry Date")
    data_file = fields.Binary(string="File")

    @api.multi
    def Import_inventory(self):
        if self.file_type and self.data_file:
            if self.file_type == 'csv':
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.file_type == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or picking type'))


        product_obj = self.env['product.product']
        inventory_obj = self.env['stock.inventory']
        inventory_fields = inventory_obj.fields_get()
        inventory_def_val = inventory_obj.default_get(inventory_fields)
        new_inventory_val = inventory_def_val.copy()
        new_inventory_val.update({
            'name': self.inv_name,
            'state': 'confirm',
            'location_id': self.loc_name.id,
        })
        final_created_id = inventory_obj.create(new_inventory_val)
        for row in file_data:
            prod_lot_obj = self.env['stock.production.lot']
            prod_lot_fields = prod_lot_obj.fields_get()
            prod_lot_obj_def_val = prod_lot_obj.default_get(prod_lot_fields)
            new_inventory_line_val_ids = prod_lot_obj_def_val.copy()

            inventory_line_obj = self.env['stock.inventory.line']
            inventory_line_fields = inventory_line_obj.fields_get()
            inventory_line_def_val = inventory_line_obj.default_get(inventory_line_fields)
            new_inventory_line_val = inventory_line_def_val.copy()

            date = datetime.datetime.strptime(row[3], "%d-%m-%Y")
            stock_prod_lot_obj = self.env['stock.production.lot'].search([('name','=',int(row[2]))])
            print ("::::::::::::::::::::::::::::::::::::stock_prod_lot_obj:::::::::::::::::",stock_prod_lot_obj)
            print ("::::::::::::::::::::::::::::::::::::row[2]:::::::::::::::::",row[2])

            if self.imp_product_by == "code":
                pro_nm_bycode = product_obj.search([('default_code', '=', row[0])])
                new_inventory_line_val_ids.update({
                    'name': self.ser_no_lot_expi == True and int(row[2]) or '',
                    'product_id': pro_nm_bycode.id,
                    'life_date': self.ser_no_lot_expi == True and date or '',
                })
                new_lot_serial = prod_lot_obj.create(new_inventory_line_val_ids)
                new_inventory_line_val.update({
                    'inventory_id': final_created_id.id,
                    'product_id': pro_nm_bycode.id,
                    'product_qty': row[1],
                    'location_id': self.loc_name.id,
                    'prod_lot_id': stock_prod_lot_obj.id and stock_prod_lot_obj.id or new_lot_serial.id,
                })
                final_line = inventory_line_obj.create(new_inventory_line_val)
                print ("::::::::::::::::::::::lines:::::::::::::::::::", final_line)

            elif self.imp_product_by == "barcode":
                pro_nm_barcode = product_obj.search([('barcode', '=', int(row[0]))])
                new_inventory_line_val_ids.update({
                    'name': self.ser_no_lot_expi == True and int(row[2]) or '',
                    'product_id': pro_nm_barcode.id,
                    'life_date': self.ser_no_lot_expi == True and date or '',
                })
                new_lot_serial = prod_lot_obj.create(new_inventory_line_val_ids)
                new_inventory_line_val.update({
                    'inventory_id': final_created_id.id,
                    'product_id': pro_nm_barcode.id,
                    'product_qty': row[1],
                    'location_id': self.loc_name.id,
                    'prod_lot_id': stock_prod_lot_obj and stock_prod_lot_obj.id or new_lot_serial.id,
                })
                final_line = inventory_line_obj.create(new_inventory_line_val)
                print ("::::::::::::::::::::::lines:::::::::::::::::::", final_line)

            elif self.imp_product_by == "name":
                print (":::::::::::::::::::name::::::::::::::")
                pro_nm = product_obj.search([('name', 'like', row[0])])
                new_inventory_line_val_ids.update({
                    'name': self.ser_no_lot_expi == True and int(row[2]) or '',
                    'product_id': pro_nm.id,
                    'life_date': self.ser_no_lot_expi == True and date or ''})
                new_lot_serial = prod_lot_obj.create(new_inventory_line_val_ids)
                print ("::::::::::::::::::::::::::::::new_lot_serial:::::::::::::::::::::",new_lot_serial)
                print ("::::::::::::::::::::::::::::::stock_prod_lot_obj:::::::::::::::::::::",stock_prod_lot_obj)

                new_inventory_line_val.update({
                    'inventory_id': final_created_id.id,
                    'product_id': pro_nm.id,
                    'product_qty': row[1],
                    'location_id': self.loc_name.id,
                    'prod_lot_id': stock_prod_lot_obj and stock_prod_lot_obj.id or new_lot_serial.id,
                })
                final_line = inventory_line_obj.create(new_inventory_line_val)
                print ("::::::::::::::::::::::lines:::::::::::::::::::", final_line)
            else:
                raise exceptions.Warning(_('Please select product by'))

class Payment_wizard(models.TransientModel):
    _name = 'payment.wizard'

    payment_type = fields.Selection([('customer_py', 'Customer Payment'), ('supp_py', 'Supplier Payment')],string='Payment')
    data_file = fields.Binary(string="File")

    @api.multi
    def Import_payment(self,vals):

        if self.data_file == 'csv':
            csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",delimiter=",")
            csv_reader_data = iter(csv_reader_data)
            next(csv_reader_data)
            file_data = csv_reader_data
        else:
            file_datas = base64.decodestring(self.data_file)
            workbook = xlrd.open_workbook(file_contents=file_datas)
            sheet = workbook.sheet_by_index(0)
            result = []
            data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
            data.pop(0)
            file_data = data

        partner_obj = self.env['res.partner']
        account_obj = self.env['account.journal']


        for row in file_data:
            partner = partner_obj.search([('name', 'like', row[0])])
            account = account_obj.search([('name', 'like', row[2])])

            payment_vals = {
                'partner_type': self.payment_type == 'customer_py' and 'customer' or 'supplier',
                'partner_id': partner.id,
                'payment_date': datetime.datetime.now(),
                'journal_id': account.id,
                'amount': row[1],
                'communication': row[4],
                'payment_method_id': 2,
                'state': 'draft',
                'payment_type': 'inbound',
                }

            payment = self.env['account.payment'].create(payment_vals)

            print (":::::::::::::::::::::::pppppppppp:::::::::::::::::::::::::",payment)

class Journal_wizard(models.TransientModel):
    _name = 'journal.wizard'


    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")


    @api.multi
    def Import_journal(self):
        account_journal_browse_obj = self.env['account.move'].browse(self._context.get('active_ids'))
        file_data = False
        if self.select_file and self.data_file:
            if self.select_file == 'csv' :
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.select_file == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or seqeuance'))
        my_list = []
        for row in file_data:
            account_id_search = self.env['account.account'].search([('code', '=', int(row[8]))])
            partner_id_search = self.env['res.partner'].search([('name', '=', row[1])])
            currency__find = self.env['res.currency'].search([('name', '=', row[7])])
            search_analytic = self.env['account.analytic.account'].search([('name', '=', row[2])])
            dt = datetime.datetime.strptime(row[3], "%d-%m-%Y")
            account_line = {
                'name': row[0] and row[0] or '/',
                'account_id': account_id_search.id,
                'partner_id': partner_id_search.id,
                'analytic_account_id': search_analytic.id,
                'amount_currency': row[6],
                'date': dt,
                'move_id': account_journal_browse_obj.id,
                'company_currency_id': currency__find.id,
                'debit': int(row[4] or 0),
                'credit': int(row[5] or 0),
            }
            my_list.append((0,0,account_line))

        account_journal_browse_obj.write({'line_ids':my_list})

class Bank_account_wizard(models.TransientModel):
    _name = 'bank.wizard'

    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")

    @api.multi
    def Import_Bank_AC(self):
        account_journal_browse_obj = self.env['account.bank.statement'].browse(self._context.get('active_ids'))
        file_data = False
        if self.select_file and self.data_file:
            if self.select_file == 'csv' :
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)), quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.select_file == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or seqeuance'))
        my_list = []
        for row in file_data:
            partner_id_search = self.env['res.partner'].search([('name', '=', row[2])])
            dt = datetime.datetime.strptime(row[0], "%d-%m-%Y")
            account_line = {
                'name': row[3] and row[3] or '/',
                'partner_id': partner_id_search.id,
                'amount': row[4],
                'ref': row[1],
                'date': dt,
            }
            my_list.append((0,0,account_line))
        account_journal_browse_obj.write({'line_ids':my_list})

class Bom_wizard(models.TransientModel):
    _name = 'bom.wizard'

    select_file = fields.Selection([('csv', 'CSV File'),('xls', 'XLS File')], string='Select')
    data_file = fields.Binary(string="File")
    bom_type = fields.Selection([('mp', 'Manufacture Product'), ('kit', 'Kit')], string='Bom Type')

    @api.multi
    def Import_BOM(self):
        product_tem_obj = self.env['product.template']
        product_obj = self.env['product.product']

        mrp_result = {}
        mrp_obj = self.env['mrp.bom']
        mrp_obj_fileds = mrp_obj.fields_get()
        mrp_default_value = mrp_obj.default_get(mrp_obj_fileds)
        mrp_line_obj = self.env['mrp.bom.line']
        line_fields = mrp_line_obj.fields_get()
        file_data = False
        if self.select_file and self.data_file and self.bom_type:
            if self.select_file == 'csv' :
                csv_reader_data = pycompat.csv_reader(io.BytesIO(base64.decodestring(self.data_file)),quotechar=",",delimiter=",")
                csv_reader_data = iter(csv_reader_data)
                next(csv_reader_data)
                file_data = csv_reader_data
            elif self.select_file == 'xls':
                file_datas = base64.decodestring(self.data_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                result = []
                data = [[sheet.cell_value(r, c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                data.pop(0)
                file_data = data
        else:
            raise exceptions.Warning(_('Please select file and type of file or bom type'))

        for row in file_data:
            product_tem = product_tem_obj.search([('name', '=', row[0]),('default_code', '=', row[1])])
            product_rows = product_obj.search([('name', '=', row[3])])
            if not product_tem:
                raise ValidationError("Product  '%s' not found"%row[0])
            if not product_rows:
                raise ValidationError("Product  '%s' not found"%row[3])

            mrp_obj_update = mrp_default_value.copy()
            mrp_obj_update.update({
                'product_tmpl_id': product_tem.id,
                'product_qty': row[2],
                'product_uom_id': product_tem.uom_id.id,
                'type': self.bom_type == 'mp' and 'normal' or 'phantom',
                'code': row[1],

            })
            line_v1 = mrp_line_obj.default_get(line_fields)
            line_vals = line_v1.copy()
            line_vals.update({'product_id': product_rows.id, 'product_qty': row[4] and int(row[4]) or 1,
                          'product_uom_id': product_rows.uom_id.id})
            l2 = [(0, 0, line_vals)]
            if mrp_result.get(row[0]):
                l1 = mrp_result[row[0]]['bom_line_ids']
                mrp_result[row[0]].update({'bom_line_ids': l1 + l2})
            if not mrp_result.get(row[0]):
                mrp_obj_update.update({'bom_line_ids': l2})
                mrp_result[row[0]] = mrp_obj_update
        for mrp_data in mrp_result.values():
            mrp_gen = mrp_obj.create(mrp_data)
            print ("::::::::::::::::::mrp_gen::::::::::::::::",mrp_gen)
        return True



















