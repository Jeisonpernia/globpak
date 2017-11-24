from odoo import models, fields, api

class Product(models.Model):
	_inherit = 'product.product'

	is_allowed_price_view = fields.Boolean(compute='_compute_group')

	# @api.depends('name')
	def _compute_group(self):
		user = self.env['res.users'].browse(self.env.uid)
		if user.has_group('purchase.group_purchase_user') or user.has_group('stock.group_stock_user'):
			self.is_allowed_price_edit = False
		else:
			self.is_allowed_price_edit = True