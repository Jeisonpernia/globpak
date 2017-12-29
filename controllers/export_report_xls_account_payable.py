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

class ExportReportXlsAccountPayable(http.Controller):

    @http.route('/web/export_xls/account_payable', type='http', auth="user")
    def export_xls(self, filename, title, company_id, date_from, date_to, account_id, **kw):
        company = request.env['res.company'].search([('id', '=', company_id)])
        account_ewt = request.env['account.account'].search([('name','=','Withholding Tax Expanded')], limit=1)
        # account = request.env['account.account'].search([('id', '=', account_id)])
        # accounts_payable = request.env['account.move.line'].search([('account_id', '=', account_id)])
        account_invoice_payable = request.env['account.invoice'].search([('type', '=', 'in_invoice'),('state','in',('open','paid')),('date','>=',date_from),('date','<=',date_to)])
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

        # TEMPLATE HEADERS
        worksheet.write(0, 0, company.name, style_header_bold) # Company Name
        worksheet.write(1, 0, '%s %s %s %s %s %s'%(company.street,company.street2,company.city,company.state_id.name,company.zip,company.country_id.name), style_header_bold) # Company Address
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
        worksheet.write_merge(7, 8, 14, 14, 'AP AMOUNT', style_table_header_bold) # HEADER

        worksheet.write_merge(7, 7, 15, 17, 'EXPANDED WITHOLDING TAX', style_table_header_bold) # HEADER
        worksheet.write(8, 15, 'ATC', style_table_header_bold) # HEADER
        worksheet.write(8, 16, 'EWT RATE', style_table_header_bold) # HEADER
        worksheet.write(8, 17, 'AMOUNT', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 18, 18, 'EWT ABSORBED BY COMPANY', style_table_header_bold) # HEADER

        # TABLE ROW LINES
        # table_row_start = 9
        row_count = 9
        transaction_count = 0
        total_gross_amount = 0
        total_non_vat_amount = 0
        total_net_vat_amount = 0
        total_input_tax_amount = 0
        total_ap_amount = 0
        total_ewt_tax_amount = 0
        for account in account_invoice_payable:
            ewt_tax_base = 0
            ewt_atc = ''
            ewt_rate = 0
            ewt_tax_amount = 0
            input_tax_amount = 0

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

            worksheet.write(row_count, 0, account.date, style_table_row) 
            worksheet.write(row_count, 1, account.journal_id.name, style_table_row)
            worksheet.write(row_count, 2, account.number, style_table_row)
            worksheet.write(row_count, 3, account.partner_id.name, style_table_row)
            worksheet.write(row_count, 4, '%s %s %s %s %s %s'%(account.partner_id.street or '',account.partner_id.street2 or '',account.partner_id.city or '',account.partner_id.state_id.name or '',account.partner_id.zip or '',account.partner_id.country_id.name or ''), style_table_row)
            worksheet.write(row_count, 5, account.partner_id.vat or '', style_table_row)
            
            worksheet.write(row_count, 6, '', style_table_row)
            worksheet.write(row_count, 7, account.origin or '', style_table_row)
            worksheet.write(row_count, 8, account.amount_total, style_table_row_amount)
            worksheet.write(row_count, 9, account.vat_exempt_sales, style_table_row_amount) 

            worksheet.write(row_count, 10, account.vat_sales, style_table_row_amount)
            worksheet.write(row_count, 11, input_tax_amount, style_table_row_amount) 
            worksheet.write(row_count, 12, '', style_table_row_amount)
            worksheet.write(row_count, 13, account.x_description or '', style_table_row)
            worksheet.write(row_count, 14, account.amount_total, style_table_row_amount) 

            worksheet.write(row_count, 15, ewt_atc or '', style_table_row)
            worksheet.write(row_count, 16, ewt_rate, style_table_row_amount)
            worksheet.write(row_count, 17, ewt_tax_amount, style_table_row_amount)
            worksheet.write(row_count, 18, '', style_table_row_amount)

            row_count +=1
            transaction_count +=1
            total_gross_amount += account.amount_total
            total_non_vat_amount += account.vat_exempt_sales
            total_net_vat_amount += account.vat_sales
            total_input_tax_amount += input_tax_amount
            total_ap_amount +=  account.amount_total
            total_ewt_tax_amount += ewt_tax_amount

        table_total_start = row_count


        # TABLE TOTALS
        worksheet.write_merge(table_total_start, table_total_start, 0, 7, 'TOTAL', style_table_total)
        worksheet.write(table_total_start, 8, total_gross_amount, style_table_total_value)
        worksheet.write(table_total_start, 9, total_non_vat_amount, style_table_total_value)
        worksheet.write(table_total_start, 10, total_net_vat_amount, style_table_total_value)
        worksheet.write(table_total_start, 11, total_input_tax_amount, style_table_total_value)
        worksheet.write(table_total_start, 12, '', style_table_total_value)
        worksheet.write(table_total_start, 13, '', style_table_total_value)
        worksheet.write(table_total_start, 14, total_ap_amount, style_table_total_value)
        worksheet.write(table_total_start, 15, '', style_table_total_value)
        worksheet.write(table_total_start, 16, '', style_table_total_value)
        worksheet.write(table_total_start, 17, total_ewt_tax_amount, style_table_total_value)
        worksheet.write(table_total_start, 18, '', style_table_total_value)

        worksheet.write(0, 18, 'No. of Transaction: %s'%(transaction_count), style_header_right)
        worksheet.write(1, 18, 'Date Processed: %s'%(date_processed), style_header_right)
        worksheet.write(2, 18, 'Processed By: %s'%(user_id), style_header_right)
        # worksheet.write(3, 18, '%s'%(account_invoice_payable), style_header_right)

        response = request.make_response(None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=%s;'%(filename)
                    )])

        workbook.save(response.stream)

        return response
