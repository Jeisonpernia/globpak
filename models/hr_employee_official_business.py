from odoo import models, fields, api, _

from odoo.exceptions import UserError

import logging
_logger = logging.getLogger(__name__)

class Calendar(models.Model):
	_inherit = 'calendar.event'

	ob_id = fields.Many2one('hr.employee.official.business', 'Official Business')

class HrEmployeeOfficialBusiness(models.Model):
	_name = 'hr.employee.official.business'
	_description = 'HR Employee Official Business'
	_inherit = ['mail.thread','mail.activity.mixin']
	_order = "date_ob desc, id desc"

	name = fields.Char(string='OB #', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
	employee_id = fields.Many2one('hr.employee', 'Employee', required=True, default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1), track_visibility='always', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'cancel': [('readonly', False)]})
	# department_id = fields.Many2one('hr.department', 'Department', store=True, compute='_set_employee_details')
	date_ob = fields.Date(required=True, default=fields.Datetime.now(), string='Date of Official Business', track_visibility='always', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'cancel': [('readonly', False)]})
	date_submitted = fields.Datetime(string='Submitted Date')
	company_id = fields.Many2one('res.company', 'Company', store=True, default=lambda self: self.env.user.company_id, readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'cancel': [('readonly', False)]})
	departure_time = fields.Selection([
		('earlymorning', 'Early Morning'),
		('morning', 'Morning'),
		('directob', 'Direct OB'),
		('afternoon', 'Afternoon'),
		('anytime', 'Anytime Within The Day'),
	], string='Estimated Time of Departure', required=True, track_visibility='always', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'cancel': [('readonly', False)]})
	visit_purpose = fields.Text(string='Purpose of Visit', required=True, track_visibility='always', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'cancel': [('readonly', False)]})
	visit_person = fields.Text(string='Person to Visit', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'cancel': [('readonly', False)]})
	visit_place = fields.Text(string='Place to Visit', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'cancel': [('readonly', False)]})
	transportation_means = fields.Selection([
		('uber', 'Uber/Grab'),
		('companycar', 'With Company Car'),
		('truck', 'Truck'),
		('commute','Commute'),
		('others', 'Others'),
	], string='Means of Transportation', required=True, track_visibility='always', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'cancel': [('readonly', False)]})
	remarks = fields.Text(string='Other Remarks', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'cancel': [('readonly', False)]})
	user_id = fields.Many2one('res.user', 'User')
	# approver_id = fields.Many2one('hr.employee','Approver', store=True, compute='_set_employee_details', track_visibility='always')
	approver_id = fields.Many2one('hr.employee','Approver', store=True, required=True, track_visibility='always')
	state = fields.Selection([
		('draft', 'To Submit'),
		('confirm', 'Pending'),
		('cancel', 'Refused'),
		('validate', 'Approved'),
		('expense', 'In Expense'),
		('done', 'Done'),
	], default='draft', track_visibility='onchange')

	current_user = fields.Many2one('res.users', compute='_get_current_user')

	@api.multi
	def name_get(self):
		res = []
		for rec in self:
			name = '[%s] %s' % (rec.name, rec.visit_purpose)
			res.append((rec.id, name))
		return res

	@api.depends()
	def _get_current_user(self):
		for rec in self:
			rec.current_user = self.env.user
		# i think this work too so you don't have to loop
		self.update({'current_user' : self.env.user.id})
	
	@api.model
	def create(self, values):
		if values.get('name', 'New') == 'New':
			values['name'] = self.env['ir.sequence'].next_by_code('hr.employee.official.business') or 'New'

		result = super(HrEmployeeOfficialBusiness, self).create(values)
			
		if values.get('employee_id'):
			result._add_followers()

		return result

	def _add_followers(self):
		user_ids = []
		employee = self.employee_id
		if employee.user_id:
			user_ids.append(employee.user_id.id)
		# if employee.parent_id:
			# user_ids.append(employee.parent_id.user_id.id)
		# if employee.department_id and employee.department_id.manager_id and employee.parent_id != employee.department_id.manager_id:
			# user_ids.append(employee.department_id.manager_id.user_id.id)
		self.message_subscribe_users(user_ids=user_ids)

	# @api.depends('employee_id')
	# def _set_employee_details(self):
	# 	for ob in self:
	# 		# ob.department_id = ob.employee_id.department_id
	# 		ob.approver_id = ob.employee_id.parent_id

	@api.onchange('employee_id')
	def _set_employee_details(self):
		self.approver_id = self.employee_id.parent_id

	@api.multi
	def submit_ob(self):
		for ob in self:
			# CREATE CALENDAR
			calendar = self.env['calendar.event']
			employee = ob.employee_id
			# approver = self.env['hr.employee'].search([('id', '=', values.get('approver_id'))], limit=1)
			event = {
				'name': ob.name,
				'description': ob.visit_purpose,
				'allday': True,
				'start':ob.date_ob,
				'stop': ob.date_ob,
				'location': ob.visit_place,
				'user_id': employee.user_id.id,
				'privacy': 'confidential',
				'ob_id': ob.id,
				# 'categ_ids': ['categ_ob_pending'],
			}
			calendar.create(event)

			ob.state = 'confirm'
			ob.date_submitted = fields.Datetime.now()

	@api.multi
	def approve_ob(self):
		self.ensure_one()
		calendar = self.env['calendar.event']
		# for ob in self:
		if self.approver_id:
			if self.approver_id.user_id != self.current_user:
				raise UserError("You're not allowed to approve this OB. OB Approver: %s" % (self.approver_id.name))
		else:
			raise UserError("No Approver was set. Please assign an approver to employee.")

		self.state = 'validate'


	@api.multi
	def refuse_ob(self):
		for ob in self:
			if ob.approver_id:
				if ob.approver_id.user_id != ob.current_user:
					raise UserError("You're not allowed to refuse this OB. OB Approver: %s" % (ob.approver_id.name))
			else:
				raise UserError("No Approver was set. Please assign an approver to employee.")

			# Remove event if OB was refused
			calendar = self.env['calendar.event'].search([('ob_id', '=', ob.id)], limit=1)
			calendar.unlink()
			ob.state = 'cancel'

	@api.multi
	def done_ob(self):
		for ob in self:
			ob.state = 'done'

	@api.multi
	def action_print(self):
		self.ensure_one()
		return self.env.ref('globpak.action_official_business').report_action(self)