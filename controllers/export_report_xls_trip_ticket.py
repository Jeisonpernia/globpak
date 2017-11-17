from collections import deque
import json

from odoo import http
from odoo.http import request
from odoo.tools import ustr
from odoo.tools.misc import xlwt

from datetime import date

class ExportReportXlsTripTicket(http.Controller):
	@http.route('/web/export_xls/report_trip_ticket', type='http', auth="user")
	def export_xls(self, filename, title, date_from, date_to, **kw):
		trip_ticket_ids = request.env['fleet.trip.ticket'].sudo().search([('ticket_date','>=',date_from),('ticket_date','<=',date_to)],order='name asc')

		workbook = xlwt.Workbook()
		worksheet = workbook.add_sheet(title)

		style_header_bold = xlwt.easyxf("font: bold on;font: name Calibri;align: wrap no")
		style_table_row = xlwt.easyxf("font: name Calibri;align: horiz left, wrap no;borders: top thin, bottom thin, right thin;")
		worksheet.col(0).width = 250*12
		worksheet.col(1).width = 500*12
		worksheet.col(2).width = 750*12
		worksheet.col(3).width = 750*12
		worksheet.col(4).width = 300*12
		worksheet.col(5).width = 800*12
		worksheet.col(6).width = 350*12

		worksheet.write(0, 0, 'TRIP TICKET NO', style_header_bold)
		worksheet.write(0, 1, 'DATE', style_header_bold)
		worksheet.write(0, 2, 'DRIVER', style_header_bold)
		worksheet.write(0, 3, 'DESTINATION', style_header_bold)
		worksheet.write(0, 4, 'GASOLINE', style_header_bold)
		worksheet.write(0, 5, 'READING (BEFORE)', style_header_bold)
		worksheet.write(0, 6, 'READING (AFTER)', style_header_bold)

		row_count = 1
		for ticket in trip_ticket_ids:
			worksheet.write(row_count, 0, ticket.name, style_table_row) 
			worksheet.write(row_count, 1, ticket.ticket_date, style_table_row)
			worksheet.write(row_count, 2, ticket.driver_id.name, style_table_row)
			worksheet.write(row_count, 3, ticket.destination, style_table_row)
			worksheet.write(row_count, 4, ticket.gas_diesel, style_table_row)
			worksheet.write(row_count, 5, ticket.reading_departure, style_table_row)
			worksheet.write(row_count, 6, ticket.reading_arrival, style_table_row)

			row_count +=1

		response = request.make_response(None,
		headers=[('Content-Type', 'application/vnd.ms-excel'),
			('Content-Disposition', 'attachment; filename=%s;'%(filename)
			)])

		workbook.save(response.stream)

		return response