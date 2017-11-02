from odoo import models, fields, api, _ 

class StudioHrEmployee(models.Model):
	_inherit = 'hr.employee'

	x_hiredate = fields.Date('Hire Date', store=True, copy=True)
	x_regularizationdate = fields.Date('Regularization Date', store=True, copy=True)
	x_idno = fields.Char('Company ID No.', store=True, copy=True)
	x_payrollaccount = fields.Char('Payroll Account No.', store=True, copy=True)
	