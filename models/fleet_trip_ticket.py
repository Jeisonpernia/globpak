from odoo import models, fields, api, _ 

from odoo.exceptions import UserError

class FleetTripTicket(models.Model):
	_name = 'fleet.trip.ticket'
	_descrription = 'Fleet Trip Ticket'
	_inherit = ['mail.thread','mail.activity.mixin']

	@api.multi
	def _get_manager(self):
		job_id = self.env['hr.job'].search([('name', 'ilike', 'Procurement and Logistics Manager')], limit=1)
		approver_id = self.env['hr.employee'].search([('job_id', '=', job_id.id)], limit=1)
		return approver_id

	name = fields.Char(string='Trip Ticket #', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
	ticket_date = fields.Date(string='Date', required=True, default=fields.Datetime.now(), track_visibility='always')
	driver_id = fields.Many2one('res.partner', 'Vehicle Driver Name', required=True, track_visibility='always')
	vehicle_id = fields.Many2one('fleet.vehicle', 'Type of Vehicle Used', required=True, track_visibility='always')
	license_plate = fields.Char(string='Plate No.', related='vehicle_id.license_plate')
	destination = fields.Char(string='Place of Destination', required=True, track_visibility='always')
	purpose = fields.Text(string='Purpose/Details')
	estimate_kilometers = fields.Char(string='Estimate Kilometers')
	gas_diesel = fields.Float(string='Gas/Diesel', default=1.00)
	oil_fluid = fields.Float(string='OIL/FLUID', default=1.00)
	reading_departure = fields.Float(string='Reading (Departure)')
	reading_arrival = fields.Float(string='Reading (Arrival)')
	departure_time = fields.Float(string='Time of Departure from Office or Garage')
	arrival_time = fields.Float(string='Time of Arrival')

	company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
	employee_id = fields.Many2one('hr.employee', 'Created By', required=True, default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))
	passenger_id = fields.Many2one('res.partner', 'Passenger')

	approver_id = fields.Many2one('hr.employee', 'Procurement & Logistics Manager', required=True, default=_get_manager, track_visibility='always')
	president_id = fields.Many2one('res.partner', 'President')
	
	state = fields.Selection([
		('draft', 'To Submit'),
		('confirm', 'Pending'),
		('validate', 'Approved'),
		('done', 'Done'),
		('cancel', 'Canceled'),
	], default='draft', track_visibility='onchange')

	current_user = fields.Many2one('res.users', compute='_get_current_user')

	@api.depends()
	def _get_current_user(self):
		# for rec in self:
		# 	rec.current_user = self.env.user
		self.update({'current_user' : self.env.user.id})

	@api.model
	def create(self, values):
		if values.get('name', 'New') == 'New':
			values['name'] = self.env['ir.sequence'].next_by_code('fleet.trip.ticket') or 'New'

		result = super(FleetTripTicket, self).create(values)
		result._add_followers()

		return result

	@api.multi
	def submit_trip(self):
		for trip in self:
			trip.state = 'confirm'

	@api.multi
	def approve_trip(self):
		for trip in self:
			if trip.approver_id.user_id != trip.current_user:
				raise UserError("You're not allowed to approve this trip. Trip Approver: %s" % (trip.approver_id.name))
			trip.state = 'validate'

	@api.multi
	def cancel_trip(self):
		for trip in self:
			if trip.approver_id.user_id != trip.current_user:
				raise UserError("You're not allowed to refuse this trip. Trip Approver: %s" % (trip.approver_id.name))
			trip.state = 'cancel'

	@api.multi
	def done_trip(self):
		for trip in self:
			trip.state = 'done'

	def _add_followers(self):
		user_ids = []
		employee = self.employee_id
		approver = self.approver_id
		if employee.user_id:
			user_ids.append(employee.user_id.id)
		if employee.parent_id:
			user_ids.append(employee.parent_id.user_id.id)
		if employee.department_id and employee.department_id.manager_id and employee.parent_id != employee.department_id.manager_id:
			user_ids.append(employee.department_id.manager_id.user_id.id)
		if approver.user_id:
			user_ids.append(approver.user_id.id)
		self.message_subscribe_users(user_ids=user_ids)