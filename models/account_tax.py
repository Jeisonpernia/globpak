from odoo import models, fields, api, _

class AccountTax(models.Model):
	_inherit = 'account.tax'

	# NEW FIELDS
	ewt_structure_id = fields.Many2one('account.ewt.structure', string='EWT Structure')

	# EXTEND
	amount_type = fields.Selection(selection=[('group', 'Group of Taxes'), ('fixed', 'Fixed'), ('percent', 'Percentage of Price'), ('division', 'Percentage of Price Tax Included'), ('base_deduction','Percentage of Price Tax Included Deduction - Custom')])

	def _compute_amount(self, base_amount, price_unit, quantity=1.0, product=None, partner=None):
		res = super(AccountTax, self)._compute_amount(base_amount, price_unit, quantity, product, partner)
		if self.amount_type == 'base_deduction':
			# base_amount = price_unit
			# tax_amount = price_unit * self.amount / 100
			return base_amount * self.amount / 100
		return res

