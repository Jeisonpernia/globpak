from odoo import models, fields, api

class Product(models.Model):
	_inherit = 'product.product'

	is_allowed_price_view = fields.Boolean(compute='_compute_group')
	is_allowed_price_cost_view = fields.Boolean(compute='_compute_group')
	parent_product = fields.Many2one('product.product')

	# @api.depends('name')
	@api.multi
	def _compute_group(self):
		for record in self:
			user = self.env['res.users'].browse(self.env.uid)

			# Sale Price
			# if user.has_group('purchase.group_purchase_user') or user.has_group('stock.group_stock_user'):
			if user.has_group('purchase.group_purchase_user') or user.has_group('purchase.group_purchase_manager'):
				record.is_allowed_price_view = False
				if user.has_group('account.group_account_user') or user.has_group('account.group_account_manager'):
					record.is_allowed_price_view = True
				if user.has_group('sales_team.group_sale_salesman_all_leads') or user.has_group('sales_team.group_sale_salesman') or user.has_group('sales_team.group_sale_manager'):
					record.is_allowed_price_view = True
			else:
				record.is_allowed_price_view = True

			# Cost Price
			if user.has_group('sales_team.group_sale_salesman_all_leads') or user.has_group('sales_team.group_sale_salesman') or user.has_group('sales_team.group_sale_manager'):
				record.is_allowed_price_cost_view = False
				if user.has_group('account.group_account_user') or user.has_group('account.group_account_manager'):
					record.is_allowed_price_cost_view = True
				if user.has_group('purchase.group_purchase_user') or user.has_group('purchase.group_purchase_manager'):
					record.is_allowed_price_cost_view = True
			else:
				record.is_allowed_price_cost_view = True



class ProductTemplate(models.Model):
	_inherit = 'product.template'

	is_allowed_price_view = fields.Boolean(compute='_compute_group')
	is_allowed_price_cost_view = fields.Boolean(compute='_compute_group')
	parent_product = fields.Many2one('product.template')

	# @api.depends('name')
	@api.multi
	def _compute_group(self):
		for record in self:
			user = self.env['res.users'].browse(self.env.uid)

			# Sale Price
			# if user.has_group('purchase.group_purchase_user') or user.has_group('stock.group_stock_user'):
			if user.has_group('purchase.group_purchase_user') or user.has_group('purchase.group_purchase_manager'):
				record.is_allowed_price_view = False
				if user.has_group('account.group_account_user') or user.has_group('account.group_account_manager'):
					record.is_allowed_price_view = True
			else:
				record.is_allowed_price_view = True

			# Cost Price
			if user.has_group('sales_team.group_sale_salesman_all_leads') or user.has_group('sales_team.group_sale_salesman') or user.has_group('sales_team.group_sale_manager'):
				record.is_allowed_price_cost_view = False
				if user.has_group('account.group_account_user') or user.has_group('account.group_account_manager'):
					record.is_allowed_price_cost_view = True
			else:
				record.is_allowed_price_cost_view = True

	@api.model
	def create(self, values):
		result = super(ProductTemplate, self).create(values)
			
		if values.get('parent_product'):
			pricelist = self.env['product.pricelist.item']
			parent_product = self.env['product.template'].search([('id', '=', values.get('parent_product'))], limit=1)
			if parent_product:
				for item in parent_product.item_ids:
					pricelist.create({
						'product_tmpl_id': result.id,
						'pricelist_id': item.pricelist_id.id,
						'fixed_price': item.fixed_price,
						'min_quantity': item.min_quantity,
						'date_start': item.date_start,
						'date_end': item.date_end,
					})

		return result

	@api.multi
	def write(self, values):

		result = super(ProductTemplate, self).write(values)
			
		if values.get('parent_product'):
			pricelist = self.env['product.pricelist.item']
			parent_product = self.env['product.template'].search([('id', '=', values.get('parent_product'))], limit=1)
			if parent_product:
				for item in parent_product.item_ids:
					pricelist.create({
						'product_tmpl_id': self.id,
						'pricelist_id': item.pricelist_id.id,
						'fixed_price': item.fixed_price,
						'min_quantity': item.min_quantity,
						'date_start': item.date_start,
						'date_end': item.date_end,
					})

		return result