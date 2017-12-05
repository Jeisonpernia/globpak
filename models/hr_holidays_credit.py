# from odoo import models, fields, api

# class HrEmployee(models.Model):
# 	_inherit = 'hr.employee'

# 	holiday_credit_id = fields.Many2one('hr.holidays.credit')

# class HrHolidaysCredit(models.Model):
# 	_name = 'hr.holidays.credit'

# 	credit_count = fields.Float()
# 	credit_year = fields.Char('Year')

# 	employee_ids = fields.One2many('hr.employee', 'holiday_credit_id', string='Employees')

# 	@api.multi
# 	def compute_holidays_credit(self):
# 		employee_ids = self.env['hr.employee'].search([])
# 		for employee in employee_ids:
# 			employee.write({'remaining_leaves': self.credit_count})

# 		self.write({'employee_ids': employee_ids})
