from odoo import models, fields, api, _

class AccountLandedCost(models.Model):
	_name = 'account.landed.cost'
	_description = 'Account Landed Cost'

	name = fields.Char(string='Landed Cost', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
	line_ids = fields.One2many('account.landed.cost.line', 'landed_cost_id', string='Landed Cost Line')
	amount_total = fields.Float(string='Amount')
	invoice_id = fields.Many2one('account.invoice', 'Invoice')
	
	@api.model
	def create(self, values):
		if values.get('name', 'New') == 'New':
			values['name'] = self.env['ir.sequence'].next_by_code('account.landed.cost') or 'New'

		result = super(AccountLandedCost, self).create(values)
		return result


class AccountLandedCostLine(models.Model):
	_name = 'account.landed.cost.line'

	name = fields.Char()
	amount = fields.Float('Amount')
	invoice_id = fields.Many2one('account.invoice', 'Invoice')
	landed_cost_id = fields.Many2one('account.landed.cost', 'Landed Cost')
