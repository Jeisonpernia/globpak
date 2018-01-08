# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import deque
import json

from odoo import http
from odoo.http import request
from odoo.tools import ustr
from odoo.tools.misc import xlwt

from datetime import datetime
from datetime import date

class ExportReportXlsAssetSummary(http.Controller):

	@http.route('/web/export_xls/asset_summary', type='http', auth="user")
	def export_xls(self, filename, title, company_id, date_from, date_to, **kw):
		company = request.env['res.company'].search([('id', '=', company_id)])
		# account_ewt = request.env['account.account'].search([('name','=','Withholding Tax Expanded')], limit=1)
		
		account_type = request.env['account.account.type'].search([('name', '=', 'Fixed Assets')])
		account_ids = request.env['account.account'].search([('user_type_id', '=', account_type.id)])
		account_asset = request.env['account.asset.asset'].search([('state','!=','draft')])
		
		date_processed = date.today().strftime('%m-%d-%Y')
		to_report_month = datetime.strptime(date_to, '%Y-%m-%d')
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
		worksheet.col(31).width = 350*12
		worksheet.col(32).width = 350*12
		worksheet.col(33).width = 350*12
		worksheet.col(34).width = 350*12
		worksheet.col(35).width = 350*12
		worksheet.col(36).width = 350*12
		worksheet.col(37).width = 350*12
		worksheet.col(38).width = 350*12


		# TEMPLATE HEADERS
		worksheet.write(0, 0, company.name, style_header_bold) # Company Name
		worksheet.write(1, 0, '%s %s %s %s %s %s'%(company.street or '',company.street2 or '',company.city or '',company.state_id.name or '',company.zip or '',company.country_id.name or ''), style_header_bold) # Company Address
		worksheet.write(2, 0, company.vat, style_header_bold) # Company TIN

		worksheet.write(4, 0, title, style_header_bold) # Report Title
		worksheet.write(5, 0, 'As of %s'%(to_report_month.strftime('%B %d, %Y')), style_header_bold) # Report Date

		# TABLE HEADER
		worksheet.write_merge(7, 8, 0, 0, 'REFERENCE DATE', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 1, 1, 'JOURNAL TYPE', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 2, 2, 'REFERENCE NO.', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 3, 3, 'SUPPLIER NAME', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 4, 4, 'REGISTERED ADDRESS', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 5, 5, 'TIN', style_table_header_bold) # HEADER

		worksheet.write_merge(7, 7, 6, 7, 'SOURCE DOCUMENT', style_table_header_bold) # HEADER
		worksheet.write(8, 6, 'TYPE', style_table_header_bold) # HEADER
		worksheet.write(8, 7, 'NUMBER', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 8, 8, 'GROSS AMOUNT', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 9, 9, 'NON-VAT / EXEMPT', style_table_header_bold) # HEADER

		worksheet.write_merge(7, 8, 10, 10, 'NET OF VAT', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 11, 11, 'INPUT TAX (12%)', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 12, 12, 'INPUT TAX ALLOWED', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 13, 13, 'PARTICULARS', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 14, 14, 'ASSET AMOUNT', style_table_header_bold) # HEADER

		worksheet.write_merge(7, 7, 15, 17, 'EXPANDED WITHOLDING TAX', style_table_header_bold) # HEADER
		worksheet.write(8, 15, 'ATC', style_table_header_bold) # HEADER
		worksheet.write(8, 16, 'EWT RATE', style_table_header_bold) # HEADER
		worksheet.write(8, 17, 'AMOUNT', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 18, 18, 'EWT ABSORBED BY COMPANY', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 19, 19, 'ESTIMATED LIFE', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 20, 20, 'MONTHLY DEPRECIATION', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 21, 21, 'JAN', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 22, 22, 'FEB', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 23, 23, 'MAR', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 24, 24, 'APR', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 25, 25, 'MAY', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 26, 26, 'JUN', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 27, 27, 'JUL', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 28, 28, 'AUG', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 29, 29, 'SEP', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 30, 30, 'OCT', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 31, 31, 'NOV', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 32, 32, 'DEC', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 33, 33, 'TOTAL', style_table_header_bold) # HEADER

		worksheet.write_merge(7, 7, 34, 36, 'ACCUMULATED DEPRECIATION', style_table_header_bold) # HEADER
		worksheet.write(8, 34, 'BEGINNING', style_table_header_bold) # HEADER
		worksheet.write(8, 35, 'CURRENT', style_table_header_bold) # HEADER
		worksheet.write(8, 36, 'TOTAL', style_table_header_bold) # HEADER

		worksheet.write_merge(7, 8, 37, 37, 'BOOK VALUE', style_table_header_bold) # HEADER
		worksheet.write_merge(7, 8, 38, 38, 'REMARKS', style_table_header_bold) # HEADER


		# TABLE ROW LINES
		# table_row_start = 9
		row_count = 9
		transaction_count = 0
		# total_gross_amount = 0
		# total_non_vat_amount = 0
		# total_net_vat_amount = 0
		# total_input_tax_amount = 0
		# total_ap_amount = 0
		# total_ewt_tax_amount = 0

		for account in account_asset:
			source_type = ''
			source_no = ''

			if account.invoice_id:
				source_type = 'Vendor Bill'
				source_no = account.invoice_id.name

			ewt_tax_base = 0
			ewt_atc = ''
			ewt_rate = 0
			ewt_tax_amount = 0
			input_tax_amount = 0

			estimated_life = 0
			if account.category_id.method_number and account.category_id.method_period:
				account.method_number * account.method_period

			monthly_value = 0
			beginning_value = 0
			current_value = 0
			total_value = 0
			jan_value = 0
			feb_value = 0
			mar_value = 0
			apr_value = 0 
			may_value = 0
			jun_value = 0
			jul_value = 0
			aug_value = 0
			sep_value = 0
			oct_value = 0
			nov_value = 0
			dec_value = 0

			for line in account.depreciation_line_ids:
				month_today = date.today().strftime('%m')
				
				if line.sequence == 1:
					monthly_value = line.amount
					beginning_value = line.depreciated_value

				if month_today == '01':
					jan_value += line.amount

				if month_today == '02':
					feb_value += line.amount

				if month_today == '03':
					mar_value += line.amount

				if month_today == '04':
					apr_value += line.amount

				if month_today == '05':
					may_value += line.amount

				if month_today == '06':
					jun_value += line.amount

				if month_today == '07':
					jul_value += line.amount

				if month_today == '08':
					aug_value += line.amount

				if month_today == '09':
					sep_value += line.amount

				if month_today == '10':
					oct_value += line.amount
				
				if month_today == '11':
					nov += line.amount

				if month_today == '12':
					dec_value += line.amount

			worksheet.write(row_count, 0, account.date, style_table_row) 
			worksheet.write(row_count, 1, account.category_id.journal_id.name, style_table_row)
			worksheet.write(row_count, 2, '', style_table_row)
			worksheet.write(row_count, 3, account.partner_id.name or '', style_table_row)
			worksheet.write(row_count, 4, '%s %s %s %s %s %s'%(account.partner_id.street or '',account.partner_id.street2 or '',account.partner_id.city or '',account.partner_id.state_id.name or '',account.partner_id.zip or '',account.partner_id.country_id.name or ''), style_table_row)
			worksheet.write(row_count, 5, account.partner_id.vat or '', style_table_row)
				
			worksheet.write(row_count, 6, source_type, style_table_row)
			worksheet.write(row_count, 7, source_no, style_table_row)
			worksheet.write(row_count, 8, account.value, style_table_row_amount)
			worksheet.write(row_count, 9, '', style_table_row_amount) 

			worksheet.write(row_count, 10, '', style_table_row_amount)
			worksheet.write(row_count, 11, input_tax_amount, style_table_row_amount) 
			worksheet.write(row_count, 12, '', style_table_row_amount)
			worksheet.write(row_count, 13, '', style_table_row)
			worksheet.write(row_count, 14, account.value, style_table_row_amount) 

			worksheet.write(row_count, 15, ewt_atc or '', style_table_row)
			worksheet.write(row_count, 16, ewt_rate, style_table_row_amount)
			worksheet.write(row_count, 17, ewt_tax_amount, style_table_row_amount)
			worksheet.write(row_count, 18, '', style_table_row_amount)

			worksheet.write(row_count, 19, estimated_life, style_table_row_amount)
			worksheet.write(row_count, 20, monthly_value, style_table_row_amount)

			worksheet.write(row_count, 21, jan_value, style_table_row_amount)
			worksheet.write(row_count, 22, feb_value, style_table_row_amount)
			worksheet.write(row_count, 23, mar_value, style_table_row_amount)
			worksheet.write(row_count, 24, apr_value, style_table_row_amount)
			worksheet.write(row_count, 25, mar_value, style_table_row_amount)
			worksheet.write(row_count, 26, jun_value, style_table_row_amount)
			worksheet.write(row_count, 27, jul_value, style_table_row_amount)
			worksheet.write(row_count, 28, aug_value, style_table_row_amount)
			worksheet.write(row_count, 29, sep_value, style_table_row_amount)
			worksheet.write(row_count, 30, oct_value, style_table_row_amount)
			worksheet.write(row_count, 31, nov_value, style_table_row_amount)
			worksheet.write(row_count, 32, dec_value, style_table_row_amount)

			worksheet.write(row_count, 33, account.value_residual, style_table_row_amount)

			worksheet.write(row_count, 34, beginning_value, style_table_row_amount)
			worksheet.write(row_count, 35, current_value, style_table_row_amount)
			worksheet.write(row_count, 36, total_value, style_table_row_amount)

			worksheet.write(row_count, 37, total_value, style_table_row_amount)
			worksheet.write(row_count, 38, '', style_table_row_amount)

			row_count +=1
			transaction_count +=1
			# total_gross_amount += account.amount_total
			# total_non_vat_amount += account.vat_exempt_sales
			# total_net_vat_amount += account.vat_sales
			# total_input_tax_amount += input_tax_amount
			# total_ap_amount +=  account.amount_total
			# total_ewt_tax_amount += ewt_tax_amount

		table_total_start = row_count

		# for account_id in account_ids:
		# accounts_asset = request.env['account.move.line'].search([('account_id', '=', account_id.id)])
		# for account in accounts_asset:
		#   ewt_tax_base = 0
		#   ewt_atc = ''
		#   ewt_rate = 0
		#   ewt_tax_amount = 0
		#   input_tax_amount = 0

			# has_ewt = False
			# for tax in account.tax_line_ids:
			#     if tax.account_id.id == account_ewt.id:
			#         has_ewt = True
			#         ewt_tax_base = tax.base
			#         ewt_atc = tax.tax_id.ewt_structure_id.name
			#         ewt_rate = tax.tax_id.amount
			#         ewt_tax_amount = tax.amount_total
			#     else:
			#         if tax.amount == 12.00:
			#             input_tax_amount = tax.amount_total

		#   worksheet.write(row_count, 0, account.date, style_table_row) 
		#   worksheet.write(row_count, 1, account.journal_id.name, style_table_row)
		#   worksheet.write(row_count, 2, account.name, style_table_row)
		#   worksheet.write(row_count, 3, account.partner_id.name, style_table_row)
		#   worksheet.write(row_count, 4, '%s %s %s %s %s %s'%(account.partner_id.street or '',account.partner_id.street2 or '',account.partner_id.city or '',account.partner_id.state_id.name or '',account.partner_id.zip or '',account.partner_id.country_id.name or ''), style_table_row)
		#   worksheet.write(row_count, 5, account.partner_id.vat or '', style_table_row)
				
		#   worksheet.write(row_count, 6, '', style_table_row)
		#   worksheet.write(row_count, 7, account.origin or '', style_table_row)
		#   worksheet.write(row_count, 8, account.amount_total, style_table_row_amount)
		#   worksheet.write(row_count, 9, account.vat_exempt_sales, style_table_row_amount) 

		#   worksheet.write(row_count, 10, account.vat_sales, style_table_row_amount)
		#   worksheet.write(row_count, 11, input_tax_amount, style_table_row_amount) 
		#   worksheet.write(row_count, 12, '', style_table_row_amount)
		#   worksheet.write(row_count, 13, account.x_description or '', style_table_row)
		#   worksheet.write(row_count, 14, account.amount_total, style_table_row_amount) 

		#   worksheet.write(row_count, 15, ewt_atc or '', style_table_row)
		#   worksheet.write(row_count, 16, ewt_rate, style_table_row_amount)
		#   worksheet.write(row_count, 17, ewt_tax_amount, style_table_row_amount)
		#   worksheet.write(row_count, 18, '', style_table_row_amount)

		#   row_count +=1
		#   transaction_count +=1
		#   total_gross_amount += account.amount_total
		#   total_non_vat_amount += account.vat_exempt_sales
		#   total_net_vat_amount += account.vat_sales
		#   total_input_tax_amount += input_tax_amount
		#   total_ap_amount +=  account.amount_total
		#   total_ewt_tax_amount += ewt_tax_amount

		# table_total_start = row_count


		# TABLE TOTALS
		worksheet.write_merge(table_total_start, table_total_start, 0, 7, 'TOTAL', style_table_total)
		worksheet.write(table_total_start, 8, '-', style_table_total_value)
		worksheet.write(table_total_start, 9, '-', style_table_total_value)
		worksheet.write(table_total_start, 10, '-', style_table_total_value)
		worksheet.write(table_total_start, 11, '-', style_table_total_value)
		worksheet.write(table_total_start, 12, '', style_table_total_value)
		worksheet.write(table_total_start, 13, '', style_table_total_value)
		worksheet.write(table_total_start, 14, '-', style_table_total_value)
		worksheet.write(table_total_start, 15, '', style_table_total_value)
		worksheet.write(table_total_start, 16, '', style_table_total_value)
		worksheet.write(table_total_start, 17, '-', style_table_total_value)
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
		worksheet.write(table_total_start, 31, '', style_table_total_value)
		worksheet.write(table_total_start, 32, '', style_table_total_value)
		worksheet.write(table_total_start, 33, '', style_table_total_value)
		worksheet.write(table_total_start, 34, '', style_table_total_value)
		worksheet.write(table_total_start, 35, '', style_table_total_value)
		worksheet.write(table_total_start, 36, '', style_table_total_value)
		worksheet.write(table_total_start, 37, '', style_table_total_value)
		worksheet.write(table_total_start, 38, '', style_table_total_value)

		# worksheet.write(0, 18, 'No. of Transaction: %s'%(transaction_count), style_header_right)
		# worksheet.write(1, 18, 'Date Processed: %s'%(date_processed), style_header_right)
		# worksheet.write(2, 18, 'Processed By: %s'%(user_id), style_header_right)

		response = request.make_response(None,
			headers=[('Content-Type', 'application/vnd.ms-excel'),
					('Content-Disposition', 'attachment; filename=%s;'%(filename)
					)])

		workbook.save(response.stream)

		return response