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

class ExportReportXlsAccountEwtDeduction(http.Controller):

    @http.route('/web/export_xls/ewt_deduction', type='http', auth="user")
    def export_xls(self, filename, title, company_id, date_from, date_to, account_id, **kw):
        company = request.env['res.company'].search([('id', '=', company_id)])
        # journal = request.env['account.journal'].search([('id', '=', journal_id)])
        account_ewt = request.env['account.account'].search([('name','=','Withholding Tax Expanded')], limit=1)
        # account_vendor_bill = request.env['account.invoice'].search([('journal_id.id', '=', journal_id),('state','in',('open','paid')),('date','>=',date_from),('date','<=',date_to)])
        account_vendor_bill = request.env['account.move.line'].search([('account_id.id', '=', account_id),('date','>=',date_from),('date','<=',date_to)])
        date_processed = date.today().strftime('%m-%d-%Y')
        from_report_month = datetime.strptime(date_from, '%Y-%m-%d')
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
        worksheet.col(7).width = 350*12
        worksheet.col(6).width = 350*12
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

        # TEMPLATE HEADERS
        worksheet.write(0, 0, company.name, style_header_bold) # Company Name
        worksheet.write(1, 0, '%s %s %s %s %s %s'%(company.street,company.street2,company.city,company.state_id.name,company.zip,company.country_id.name), style_header_bold) # Company Address
        worksheet.write(2, 0, 'TIN %s'%(company.vat), style_header_bold) # Company TIN

        worksheet.write(4, 0, title, style_header_bold) # Report Title
        worksheet.write(5, 0, '%s to %s'%(from_report_month.strftime('%B %d, %Y'),to_report_month.strftime('%B %d, %Y')), style_header_bold) # Report Date

        # TABLE HEADER
        worksheet.write_merge(7, 8, 0, 0, 'REFERENCE DATE', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 1, 1, 'VOUCHER DATE', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 2, 2, 'JOURNAL TYPE', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 3, 3, 'REFERENCE NO.', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 4, 4, 'SUPPLIER NAME', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 5, 5, 'REGISTERED ADDRESS', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 6, 6, 'TIN', style_table_header_bold) # HEADER

        worksheet.write_merge(7, 7, 7, 8, 'SOURCE DOCUMENT', style_table_header_bold) # HEADER
        worksheet.write(8, 7, 'TYPE', style_table_header_bold) # HEADER
        worksheet.write(8, 8, 'NUMBER', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 9, 9, 'GROSS AMOUNT', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 10, 10, 'NON-VAT / EXEMPT', style_table_header_bold) # HEADER

        worksheet.write_merge(7, 8, 11, 11, 'NET OF VAT', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 12, 12, 'INPUT TAX (12%)', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 13, 13, 'INPUT TAX ALLOWED', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 14, 14, 'ACCOUNT TITLE', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 15, 15, 'PARTICULARS', style_table_header_bold) # HEADER

        worksheet.write_merge(7, 8, 16, 16, 'EXPENSE AMOUNT', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 7, 17, 19, 'EXPANDED WITHOLDING TAX', style_table_header_bold) # HEADER
        worksheet.write(8, 17, 'ATC', style_table_header_bold) # HEADER
        worksheet.write(8, 18, 'EWT RATE', style_table_header_bold) # HEADER
        worksheet.write(8, 19, 'AMOUNT', style_table_header_bold) # HEADER
        worksheet.write_merge(7, 8, 20, 20, 'EWT ABSORBED BY COMPANY', style_table_header_bold) # HEADER

        # TABLE ROW LINES
        # table_row_start = 9
        row_count = 9
        transaction_count = 0
        
        for account in account_vendor_bill:
            source_type = ''
            source_num = ''
            amount_income = 0
            amount_tax = 0
            account_title = ''
            input_tax_amount = 0

            # GET SOURCES
            if account.invoice_id:
                source_num = account.invoice_id.number
                if account.invoice_id.type == 'out_invoice':
                    source_type = 'Customer Invoice'
                elif account.invoice_id.type == 'in_invoice':
                    source_type = 'Vendor Bill'
                elif account.invoice_id.type == 'out_refund':
                    source_type = 'Customer Credit Note'
                else:
                    source_type = 'Vendor Credit Note'
            else:
                # GET PAYMENT
                # VENDOR PAYMENT
                if 'SUPP.OUT' in account.name:
                    payment = request.env['account.payment'].search([('name','=', account.name)], limit=1)
                    if payment:
                        source_type = 'O.R'
                        source_num = payment.name
                if 'CUST.IN' in account.name:
                    payment = request.env['account.payment'].search([('name','=', account.name)], limit=1)
                    if payment:
                        source_type = 'O.R'
                        source_num = payment.name
                        if payment.collection_receipt_id:
                            source_type = 'C.R'
                        if payment.acknowledgement_receipt_id:
                            source_type = 'C.R'
                        # if not payment.collection_receipt_id and not payment.acknowledgement_receipt_id or payment.collection_receipt_id and payment.acknowledgement_receipt_id:
                        #     source_type = 'O.R'

            # GET TAXES AMOUNT
            for tax in account.invoice_id.tax_line_ids:
                if tax.account_id == account.account_id:
                    amount_income = tax.base
                    amount_tax = tax.amount_total
                else:
                    # if tax.amount == 12:
                    input_tax_amount = tax.amount_total

            if amount_tax <= 0:
                if account.debit > 0:
                    amount_tax = account.debit
                else:
                    amount_tax = account.credit

            if account.move_id:
                for move in account.move_id.line_ids:
                    for tax in move.tax_ids:
                        if tax.account_id.id == account_ewt.id:
                            account_title = move.account_id.name


            worksheet.write(row_count, 0, '', style_table_row)
            worksheet.write(row_count, 1, account.date, style_table_row) 
            worksheet.write(row_count, 2, account.move_id.journal_id.name, style_table_row)
            worksheet.write(row_count, 3, account.move_id.name, style_table_row)
            worksheet.write(row_count, 4, account.partner_id.name, style_table_row)
            worksheet.write(row_count, 5, '%s %s %s %s %s %s'%(account.partner_id.street or '',account.partner_id.street2 or '',account.partner_id.city or '',account.partner_id.state_id.name or '',account.partner_id.zip or '',account.partner_id.country_id.name or ''), style_table_row)
            worksheet.write(row_count, 6, account.partner_id.vat or '', style_table_row)

            worksheet.write(row_count, 7, source_type, style_table_row)
            worksheet.write(row_count, 8, source_num, style_table_row)
            worksheet.write(row_count, 9, account.invoice_id.amount_total, style_table_row_amount)
            worksheet.write(row_count, 10, account.invoice_id.vat_exempt_sales, style_table_row_amount) 

            worksheet.write(row_count, 11, account.invoice_id.vat_sales, style_table_row_amount)
            worksheet.write(row_count, 12, input_tax_amount, style_table_row_amount) 
            worksheet.write(row_count, 13, '', style_table_row)
            worksheet.write(row_count, 14, account_title, style_table_row)
            worksheet.write(row_count, 15, account.invoice_id.x_description or '', style_table_row_amount) 

            worksheet.write(row_count, 16, account.invoice_id.amount_untaxed, style_table_row_amount)
            worksheet.write(row_count, 17, account.tax_line_id.ewt_structure_id.name  or '', style_table_row)
            worksheet.write(row_count, 18, account.tax_line_id.amount, style_table_row_amount)
            worksheet.write(row_count, 19, amount_tax, style_table_row_amount)
            worksheet.write(row_count, 20, '', style_table_row)

            row_count +=1
            transaction_count +=1

        table_total_start = row_count


        # TABLE TOTALS
        # worksheet.write_merge(table_total_start, table_total_start, 0, 7, 'TOTAL', style_table_total)
        # worksheet.write(table_total_start, 8, '-', style_table_total_value)
        # worksheet.write(table_total_start, 9, '', style_table_total_value)
        # worksheet.write(table_total_start, 10, '-', style_table_total_value)
        # worksheet.write(table_total_start, 11, '-', style_table_total_value)
        # worksheet.write(table_total_start, 12, '', style_table_total_value)
        # worksheet.write(table_total_start, 13, '', style_table_total_value)
        # worksheet.write(table_total_start, 14, '-', style_table_total_value)
        # worksheet.write(table_total_start, 15, '', style_table_total_value)
        # worksheet.write(table_total_start, 16, '', style_table_total_value)
        # worksheet.write(table_total_start, 17, '-', style_table_total_value)
        # worksheet.write(table_total_start, 18, '-', style_table_total_value)

        worksheet.write(0, 20, 'No. of Transaction: %s'%(transaction_count), style_header_right)
        worksheet.write(1, 20, 'Date Processed: %s'%(date_processed), style_header_right)
        worksheet.write(2, 20, 'Processed By: %s'%(user_id), style_header_right)
        # worksheet.write(3, 18, '%s'%(account_invoice_payable), style_header_right)

        response = request.make_response(None,
            headers=[('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition', 'attachment; filename=%s;'%(filename)
                    )])

        workbook.save(response.stream)

        return response
