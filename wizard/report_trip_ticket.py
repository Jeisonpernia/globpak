from odoo import models, fields, api

class ReportTripTicket(models.TransientModel):
	_name = 'report.trip.ticket'
	_description = 'Trip Ticket Report'

	date_from = fields.Date('Date From', required=True)
	date_to = fields.Date('Date To', required=True)

	def _print_report(self, data):
		filename = 'report_trip_ticket.xls'
		title = 'Trip Ticket Report'
		date_from = data['date_from']['date_from']
		date_to = data['date_to']['date_to']
		
		return {
			'type' : 'ir.actions.act_url',
			'url': '/web/export_xls/report_trip_ticket?filename=%s&title=%s&date_from=%s&date_to=%s'%(filename,title,date_from,date_to),
			'target': 'new',
		}

	@api.multi
	def generate_report(self):
		self.ensure_one()
		data = {}
		data['date_from'] = self.read(['date_from'])[0]
		data['date_to'] = self.read(['date_to'])[0]
		return self._print_report(data)