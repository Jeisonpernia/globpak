# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from collections import deque
import json

from odoo import http
from odoo.http import request
from odoo.tools import ustr
from odoo.tools.misc import xlwt

from datetime import date

class ExportReportXlsAccountAlphalistPayee(http.Controller):

    @http.route('/web/export_xls/account_alphalist_payee', type='http', auth="user")
    def export_xls(self, filename, title, company_id, date_from, date_to, account_id, **kw):
        company = request.env['res.company'].search([('id', '=', company_id)])
        account = request.env['account.account'].search([('id', '=', account_id)])
        account_move_lines = request.env['account.move.line'].sudo().search([('account_id.id', '=', account_id)],order='partner_id asc')
        # account_move_lines = request.env['account.move.line'].sudo().search([])
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
        worksheet.col(0).width = 250*12
        worksheet.col(1).width = 500*12
        worksheet.col(2).width = 750*12
        worksheet.col(3).width = 750*12
        worksheet.col(4).width = 300*12
        worksheet.col(5).width = 800*12
        worksheet.col(6).width = 350*12
        worksheet.col(7).width = 300*12
        worksheet.col(8).width = 350*12

        # TEMPLATE HEADERS
        worksheet.write(0, 0, 'BIR FORM 1601E - SCHEDULE I', style_header_bold) # BIR FORM INFO
        worksheet.write(1, 0, title, style_header_bold) # TITLE
        worksheet.write(2, 0, 'FOR THE MONTH OF %s'%(date_to), style_header_bold) # Report Date

        worksheet.write(3, 0, account_id, style_header_bold) # Report Date
        # worksheet.write(4, 0, account_move_lines, style_header_bold) # Report Date

        worksheet.write(5, 0, 'TIN: %s'%(company.vat), style_header_bold) # Company Name
        worksheet.write(6, 0, "WITHHOLDING AGENT'S NAME: %s"%(company.name), style_header_bold) # Company TIN

        # TABLE HEADER
        worksheet.write(9, 0, 'SEQ NO', style_table_header_bold) # HEADER
        worksheet.write(9, 1, 'TAXPAYER IDENTIIFICATION NUMBER', style_table_header_bold) # HEADER
        worksheet.write(9, 2, 'CORPORATION (Registered Name)', style_table_header_bold) # HEADER
        worksheet.write(9, 3, 'INDIVIDUAL (Last Name, First Name, Middle Name)', style_table_header_bold) # HEADER
        worksheet.write(9, 4, 'ATC CODE', style_table_header_bold) # HEADER
        worksheet.write(9, 5, 'NATURE OF PAYMENT', style_table_header_bold) # HEADER

        worksheet.write(9, 6, 'AMOUNT OF INCOME PAYMENT', style_table_header_bold) # HEADER
        worksheet.write(9, 7, 'TAX RATE', style_table_header_bold) # HEADER
        worksheet.write(9, 8, 'AMOUNT OF TAX WITHHELD', style_table_header_bold) # HEADER

        # TABLE ROW LINES
        row_count = 10
        seq_count = 1
        for account in account_move_lines:
            worksheet.write(row_count, 0, seq_count, style_table_row) 
            worksheet.write(row_count, 1, account.partner_id.x_tin, style_table_row)
            worksheet.write(row_count, 2, account.partner_id.name, style_table_row)
            worksheet.write(row_count, 3, '', style_table_row)
            worksheet.write(row_count, 4, account.tax_line_id.ewt_structure_id.name or '', style_table_row)
            worksheet.write(row_count, 5, account.tax_line_id.ewt_structure_id.description or '', style_table_row)
            
            worksheet.write(row_count, 6, '-', style_table_row)
            worksheet.write(row_count, 7, account.tax_line_id.amount, style_table_row)
            worksheet.write(row_count, 8, account.debit, style_table_row_amount)

            row_count +=1
            seq_count +=1

        table_total_start = row_count

        end_report = table_total_start + 2


        # TABLE TOTALS
        worksheet.write_merge(table_total_start, table_total_start, 0, 7, 'GRAND TOTAL', style_table_total)
        worksheet.write(table_total_start, 8, '-', style_table_total_value)
        worksheet.write(end_report, 0, 'END OF REPORT', style_end_report)

        response = request.make_response(None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=%s;'%(filename)
                    )])

        workbook.save(response.stream)

        return response
