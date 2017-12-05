from odoo import models, fields, api, _ 
from odoo.exceptions import UserError, AccessError

class StudioSalesOrder(models.Model):
	_inherit = 'sale.order'

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
		if user.has_group('sales_team.group_sale_salesman_all_leads') or user.has_group('sales_team.group_sale_salesman') or user.has_group('sales_team.group_sale_manager'):
			self.is_allowed_sale_validate_confirm = False
		
		if user.has_group('account.group_account_manager'):
			self.is_allowed_sale_validate_confirm = True

class StudioSalesOrderLine(models.Model):
	_inherit = 'sale.order.line'

	is_allowed_price_edit = fields.Boolean(compute='_compute_group')

	@api.depends('product_id')
	def _compute_group(self):
		user = self.env['res.users'].browse(self.env.uid)
		if user.has_group('sales_team.group_sale_salesman_all_leads') or user.has_group('sales_team.group_sale_salesman') or user.has_group('sales_team.group_sale_manager'):
			self.is_allowed_price_edit = False
			if user.has_group('account.group_account_invoice') or user.has_group('account.group_account_user') or user.has_group('account.group_account_manager'):
				self.is_allowed_price_edit = True
		else:
			self.is_allowed_price_edit = True