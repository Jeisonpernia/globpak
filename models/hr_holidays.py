from odoo import models, fields, api

from odoo.exceptions import UserError

class HrHolidays(models.Model):
	_inherit = 'hr.holidays'

	approver_id = fields.Many2one('hr.employee','Approver', compute='_set_employee_details')
	current_user = fields.Many2one('res.users', compute='_get_current_user')

	@api.depends('employee_id')
	def _set_employee_details(self):
		for ob in self:
			ob.approver_id = ob.employee_id.parent_id

	@api.depends()
	def _get_current_user(self):
		for rec in self:
			rec.current_user = self.env.user
		# i think this work too so you don't have to loop
		self.update({'current_user' : self.env.user.id})

	# EXTEND FUNCTIONS
	@api.multi
	def action_approve(self):
		for record in self:
			if record.approver_id.user_id != record.current_user:
				raise UserError("You're not allowed to approve this leave. Leave Approver: %s" % (record.approver_id.name))
		res = super(HrHolidays, self).action_approve()
		return res

	@api.multi
	def action_refuse(self):
		for record in self:
			if record.approver_id.user_id != record.current_user:
				raise UserError("You're not allowed to refuse this leave. Leave Approver: %s" % (record.approver_id.name))
		res = super(HrHolidays, self).action_refuse()
		return res