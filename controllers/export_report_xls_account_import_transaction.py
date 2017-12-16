# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import deque
import json

from odoo import http
from odoo.http import request
from odoo.tools import ustr
from odoo.tools.misc import xlwt

from datetime import date

class ExportReportXlsAccountImportTransaction(http.Controller):

    @http.route('/web/export_xls/import_transaction', type='http', auth="user")
    def export_xls(self, filename, title, subtitle, company_id, date_from, date_to, journal_id, **kw):
        company = request.env['res.company'].search([('id', '=', company_id)])
        journal = request.env['account.journal'].search([('id', '=', journal_id)])
        account_invoice_purchase = request.env['account.invoice'].search([('journal_id.id', '=', journal_id),('po_type','=','import'),('type','=','in_invoice'),('state','in',('open','paid')),('date','>=',date_from),('date','<=',date_to)],order='date asc')
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
        style_end_report = xlwt.easyxf("font: bold on;font: name Calibri;align: horiz left, wrap no;")
        worksheet.col(0).width = 500*12
        worksheet.col(1).width = 500*12
        worksheet.col(2).width = 500*12
        worksheet.col(3).width = 500*12
        worksheet.col(4).width = 500*12
        worksheet.col(5).width = 500*12
        worksheet.col(6).width = 500*12
        worksheet.col(7).width = 500*12
        worksheet.col(8).width = 500*12
        worksheet.col(9).width = 500*12
        worksheet.col(10).width = 500*12
        worksheet.col(11).width = 500*12
        worksheet.col(12).width = 500*12
        worksheet.col(13).width = 500*12
        worksheet.col(14).width = 500*12

        # TEMPLATE HEADERS
        worksheet.write(0, 0, title, style_header_bold) # TITLE
        worksheet.write(1, 0, subtitle, style_header_bold) # SUBTITLE

        worksheet.write(3, 0, 'TIN: %s'%(company.vat), style_header_bold) # Company TIN
        worksheet.write(4, 0, "OWNER'S NAME: %s"%(company.name), style_header_bold) # Company Name
        # worksheet.write(5, 0, "OWNER'S TRADE NAME: %s"%('GLOBPAK'), style_header_bold) # Company Trade Name
        worksheet.write(5, 0, "OWNER's ADDRESS %s %s %s %s %s %s"%(company.street,company.street2,company.city,company.state_id.name,company.zip,company.country_id.name), style_header_bold) # Company Address

        # TABLE HEADER
        worksheet.write(7, 0, 'TAXABLE MONTH', style_table_header_bold) # HEADER
        worksheet.write(7, 1, 'IMPORT ENTRY NUMBER', style_table_header_bold) # HEADER
        worksheet.write(7, 2, 'ASSESSMENT/RELEASE DATE', style_table_header_bold) # HEADER
        worksheet.write(7, 3, 'REGISTERED NAME', style_table_header_bold) # HEADER
        worksheet.write(7, 4, "IMPORTATION DATE", style_table_header_bold) # HEADER
        
        worksheet.write(7, 5, 'COUNTRY OF ORIGIN', style_table_header_bold) # HEADER
        worksheet.write(7, 6, 'AMOUNT OF TOTAL LANDED COST', style_table_header_bold) # HEADER
        worksheet.write(7, 7, 'AMOUNT OF TOTAL DUTIABLE VALUE', style_table_header_bold) # HEADER
        worksheet.write(7, 8, 'AMOUNT OF CHARGES BEFORE RELEASE FROM CUSTOM', style_table_header_bold) # HEADER

        worksheet.write(7, 9, 'AMOUNT OF TAXABLE IMPORTS', style_table_header_bold) # HEADER
        worksheet.write(7, 10, 'AMOUNT OF EXEMPT IMPORTS', style_table_header_bold) # HEADER
        worksheet.write(7, 11, 'AMOUNT OF VAT', style_table_header_bold) # HEADER
        worksheet.write(7, 12, 'OR NUMBER', style_table_header_bold) # HEADER
        worksheet.write(7, 13, 'DATE OF VAT PAYMENT', style_table_header_bold) # HEADER

        # TABLE ROW LINES
        # table_row_start = 9
        row_count = 8
        transaction_count = 0
        total_amount_untaxed = 0
        total_vat_exempt_sales = 0
        total_zero_rated_sales = 0
        total_vat_sales = 0
        total_amount_tax = 0
        total_landed_cost = 0
        total_dutiable_amount = 0
        total_charges_custom = 0
        for account in account_invoice_purchase:
            worksheet.write(row_count, 0, account.date, style_table_row) 
            worksheet.write(row_count, 1, account.import_entry_no or '', style_table_row)
            worksheet.write(row_count, 2, account.assessment_date or '', style_table_row)
            worksheet.write(row_count, 3, account.partner_id.name, style_table_row)
            worksheet.write(row_count, 4, account.importation_date or '', style_table_row)
            
            worksheet.write(row_count, 5, account.x_origin.name, style_table_row_amount)
            worksheet.write(row_count, 6, account.total_landed_cost, style_table_row_amount)
            worksheet.write(row_count, 7, account.total_landed_cost, style_table_row_amount)
            worksheet.write(row_count, 8, account.total_charges_custom, style_table_row_amount)

            worksheet.write(row_count, 9, account.vat_sales, style_table_row_amount)
            worksheet.write(row_count, 10, account.vat_exempt_sales, style_table_row_amount)
            worksheet.write(row_count, 11, account.amount_tax, style_table_row_amount)
            worksheet.write(row_count, 12, '', style_table_row_amount)
            worksheet.write(row_count, 13, '', style_table_row_amount)

            row_count +=1
            transaction_count +=1

            total_amount_untaxed += account.amount_untaxed
            total_vat_exempt_sales += account.vat_exempt_sales
            total_zero_rated_sales +=  account.zero_rated_sales
            total_vat_sales += account.vat_sales
            total_amount_tax += account.amount_tax
            total_landed_cost += account.total_landed_cost
            total_dutiable_amount += account.total_landed_cost
            total_charges_custom += account.total_charges_custom

        table_total_start = row_count

        end_report = table_total_start + 2

        # TABLE TOTALS
        worksheet.write_merge(table_total_start, table_total_start, 0, 5, 'GRAND TOTAL', style_table_total)
        worksheet.write(table_total_start, 6, total_landed_cost, style_table_total_value)
        worksheet.write(table_total_start, 7, total_dutiable_amount, style_table_total_value)
        worksheet.write(table_total_start, 8, total_charges_custom, style_table_total_value)
        worksheet.write(table_total_start, 9, total_vat_sales, style_table_total_value)
        worksheet.write(table_total_start, 10, total_vat_exempt_sales, style_table_total_value)
        worksheet.write(table_total_start, 11, total_amount_tax, style_table_total_value)
        worksheet.write(table_total_start, 12, '-', style_table_total_value)
        worksheet.write(table_total_start, 13, '-', style_table_total_value)
        worksheet.write(end_report, 0, 'END OF REPORT', style_end_report)
        

        response = request.make_response(None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=%s;'%(filename)
                    )])

        workbook.save(response.stream)

        return response
