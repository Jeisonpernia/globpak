# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import deque
import json

from odoo import http
from odoo.http import request
from odoo.tools import ustr
from odoo.tools.misc import xlwt

from datetime import date

class ExportReportXlsAccountPurchaseTransaction(http.Controller):

    @http.route('/web/export_xls/purchase_transaction', type='http', auth="user")
    def export_xls(self, filename, title, subtitle, company_id, date_from, date_to, account_id, **kw):
        company = request.env['res.company'].search([('id', '=', company_id)])
        account = request.env['account.account'].search([('id', '=', account_id)])
        # account_move_ids = request.env['account.move.line'].search([('account_id', '=', account_id)])
        account_invoice_sales = request.env['account.invoice'].search([('type', '=', 'in_invoice'),('state','=','paid'),('date','>=',date_from),('date','<=',date_to)],order='date asc')
        date_processed = date.today().strftime('%m-%d-%Y')
        user_id = request.env.user.name

        workbook = xlwt.Workbook()
        worksheet = workbook.add_sheet(title)

        # STYLES
        style_header_bold = xlwt.easyxf("font: bold on;font: name Calibri;align: wrap no")
        style_header_right = xlwt.easyxf("font: name Calibri;align: horiz right, wrap no")
        style_table_header_bold = xlwt.easyxf("font: bold on;font: name Calibri;align: horiz centre, vert centre, wrap on;borders: top thin, bottom thin, right thin;")
        style_table_row = xlwt.easyxf("font: name Calibri;align: horiz left, wrap no;borders: top thin, bottom thin, right thin;")
        style_table_row_amount = xlwt.easyxf("font: name Calibri;align: horiz right, wrap no;borders: top thin, bottom thin, right thin;")
        style_table_total = xlwt.easyxf("pattern: pattern solid, fore_colour pale_blue;font: bold on;font: name Calibri;align: horiz left, wrap no;borders: top thin, bottom medium, right thin;")
        style_table_total_value = xlwt.easyxf("pattern: pattern solid, fore_colour pale_blue;font: bold on;font: name Calibri;align: horiz right, wrap no;borders: top thin, bottom medium, right thin;")
        style_end_report = xlwt.easyxf("font: bold on;font: name Calibri;align: horiz left, wrap no;")
        worksheet.col(0).width = 500*12
        worksheet.col(1).width = 500*12
        worksheet.col(2).width = 500*12
        worksheet.col(3).width = 500*12
        worksheet.col(4).width = 500*12
        worksheet.col(5).width = 500*12
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
        worksheet.write(5, 0, "OWNER'S TRADE NAME: %s"%('GLOBPAK'), style_header_bold) # Company Trade Name
        worksheet.write(6, 0, "OWNER's ADDRESS %s %s %s %s %s %s"%(company.street,company.street2,company.city,company.state_id.name,company.zip,company.country_id.name), style_header_bold) # Company Address

        # TABLE HEADER
        worksheet.write(8, 0, 'TAXABLE MONTH', style_table_header_bold) # HEADER
        worksheet.write(8, 1, 'TAXPAYER IDENTIFICATION NUMBER', style_table_header_bold) # HEADER
        worksheet.write(8, 2, 'REGISTERED NAME', style_table_header_bold) # HEADER
        worksheet.write(8, 3, 'NAME OF SUPPLIER (Last Name, First Name, Middle Name)', style_table_header_bold) # HEADER
        worksheet.write(8, 4, "SUPPLIER'S ADDRESS", style_table_header_bold) # HEADER
        
        worksheet.write(8, 5, 'AMOUNT OF GROSS PURCHASE', style_table_header_bold) # HEADER
        worksheet.write(8, 6, 'AMOUNT OF EXEMPT PURCHASE', style_table_header_bold) # HEADER
        worksheet.write(8, 7, 'AMOUNT OF ZERO RATED PURCHASE', style_table_header_bold) # HEADER
        worksheet.write(8, 8, 'AMOUNT OF TAXABLE PURCHASE', style_table_header_bold) # HEADER

        worksheet.write(8, 9, 'AMOUNT OF PURCHASE OF SERVICES', style_table_header_bold) # HEADER
        worksheet.write(8, 10, 'AMOUNT OF PURCHASE OF CAPITAL', style_table_header_bold) # HEADER
        worksheet.write(8, 11, 'AMOUNT OF PURCHASE OF GOODS', style_table_header_bold) # HEADER
        worksheet.write(8, 12, 'AMOUNT OF INPUT TAX', style_table_header_bold) # HEADER
        worksheet.write(8, 13, 'AMOUNT OF GROSS TAXABLE PURCHASE', style_table_header_bold) # HEADER

        # TABLE ROW LINES
        # table_row_start = 9
        row_count = 9
        transaction_count = 0
        total_amount_untaxed = 0
        total_vat_exempt_sales = 0
        total_zero_rated_sales = 0
        total_vat_sales = 0
        total_amount_tax = 0
        for account in account_invoice_sales:
            worksheet.write(row_count, 0, account.date, style_table_row) 
            worksheet.write(row_count, 1, account.partner_id.x_tin or '', style_table_row)
            worksheet.write(row_count, 2, account.partner_id.name, style_table_row)
            worksheet.write(row_count, 3, '', style_table_row)
            worksheet.write(row_count, 4, '%s %s %s %s %s %s'%(account.partner_id.street or '',account.partner_id.street2 or '',account.partner_id.city or '',account.partner_id.state_id.name or '',account.partner_id.zip or '',account.partner_id.country_id.name or ''), style_table_row)
            
            worksheet.write(row_count, 5, account.amount_untaxed, style_table_row_amount)
            worksheet.write(row_count, 6, account.vat_exempt_sales, style_table_row_amount)
            worksheet.write(row_count, 7, account.zero_rated_sales or '', style_table_row_amount)
            worksheet.write(row_count, 8, account.vat_sales, style_table_row_amount)

            worksheet.write(row_count, 9, '-', style_table_row_amount)
            worksheet.write(row_count, 10, '-', style_table_row_amount)
            worksheet.write(row_count, 11, '-', style_table_row_amount)
            worksheet.write(row_count, 12, account.amount_tax, style_table_row_amount)
            worksheet.write(row_count, 13, '-', style_table_row_amount)

            row_count +=1
            transaction_count +=1

            total_amount_untaxed += account.amount_untaxed
            total_vat_exempt_sales += account.vat_exempt_sales
            total_zero_rated_sales +=  account.zero_rated_sales
            total_vat_sales += account.vat_sales
            total_amount_tax += account.amount_tax

        table_total_start = row_count

        end_report = table_total_start + 2

        # TABLE TOTALS
        worksheet.write_merge(table_total_start, table_total_start, 0, 4, 'GRAND TOTAL', style_table_total)
        worksheet.write(table_total_start, 5, total_amount_untaxed, style_table_total_value)
        worksheet.write(table_total_start, 6, total_vat_exempt_sales, style_table_total_value)
        worksheet.write(table_total_start, 7, total_zero_rated_sales, style_table_total_value)
        worksheet.write(table_total_start, 8, total_vat_sales, style_table_total_value)
        worksheet.write(table_total_start, 9, '-', style_table_total_value)
        worksheet.write(table_total_start, 10, '-', style_table_total_value)
        worksheet.write(table_total_start, 11, '-', style_table_total_value)
        worksheet.write(table_total_start, 12, total_amount_tax, style_table_total_value)
        worksheet.write(table_total_start, 13, '-', style_table_total_value)
        worksheet.write(end_report, 0, 'END OF REPORT', style_end_report)
        

        response = request.make_response(None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=%s;'%(filename)
                    )])

        workbook.save(response.stream)

        return response
