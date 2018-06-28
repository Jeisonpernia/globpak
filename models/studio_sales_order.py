from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, AccessError

import logging
_logger = logging.getLogger(__name__)

class StudioSalesOrder(models.Model):
	_inherit = 'sale.order'

	@api.one
	@api.depends('order_line', 'order_line.price_subtotal')
	def _compute_amount_sales(self):
		vat_sales = 0
		vat_exempt = 0
		zero_rated = 0
		for line in self.order_line:
			if line.tax_id:
				for tax in line.tax_id:
					# Check if zero rated sales or vatable sales
					if tax.amount == 0:
						# Zero Rated Sales
						zero_rated += line.price_subtotal
					else:
						# Vatable Sales
						vat_sales += line.price_subtotal
			else:
				# Vat Exempt Sales
				vat_exempt += line.price_subtotal

		self.vat_sales = vat_sales
		self.vat_exempt_sales = vat_exempt
		self.zero_rated_sales = zero_rated


	@api.one
	@api.depends('order_line', 'order_line.product_id', 'order_line.price_subtotal')
	def _compute_amount_product_type(self):
		amount_services = 0
		amount_capital = 0
		amount_goods = 0
		for line in self.order_line:
			if line.product_id.type == 'service':
				amount_services += line.price_subtotal

			if line.product_id.type == 'consu' or line.product_id.type == 'product':
				amount_goods += line.price_subtotal

		self.amount_services = amount_services
		self.amount_goods = amount_goods

	x_clientpo = fields.Char(string='Client PO No.', store=True, copy=True)
	subject = fields.Char(required=True)
	description = fields.Text(required=False)

	state = fields.Selection([
		('draft', 'Quotation'),
		('sent', 'Quotation Sent'),
		('confirm', 'Confirmed (Client)'),
		('sale', 'Sales Order'),
		('done', 'Locked'),
		('cancel', 'Cancelled'),
	])

	is_allowed_sale_validate_confirm = fields.Boolean(compute='_compute_group')

	vat_sales = fields.Monetary(string='Vatable Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
	vat_exempt_sales = fields.Monetary(string='Vat Exempt Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
	zero_rated_sales = fields.Monetary(string='Zero Rated Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')

	amount_services = fields.Monetary(string='Amount of Services', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')
	amount_capital = fields.Monetary(string='Amount of Capital', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')
	amount_goods = fields.Monetary(string='Amount of Goods', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')

	account_name = fields.Char(compute='_get_customer_details')
	contact_name = fields.Char(compute='_get_customer_details')
	partner_contact_id = fields.Many2one('res.partner', string='Contact Person')

	@api.multi
	def action_confirm(self):
		for record in self:
			if not record.x_clientpo:
				raise UserError('Cannot confirm sale. Client PO number is required.')

		res = super(StudioSalesOrder, self).action_confirm()
		return res

	# @api.multi
	# def action_validate(self):
	# 	for record in self:
			# if not record.x_clientpo:
			# 	raise UserError('Cannot validate sale. Client PO number is required.')
			# else:
			# record.write({'state': 'validate'})

	@api.depends('partner_id')
	def _compute_group(self):
		user = self.env['res.users'].browse(self.env.uid)
		for record in self:
			if user.has_group('sales_team.group_sale_salesman_all_leads') or user.has_group('sales_team.group_sale_salesman') or user.has_group('sales_team.group_sale_manager'):
				record.is_allowed_sale_validate_confirm = False
				if record.state == 'confirm':
					record.is_allowed_sale_validate_confirm = True
			
			if user.has_group('account.group_account_manager'):
				record.is_allowed_sale_validate_confirm = True

	@api.multi
	def _get_customer_details(self):
		for record in self:
			account_name = ''
			contact_name = ''

			if record.partner_id.company_type == 'company':
				account_name = record.partner_id.name
				contact_name = ''
			else:
				account_name = record.partner_id.parent_id.name
				contact_name = record.partner_id.name

				if not record.partner_id.parent_id:
					account_name = record.partner_id.name
					contact_name = ''

			record.account_name = account_name
			record.contact_name = contact_name

class StudioSalesOrderLine(models.Model):
	_inherit = 'sale.order.line'

	is_allowed_price_edit = fields.Boolean(compute='_compute_group')
	is_flc = fields.Boolean(string='FCL', default=False)

	@api.depends('product_id')
	def _compute_group(self):
		user = self.env['res.users'].browse(self.env.uid)
		for record in self:
			if user.has_group('sales_team.group_sale_salesman_all_leads') or user.has_group('sales_team.group_sale_salesman') or user.has_group('sales_team.group_sale_manager'):
				record.is_allowed_price_edit = False
				if user.has_group('account.group_account_invoice') or user.has_group('account.group_account_user') or user.has_group('account.group_account_manager'):
					record.is_allowed_price_edit = True
			else:
				record.is_allowed_price_edit = True

	@api.multi
	def _get_display_price(self, product):
		location_id = self.order_id.partner_shipping_id.state_id
		# if self.order_id.partner_shipping_id.state_id:
		# 	raise UserError(self.order_id.partner_shipping_id.state_id.name)

		# TO DO: move me in master/saas-16 on sale.order
		_logger.info("TINDE")
		if self.order_id.pricelist_id.discount_policy == 'with_discount':
			_logger.info(product.with_context(pricelist=self.order_id.pricelist_id.id))
			return product.with_context(pricelist=self.order_id.pricelist_id.id).price
		final_price, rule_id = self.order_id.pricelist_id.get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
		pricelist_item = self.env['product.pricelist.item'].browse(rule_id)
		if pricelist_item.base == 'pricelist':
			base_price, rule_id = pricelist_item.base_pricelist_id.get_product_price_rule(self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
			base_price = pricelist_item.base_pricelist_id.currency_id.compute(base_price, self.order_id.pricelist_id.currency_id)
		else:
			base_price = product[pricelist_item.base] if pricelist_item else product.lst_price
			base_price = product.currency_id.compute(base_price, self.order_id.pricelist_id.currency_id)
		# negative discounts (= surcharge) are included in the display price (= unit price)
		return max(base_price, final_price)

	# EXTEND TO GET PRICELIST BY LOCATION / USE DELIVERY ADDRESS (STATE) AS LOCATION
	@api.onchange('product_uom', 'product_uom_qty', 'is_flc')
	def product_uom_change(self):
		if not self.product_uom or not self.product_id:
			self.price_unit = 0.0
			return
		if self.order_id.pricelist_id and self.order_id.partner_id:
			product = self.product_id.with_context(
				lang=self.order_id.partner_id.lang,
				partner=self.order_id.partner_id.id,
				quantity=self.product_uom_qty,
				date=self.order_id.date_order,
				pricelist=self.order_id.pricelist_id.id,
				uom=self.product_uom.id,
				fiscal_position=self.env.context.get('fiscal_position'),
				location=self.order_id.partner_shipping_id.state_id.id,
				flc=self.is_flc
			)
			self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product), product.taxes_id, self.tax_id, self.company_id)