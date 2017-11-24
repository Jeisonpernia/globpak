from odoo import models, fields, api, _

class AccountLandedCost(models.Model):
	_name = 'account.landed.cost'
	_description = 'Account Landed Cost'

	name = fields.Char(string='Landed Cost', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
	line_ids = fields.One2many('account.landed.cost.line', 'landed_cost_id', string='Landed Cost Line')
	amount_total = fields.Float('Amount', store=True, compute="")
	invoice_id = fields.Many2one('account.invoice', 'Invoice')
	
	@api.model
	def create(self, values):
		if values.get('name', 'New') == 'New':
			values['name'] = self.env['ir.sequence'].next_by_code('account.landed.cost') or 'New'

		result = super(AccountLandedCost, self).create(values)
		return result

	@api.one
	@api.depends('line_ids', 'line_ids.amount')
	def _compute_amount(self):
		amount_total = 0
		for line in self.line_ids:
			amount_total += line.amount

		self.amount_total = amount_total

class AccountLandedCostLine(models.Model):
	_name = 'account.landed.cost.line'

	name = fields.Many2one('product.product', 'Landed Cost Type', domain=[('landed_cost_ok', '=', True),('active', '=', True)])
	amount = fields.Float('Amount')
	landed_cost_id = fields.Many2one('account.landed.cost', 'Landed Cost')
