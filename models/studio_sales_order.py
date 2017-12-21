from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, AccessError

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
	subject = fields.Char()
	description = fields.Text()

	state = fields.Selection([
		('draft', 'Quotation'),
		('sent', 'Quotation Sent'),
		('validate', 'Validated'),
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

	@api.multi
	def action_confirm(self):
		for record in self:
			if not record.x_clientpo:
				raise UserError('Cannot confirm sale. Client PO number is required.')

		res = super(StudioSalesOrder, self).action_confirm()
		return res

	@api.multi
	def action_validate(self):
		for record in self:
			if not record.x_clientpo:
				raise UserError('Cannot validate sale. Client PO number is required.')
			else:
				record.write({'state': 'validate'})

	@api.depends('partner_id')
	def _compute_group(self):
		user = self.env['res.users'].browse(self.env.uid)
		for record in self:
			if user.has_group('sales_team.group_sale_salesman_all_leads') or user.has_group('sales_team.group_sale_salesman') or user.has_group('sales_team.group_sale_manager'):
				record.is_allowed_sale_validate_confirm = False
			
			if user.has_group('account.group_account_manager'):
				record.is_allowed_sale_validate_confirm = True

class StudioSalesOrderLine(models.Model):
	_inherit = 'sale.order.line'

	is_allowed_price_edit = fields.Boolean(compute='_compute_group')

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