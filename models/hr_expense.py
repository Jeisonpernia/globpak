from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

class HrExpenseSheet(models.Model):
	_inherit = 'hr.expense.sheet'

	untaxed_amount = fields.Float(string='Subtotal', store=True, compute='_compute_amount_untaxed', digits=dp.get_precision('Account'))

	@api.one
	@api.depends('expense_line_ids', 'expense_line_ids.untaxed_amount')
	def _compute_amount_untaxed(self):
		self.untaxed_amount = sum(self.expense_line_ids.mapped('untaxed_amount'))

	# @api.multi
	# def myfunction(self):
	# 	self.ensure_one()
	# 	res = {}
	# 	currency = self.currency_id or self.company_id.currency_id
	# 	for expense in self.expense_line_ids:
			
	# 		for line in expense.tax_ids:
	# 			res.setdefault(line.tax_group_id, 0.0)
	# 			amount = line.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id, expense.employee_id.user_id.partner_id)['taxes'][0]['amount']
	# 			res[line.tax_group_id] += amount
	# 	res = sorted(res.items(), key=lambda l: l[0].sequence)
	# 	res = map(lambda l: (l[0].name, l[1]), res)
	# 	return res

	@api.multi
	def get_tax_details(self, line, tax):
		currency = self.currency_id or self.company_id.currency_id
		amount = tax.compute_all(line.unit_amount, currency, line.quantity, line.product_id, line.employee_id.user_id.partner_id)['taxes'][0]['amount']
		return amount
