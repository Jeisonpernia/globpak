from odoo import models, fields, api, _ 

from odoo.tools import pycompat

import logging
_logger = logging.getLogger(__name__)

class ProductProduct(models.Model):
	_inherit = 'product.product'

	is_allowed_price_view = fields.Boolean(compute='_compute_group')
	is_allowed_price_cost_view = fields.Boolean(compute='_compute_group')
	parent_product = fields.Many2one('product.product')
	# plant_name = fields.Char()

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
		result = super(ProductProduct, self).create(values)
			
		if values.get('parent_product'):
			pricelist = self.env['product.pricelist.item']
			parent_product = self.env['product.template'].search([('id', '=', values.get('parent_product'))], limit=1)
			if parent_product:
				for item in parent_product.item_ids:
					pricelist.create({
						'product_id': result.id,
						'pricelist_id': item.pricelist_id.id,
						'fixed_price': item.fixed_price,
						'min_quantity': item.min_quantity,
						'date_start': item.date_start,
						'date_end': item.date_end,
					})

		return result

	@api.multi
	def write(self, values):

		result = super(ProductProduct, self).write(values)
			
		if values.get('parent_product'):
			pricelist = self.env['product.pricelist.item']
			parent_product = self.env['product.template'].search([('id', '=', values.get('parent_product'))], limit=1)
			if parent_product:
				for item in parent_product.item_ids:
					pricelist.create({
						'product_id': self.id,
						'pricelist_id': item.pricelist_id.id,
						'fixed_price': item.fixed_price,
						'min_quantity': item.min_quantity,
						'date_start': item.date_start,
						'date_end': item.date_end,
					})

		return result

	# EXTEND TO GET PRICELIST BY LOCATION
	def _compute_product_price(self):
		prices = {}
		pricelist_id_or_name = self._context.get('pricelist')
		if pricelist_id_or_name:
			pricelist = None
			partner = self._context.get('partner', False)
			quantity = self._context.get('quantity', 1.0)
			location = self._context.get('location', False)
			flc = self._context.get('flc')

			# Support context pricelists specified as display_name or ID for compatibility
			if isinstance(pricelist_id_or_name, pycompat.string_types):
				pricelist_name_search = self.env['product.pricelist'].name_search(pricelist_id_or_name, operator='=', limit=1)
				if pricelist_name_search:
					pricelist = self.env['product.pricelist'].browse([pricelist_name_search[0][0]])
			elif isinstance(pricelist_id_or_name, pycompat.integer_types):
				pricelist = self.env['product.pricelist'].browse(pricelist_id_or_name)

			if pricelist:
				quantities = [quantity] * len(self)
				partners = [partner] * len(self)
				locations = [location] * len(self)
				prices = pricelist.get_products_price(self, quantities, partners, locations, flc)

		for product in self:
			product.price = prices.get(product.id, 0.0)

	# OVERRIDE TO CHNAGE HOW NAME OF PRODUCT IS DISPLAYED
	@api.multi
	def name_get(self):
		def _name_get(d):
			name = d.get('name', '')
			code = self._context.get('display_default_code', True) and d.get('default_code', False) or False
			plant = d.get('plant_name', False) or False

			if code and plant:
				name = '[%s] %s - %s' % (code,name,plant)
			else:
				if code:
					name = '[%s] %s' % (code,name)
				if plant:
					name = '%s - %s' % (name,plant)

			return (d['id'], name)

		partner_id = self._context.get('partner_id')
		if partner_id:
			partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
			# _logger.info('TITCH')
			# _logger.info(partner_ids)
		else:
			partner_ids = []

		# all user don't have access to seller and partner
		# check access and use superuser
		self.check_access_rights("read")
		self.check_access_rule("read")

		result = []
		for product in self.sudo():
			# display only the attributes with multiple possible values on the template
			variable_attributes = product.attribute_line_ids.filtered(lambda l: len(l.value_ids) > 1).mapped('attribute_id')
			variant = product.attribute_value_ids._variant_name(variable_attributes)

			name = variant and "%s (%s)" % (product.name, variant) or product.name
			sellers = []
			if partner_ids:
				sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and (x.product_id == product)]
				if not sellers:
					sellers = [x for x in product.seller_ids if (x.name.id in partner_ids) and not x.product_id]
			if sellers:
				for s in sellers:
					seller_variant = s.product_name and (
						variant and "%s (%s)" % (s.product_name, variant) or s.product_name
						) or False
					mydict = {
						'id': product.id,
						'name': seller_variant or name,
						'default_code': s.product_code or product.default_code,
						'plant_name': product.plant_name,
					}
					temp = _name_get(mydict)
					if temp not in result:
						result.append(temp)
			else:
				mydict = {
					'id': product.id,
					'name': name,
					'default_code': product.default_code,
					'plant_name': product.plant_name,
				}
				result.append(_name_get(mydict))
		return result



class ProductTemplate(models.Model):
	_inherit = 'product.template'

	is_allowed_price_view = fields.Boolean(compute='_compute_group')
	is_allowed_price_cost_view = fields.Boolean(compute='_compute_group')
	parent_product = fields.Many2one('product.template')
	plant_name = fields.Char()

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

	# @api.multi
	# def _compute_template_price(self):
	# 	_logger.info("BANDA")

	# 	prices = {}
	# 	pricelist_id_or_name = self._context.get('pricelist')
	# 	if pricelist_id_or_name:
	# 		pricelist = None
	# 		partner = self._context.get('partner')
	# 		quantity = self._context.get('quantity', 1.0)
	# 		location = self._context.get('location')
			
	# 		_logger.info(location)

	# 		# Support context pricelists specified as display_name or ID for compatibility
	# 		if isinstance(pricelist_id_or_name, pycompat.string_types):
	# 			pricelist_data = self.env['product.pricelist'].name_search(pricelist_id_or_name, operator='=', limit=1)
	# 			if pricelist_data:
	# 				pricelist = self.env['product.pricelist'].browse(pricelist_data[0][0])
	# 		elif isinstance(pricelist_id_or_name, pycompat.integer_types):
	# 			pricelist = self.env['product.pricelist'].browse(pricelist_id_or_name)

	# 		if pricelist:
	# 			quantities = [quantity] * len(self)
	# 			partners = [partner] * len(self)
	# 			prices = pricelist.get_products_price(self, quantities, partners)

	# 	for template in self:
	# 		template.price = prices.get(template.id, 0.0)

	@api.multi
	def name_get(self):
		return [(template.id, '%s%s%s' % (template.default_code and '[%s] ' % template.default_code or '', template.name, template.plant_name and ' - %s' % template.plant_name or ''))
				for template in self]