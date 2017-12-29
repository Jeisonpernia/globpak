# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import deque
import json

from odoo import http
from odoo.http import request
from odoo.tools import ustr
from odoo.tools.misc import xlwt

from datetime import date

class ExportReportXlsPurchaseExpenseSummary(http.Controller):

	@http.route('/web/export_xls/purchase_expense', type='http', auth="user")
	def export_xls(self, filename, title, company_id, date_from, date_to, journal_id, **kw):
		company = request.env['res.company'].search([('id', '=', company_id)])
		journal = request.env['account.journal'].search([('id', '=', journal_id)])
		account_ewt = request.env['account.account'].search([('name','=','Withholding Tax Expanded')], limit=1)
		account_invoice = request.env['account.invoice'].search([('journal_id.id', '=', journal_id),('state','in',('open','paid')),('date','>=',date_from),('date','<=',date_to)])
		account_expense = request.env['hr.expense.sheet'].search([('state','in',('post','paid')),('accounting_date','>=',date_from),('accounting_date','<=',date_to)])
		date_processed = date.today().strftime('%m-%d-%Y')
		user_id = request.env.user.name

		workbook = xlwt.Workbook()
		worksheet = workbook.add_sheet(title)

		# STYLES
		style_header_bold = xlwt.easyxf("font: bold on;font: name Calibri;align: wrap no")
		style_header_right = xlwt.easyxf("font: name Calibri;align: horiz right, wrap no")
		style_table_header_bold = xlwt.easyxf("font: bold on;font: name Calibri;align: horiz centre, vert centre, wrap on;borders: top thin, bottom thin, right thin;")
		style_table_row = xlwt.easyxf("font: name Calibri;align: horiz left, wrap no;borders: top thin, bottom thin, right thin;")
		style_table_row_amount = xlwt.easyxf("font: name Calibri;align: horiz right, wrap no;borders: top thin, bottom thin, right thin;", num_format_str="#,##0.00")
		style_table_total = xlwt.easyxf("pattern: pattern solid, fore_colour pale_blue;font: bold on;font: name Calibri;align: horiz left, wrap no;borders: top thin, bottom medium, right thin;")
		style_table_total_value = xlwt.easyxf("pattern: pattern solid, fore_colour pale_blue;font: bold on;font: name Calibri;align: horiz right, wrap no;borders: top thin, bottom medium, right thin;", num_format_str="#,##0.00")
		worksheet.col(0).width = 350*12
		worksheet.col(1).width = 350*12
		worksheet.col(2).width = 350*12
		worksheet.col(3).width = 500*12
		worksheet.col(4).width = 500*12
		worksheet.col(5).width = 350*12
		worksheet.col(6).width = 350*12
		worksheet.col(7).width = 350*12
		worksheet.col(8).width = 350*12
		worksheet.col(9).width = 350*12
		worksheet.col(10).width = 350*12
		worksheet.col(11).width = 350*12
		worksheet.col(12).width = 350*12
		worksheet.col(13).width = 350*12
		worksheet.col(14).width = 350*12
		worksheet.col(15).width = 350*12
		worksheet.col(16).width = 350*12
		worksheet.col(17).width = 350*12
		worksheet.col(18).width = 350*12
		worksheet.col(19).width = 350*12
		worksheet.col(20).width = 350*12
		worksheet.col(21).width = 350*12
		worksheet.col(22).width = 350*12
		worksheet.col(23).width = 350*12
		worksheet.col(24).width = 350*12
		worksheet.col(25).width = 350*12
		worksheet.col(26).width = 350*12
		worksheet.col(27).width = 350*12
		worksheet.col(28).width = 350*12
		worksheet.col(29).width = 350*12
		worksheet.col(30).width = 350*12

		# TEMPLATE HEADERS
		worksheet.write(0, 0, company.name, style_header_bold) # Company Name
		worksheet.write(1, 0, '%s %s %s %s %s %s'%(company.street,company.street2,company.city,company.state_id.name,company.zip,company.country_id.name), style_header_bold) # Company Address
		worksheet.write(2, 0, company.vat, style_header_bold) # Company TIN

		worksheet.write(4, 0, title, style_header_bold) # Report Title
		worksheet.write(5, 0, 'Period Covered: %s - %s'%(date_from,date_to), style_header_bold) # Report Date

		# TABLE HEADER
		worksheet.write_merge(7, 8, 0, 0, 'DATE', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 7, 1, 2, 'REFERENCE', style_table_header_bold) # HEADER
		worksheet.write(8, 1, 'AP ENTRY NO.', style_table_header_bold) # HEADER
		worksheet.write(8, 2, 'CV ENTRY NO.', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 3, 3, 'NAME OF SUPPLIER', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 4, 4, 'REGISTERED ADDRESS', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 5, 5, 'TIN', style_table_header_bold) # HEADER

		worksheet.write_merge(7, 7, 6, 8, 'REFERENCE DEETAILS', style_table_header_bold) # HEADER
		worksheet.write(8, 6, 'SALES INVOICE', style_table_header_bold) # HEADER
		worksheet.write(8, 7, 'OFFICIAL RECEIPT', style_table_header_bold) # HEADER
		worksheet.write(8, 8, 'OTHERS', style_table_header_bold) # HEADER

		worksheet.write_merge(7, 8, 9, 9, 'GROSS AMOUNT', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 10, 10, 'INPUT TAX 12%', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 11, 11, 'NET OF VAT', style_table_header_bold) # HEADER

		worksheet.write_merge(7, 8, 12, 12, 'PURCHASE OF CAPITAL GOODS > 1M', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 13, 13, 'PURCHASE OF CAPITAL GOODS < 1M', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 14, 14, 'PURCHASES OTHER THAN CAPITAL GOODS', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 15, 15, 'DOMESTIC PURCHASE OF SERVICES', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 16, 16, 'PURCHASES NOT QUALITFIED TO INPUT TAX', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 17, 17, 'IMPORTATION OF GOODS OTHER THAN CAPITAL GOODS', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 18, 18, 'SERVICES RENDERED BY NON RESIDENTS', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 19, 19, 'OTHERS', style_table_header_bold) # HEADER

		worksheet.write_merge(7, 8, 20, 20, 'ACCOUNT TITLE', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 21, 21, 'PARTICULARS', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 22, 22, 'EXPENSE AMOUNT', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 7, 23, 26, 'EXPANDED WITHHOLDING TAX', style_table_header_bold) # HEADER
		worksheet.write(8, 23, 'TAX BASE', style_table_header_bold) # HEADER
		worksheet.write(8, 24, 'ATC', style_table_header_bold) # HEADER
		worksheet.write(8, 25, 'EWT RATE', style_table_header_bold) # HEADER
		worksheet.write(8, 26, 'EWT EXPANDED AMOUNT', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 27, 27, 'EXPENSES NOT SUBJECTED TO EWT', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 28, 28, 'ALLOWED INPUT TAX', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 29, 29, 'DISALLOWED INPUT TAX', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 30, 30, 'DEFERRED', style_table_header_bold) # HEADER

		# TABLE ROW LINES
		# table_row_start = 9
		report_lines = []
		row_count = 9
		transaction_count = 0
		total_amount_goods_gt_1m = 0
		total_amount_goods_lt_1m = 0

		# Purchase
		for account in account_invoice:
			amount_goods_gt_1m = 0
			amount_goods_lt_1m = 0
			domestic_amount_services = 0
			foreign_amount_services = 0
			expense_non_ewt = 0
			expense_input_tax = 0
			expense_non_input_tax = 0

			ewt_tax_base = 0
			ewt_atc = ''
			ewt_rate = 0
			ewt_tax_amount = 0
			input_tax_amount = 0

			if account.amount_goods > 1000000:
				amount_goods_gt_1m = account.amount_goods
			else:
				amount_goods_lt_1m = account.amount_goods

			if account.po_type == 'import':
				foreign_amount_services =  account.amount_services
			else:
				domestic_amount_services = account.amount_services

			has_ewt = False
			for tax in account.tax_line_ids:
				if tax.account_id.id == account_ewt.id:
					has_ewt = True
					ewt_tax_base = tax.base
					ewt_atc = tax.tax_id.ewt_structure_id.name
					ewt_rate = tax.tax_id.amount
					ewt_tax_amount = tax.amount_total
				else:
					if tax.amount == 12.00:
						input_tax_amount = tax.amount_total

			# EXPENSESE NOT SUBJECTED TO EWT
			if has_ewt == False:
				expense_non_ewt = account.amount_untaxed

			if input_tax_amount == 0:
				expense_non_input_tax += account.amount_untaxed
			else:
				expense_input_tax += account.amount_untaxed

			report_lines.append({
				'date': account.date, #0
				'ap_entry': account.move_id.name, #1
				'cv_entry': '', #2
				'supplier_name': account.partner_id.name, #3
				'suppier_address': '%s %s %s %s %s %s'%(account.partner_id.street or '',
					account.partner_id.street2 or '',
					account.partner_id.city or '',
					account.partner_id.state_id.name or '',
					account.partner_id.zip or '',
					account.partner_id.country_id.name or ''), #4
				'tin': account.partner_id.vat or '', #5
				'si_ref': '', #6
				'or_ref': '', #7
				'other_ref': '', #8
				'gross_amount': account.amount_total, #9
				'input_tax_amount': input_tax_amount, #10
				'net_vat_amount': account.vat_sales, #11
				'purchase_goods_gt_1m_amount': amount_goods_gt_1m, #12
				'purchase_goods_lt_1m_amount': amount_goods_lt_1m, #13
				'purchase_goods_other_amount': 0, #14
				'purchase_service_domestic_amount': domestic_amount_services, #15
				'purchase_non_vat_amount': account.vat_exempt_sales, #16
				'purchase_goods_import_amount': 0, #17
				'purcahse_service_import_amount': foreign_amount_services, #18
				'other_amount': 0, #19
				'account_title': '', #20
				'particulars': account.x_description or '', #21
				'expense_amount': account.amount_total, #22
				'ewt_tax_base': ewt_tax_base, #23
				'ewt_atc': ewt_atc or '', #24
				'ewt_rate': ewt_rate, #25
				'ewt_tax_amount': ewt_tax_amount, #26
				'expense_non_ewt': expense_non_ewt, #27
				'expense_input_tax': expense_input_tax, #28
				'expense_non_input_tax': expense_non_input_tax, #29
				'deferred': 0, #30
			})

			# row_count +=1
			# transaction_count +=1

		# Expense
		for sheet in account_expense:
			for expense in sheet.expense_line_ids:
				for line in expense.line_ids:
					amount_goods_gt_1m = 0
					amount_goods_lt_1m = 0
					expense_non_ewt = 0
					expense_input_tax = 0
					expense_non_input_tax = 0

					ewt_tax_base = 0
					ewt_atc = ''
					ewt_rate = 0
					ewt_tax_amount = 0
					input_tax_amount = 0

					amount_services = 0
					amount_goods = 0
					if line.product_id.type == 'service':
						amount_services += line.untaxed_amount

					if line.product_id.type == 'consu' or line.product_id.type == 'product':
						amount_goods += line.untaxed_amount

					if amount_goods > 1000000:
						amount_goods_gt_1m = amount_goods
					else:
						amount_goods_lt_1m = amount_goods

					has_ewt = False
					for tax in line.tax_ids:
						base = line.price_unit * line.quantity
						tax_amount = (base * tax.amount) / 100
						if tax.account_id.id == account_ewt.id:
							has_ewt = True
							ewt_tax_base = base
							ewt_atc = tax.ewt_structure_id.name
							ewt_rate = tax.amount
							ewt_tax_amount = tax_amount
						else:
							if tax.amount == 12.00:
								input_tax_amount = tax_amount


					if has_ewt == False:
						expense_non_ewt = line.untaxed_amount

					if input_tax_amount == 0:
						expense_non_input_tax += line.untaxed_amount
					else:
						expense_input_tax += line.untaxed_amount

					report_lines.append({
						'date': sheet.accounting_date, #0
						'ap_entry': sheet.account_move_id.name, #1
						'cv_entry': '', #2
						'supplier_name': line.partner_id.name, #3
						'suppier_address': '%s %s %s %s %s %s'%(line.partner_id.street or '',
							line.partner_id.street2 or '',
							line.partner_id.city or '',
							line.partner_id.state_id.name or '',
							line.partner_id.zip or '',
							line.partner_id.country_id.name or ''), #4
						'tin': line.partner_id.vat or '', #5
						'si_ref': '', #6
						'or_ref': '', #7
						'other_ref': '', #8
						'gross_amount': line.total_amount, #9
						'input_tax_amount': input_tax_amount, #10
						'net_vat_amount': line.vat_sales, #11
						'purchase_goods_gt_1m_amount': amount_goods_gt_1m, #12
						'purchase_goods_lt_1m_amount': amount_goods_lt_1m, #13
						'purchase_goods_other_amount': 0, #14
						'purchase_service_domestic_amount': amount_services, #15
						'purchase_non_vat_amount': line.vat_exempt_sales, #16
						'purchase_goods_import_amount': 0, #17
						'purcahse_service_import_amount': 0, #18
						'other_amount': 0, #19
						'account_title': line.account_id.name, #20
						'particulars': line.name or '', #21
						'expense_amount': line.total_amount, #22
						'ewt_tax_base': ewt_tax_base, #23
						'ewt_atc': ewt_atc or '', #24
						'ewt_rate': ewt_rate, #25
						'ewt_tax_amount': ewt_tax_amount, #26
						'expense_non_ewt': expense_non_ewt, #27
						'expense_input_tax': expense_input_tax, #28
						'expense_non_input_tax': expense_non_input_tax, #29
						'deferred': 0, #30
					})


		for line in report_lines:
			worksheet.write(row_count, 0, line.get('date'), style_table_row)
			worksheet.write(row_count, 1, line.get('ap_entry'), style_table_row)
			worksheet.write(row_count, 2, line.get('cv_entry'), style_table_row) 
			worksheet.write(row_count, 3, line.get('supplier_name'), style_table_row)
			worksheet.write(row_count, 4, line.get('suppier_address'), style_table_row)
			worksheet.write(row_count, 5, line.get('tin'), style_table_row)

			worksheet.write(row_count, 6, line.get('si_ref'), style_table_row)
			worksheet.write(row_count, 7, line.get('or_ref'), style_table_row)
			worksheet.write(row_count, 8, line.get('other_ref'), style_table_row)

			worksheet.write(row_count, 9, line.get('gross_amount'), style_table_row_amount)
			worksheet.write(row_count, 10, line.get('input_tax_amount'), style_table_row_amount) 
			worksheet.write(row_count, 11, line.get('net_vat_amount'), style_table_row_amount)

			worksheet.write(row_count, 12, line.get('purchase_goods_gt_1m_amount'), style_table_row_amount) 
			worksheet.write(row_count, 13, line.get('purchase_goods_lt_1m_amount'), style_table_row_amount)
			worksheet.write(row_count, 14, line.get('purchase_goods_other_amount'), style_table_row_amount)
			worksheet.write(row_count, 15, line.get('purchase_service_domestic_amount'), style_table_row_amount) 
			worksheet.write(row_count, 16, line.get('purchase_non_vat_amount'), style_table_row_amount)
			worksheet.write(row_count, 17, line.get('purchase_goods_import_amount'), style_table_row_amount)
			worksheet.write(row_count, 18, line.get('purcahse_service_import_amount'), style_table_row_amount)
			worksheet.write(row_count, 19, line.get('other_amount'), style_table_row_amount)

			worksheet.write(row_count, 20, line.get('account_title'), style_table_row)
			worksheet.write(row_count, 21, line.get('particulars'), style_table_row)
			worksheet.write(row_count, 22, line.get('expense_amount'), style_table_row_amount)
			worksheet.write(row_count, 23, line.get('ewt_tax_base'), style_table_row_amount)
			worksheet.write(row_count, 24, line.get('ewt_atc'), style_table_row)
			worksheet.write(row_count, 25, line.get('ewt_rate'), style_table_row_amount)
			worksheet.write(row_count, 26, line.get('ewt_tax_amount'), style_table_row_amount)
			worksheet.write(row_count, 27, line.get('expense_non_ewt'), style_table_row_amount)
			worksheet.write(row_count, 28, line.get('expense_input_tax'), style_table_row_amount)
			worksheet.write(row_count, 29, line.get('expense_non_input_tax'), style_table_row_amount)
			worksheet.write(row_count, 30, line.get('deferred'), style_table_row_amount)

			row_count +=1
			transaction_count +=1

		table_total_start = row_count

		# TABLE TOTALS
		worksheet.write(table_total_start, 0,  '', style_table_total)
		worksheet.write(table_total_start, 1,  '', style_table_total)
		worksheet.write(table_total_start, 2,  '', style_table_total)
		worksheet.write(table_total_start, 3,  '', style_table_total)
		worksheet.write(table_total_start, 4,  '', style_table_total)
		worksheet.write(table_total_start, 5,  '', style_table_total)
		worksheet.write(table_total_start, 6,  '', style_table_total)
		worksheet.write(table_total_start, 7,  '', style_table_total)
		worksheet.write(table_total_start, 8, '', style_table_total_value)
		worksheet.write(table_total_start, 9, '', style_table_total_value)
		worksheet.write(table_total_start, 10, '', style_table_total_value)
		worksheet.write(table_total_start, 11, '', style_table_total_value)
		worksheet.write(table_total_start, 12, '', style_table_total_value)
		worksheet.write(table_total_start, 13, '', style_table_total_value)
		worksheet.write(table_total_start, 14, '', style_table_total_value)
		worksheet.write(table_total_start, 15, '', style_table_total_value)
		worksheet.write(table_total_start, 16, '', style_table_total_value)
		worksheet.write(table_total_start, 17, '', style_table_total_value)
		worksheet.write(table_total_start, 18, '', style_table_total_value)
		worksheet.write(table_total_start, 19, '', style_table_total_value)
		worksheet.write(table_total_start, 20, '', style_table_total_value)
		worksheet.write(table_total_start, 21, '', style_table_total_value)
		worksheet.write(table_total_start, 22, '', style_table_total_value)
		worksheet.write(table_total_start, 23, '', style_table_total_value)
		worksheet.write(table_total_start, 24, '', style_table_total_value)
		worksheet.write(table_total_start, 25, '', style_table_total_value)
		worksheet.write(table_total_start, 26, '', style_table_total_value)
		worksheet.write(table_total_start, 27, '', style_table_total_value)
		worksheet.write(table_total_start, 28, '', style_table_total_value)
		worksheet.write(table_total_start, 29, '', style_table_total_value)
		worksheet.write(table_total_start, 30, '', style_table_total_value)

		response = request.make_response(None,
			headers=[('Content-Type', 'application/vnd.ms-excel'),
					('Content-Disposition', 'attachment; filename=%s;'%(filename)
					)])

		workbook.save(response.stream)

		return response
