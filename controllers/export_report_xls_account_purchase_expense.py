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
        # account_ewt = request.env['account.account'].search([('name','=','Withholding Tax Expanded')], limit=1)
        account_invoice = request.env['account.invoice'].search([('journal_id.id', '=', journal_id),('state','in',('open','paid')),('date','>=',date_from),('date','<=',date_to)])
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
        worksheet.write(0, 0, company.name, style_header_bold) # Company Name
        worksheet.write(1, 0, '%s %s %s %s %s %s'%(company.street,company.street2,company.city,company.state_id.name,company.zip,company.country_id.name), style_header_bold) # Company Address
        worksheet.write(2, 0, company.vat, style_header_bold) # Company TIN

        worksheet.write(4, 0, title, style_header_bold) # Report Title
        worksheet.write(5, 0, '%s to %s'%(date_from,date_to), style_header_bold) # Report Date

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
        worksheet.write_merge(7, 8, 18, 18, 'SERVICES RENDERED BY NOW RESIDENTS', style_table_header_bold) # HEADER
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
        row_count = 9
        transaction_count = 0
        for account in account_invoice:
            worksheet.write(row_count, 0, '', style_table_row)
            worksheet.write(row_count, 1, account.date, style_table_row) 
            worksheet.write(row_count, 2, account.partner_id.name, style_table_row)
            worksheet.write(row_count, 3, '%s %s %s %s %s %s'%(account.partner_id.street or '',account.partner_id.street2 or '',account.partner_id.city or '',account.partner_id.state_id.name or '',account.partner_id.zip or '',account.partner_id.country_id.name or ''), style_table_row)
            worksheet.write(row_count, 4, account.partner_id.x_tin, style_table_row)
            worksheet.write(row_count, 5, account.number, style_table_row)

            worksheet.write(row_count, 6, '', style_table_row)
            worksheet.write(row_count, 7, '', style_table_row)
            worksheet.write(row_count, 8, '', style_table_row)

            worksheet.write(row_count, 9, account.amount_untaxed, style_table_row_amount)
            worksheet.write(row_count, 10, '', style_table_row_amount) 
            worksheet.write(row_count, 11, '', style_table_row)

            worksheet.write(row_count, 12, '', style_table_row_amount) 
            worksheet.write(row_count, 13, account.vat_sales, style_table_row)
            worksheet.write(row_count, 14, account.zero_rated_sales, style_table_row)
            worksheet.write(row_count, 15, account.vat_exempt_sales, style_table_row_amount) 
            worksheet.write(row_count, 16, account.vat_sales, style_table_row)
            worksheet.write(row_count, 17, account.amount_tax, style_table_row)
            worksheet.write(row_count, 18, account.amount_total, style_table_row)
            worksheet.write(row_count, 19, '', style_table_row)

            worksheet.write(row_count, 20, '', style_table_row)
            worksheet.write(row_count, 21, '', style_table_row)
            worksheet.write(row_count, 22, '', style_table_row)
            worksheet.write(row_count, 23, '', style_table_row)
            worksheet.write(row_count, 24, '', style_table_row)
            worksheet.write(row_count, 25, '', style_table_row)
            worksheet.write(row_count, 26, '', style_table_row)
            worksheet.write(row_count, 27, '', style_table_row)
            worksheet.write(row_count, 28, '', style_table_row)
            worksheet.write(row_count, 29, '', style_table_row)
            worksheet.write(row_count, 30, '', style_table_row)

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
