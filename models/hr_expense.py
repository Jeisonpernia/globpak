from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

import logging
_logger = logging.getLogger(__name__)

# class HrExpense(models.Model):
# 	_inherit = 'hr.expense'

# 	tax_amount = fields.Float()
	# tax_amount = fields.Float(string='Tax Amount', store=True, compute='_compute_tax', digits=dp.get_precision('Account'))

	# @api.depends('quantity', 'unit_amount', 'tax_ids', 'currency_id')
 #    def _compute_tax(self):
 #    	for expense in self:
 #    		line_tax = expense.tax_ids.compute_all(expense.unit_amount, expense.currency_id, expense.quantity, expense.product_id, expense.employee_id.user_id.partner_id)
 #        	expense.tax_amount = line_tax.get('total_included')

class HrExpenseSheet(models.Model):
	_inherit = 'hr.expense.sheet'

	untaxed_amount = fields.Float(string='Subtotal', store=True, compute='_compute_amount_untaxed', digits=dp.get_precision('Account'))

	@api.one
	@api.depends('expense_line_ids', 'expense_line_ids.untaxed_amount')
	def _compute_amount_untaxed(self):
		self.untaxed_amount = sum(self.expense_line_ids.mapped('untaxed_amount'))

 	@api.multi
    def _get_tax_amount_by_group(self):
        self.ensure_one()
        res = {}
        currency = self.currency_id or self.company_id.currency_id
        for expense in self.expense_line_ids:
        	for line in expense.tax_ids:
            	res.setdefault(line.tax_group_id, 0.0)
            	res[line.tax_group_id] += line.amount
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = map(lambda l: (l[0].name, l[1]), res)
        _logger.info('SHALALA')
        _logger.info(res)
        return res