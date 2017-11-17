from odoo import models, fields, api, _ 

class FleetTripTicket(models.Model):
	_name = 'fleet.trip.ticket'
	_descrription = 'Fleet Trip Ticket'
	_inherit = ['mail.thread']


	name = fields.Char(string='Trip Ticket #', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
	ticket_date = fields.Date(string='Date', required=True)
	driver_id = fields.Many2one('res.partner', 'Vehicle Driver Name', required=True)
	vehicle_id = fields.Many2one('fleet.vehicle', 'Type of Vehicle Used', required=True)
	license_plate = fields.Char(string='Plate No.', related='vehicle_id.license_plate')
	destination = fields.Char(string='Place of Destination', required=True)
	purpose = fields.Text(string='Purpose/Details')
	estimate_kilometers = fields.Char(string='Estimate Kilometers')
	gas_diesel = fields.Float(string='Gas/Diesel', default=1.00)
	oil_fluid = fields.Float(string='OIL/FLUID', default=1.00)
	reading_departure = fields.Float(string='Reading (Departure)')
	reading_arrival = fields.Float(string='Reading (Arrival)')
	departure_time = fields.Float(string='Time of Departure from Office or Garage')
	arrival_time = fields.Float(string='Time of Arrival')
	passenger_id = fields.Many2one('res.partner', 'Passenger')
	manager_id = fields.Many2one('res.partner', 'Procurement & Logistics Manager')
	president_id = fields.Many2one('res.partner', 'President')
	# user_id = fields.Many2one('res.user', 'User', default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))

	@api.model
	def create(self, values):
		if values.get('name', 'New') == 'New':
			values['name'] = self.env['ir.sequence'].next_by_code('fleet.trip.ticket') or 'New'

		result = super(FleetTripTicket, self).create(values)
		return result