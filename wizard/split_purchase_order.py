from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SplitPurchaseOrderLine(models.TransientModel):
	_name = 'split.purchase.order.line'
	_description = 'Split Purchase Order Line'

	purchase_order = fields.Many2one('purchase.order')
	line_id = fields.Many2one('purchase.order.line')
	product_id = fields.Many2one('product.product')
	product_qty = fields.Float()
	new_quantity = fields.Float()
	wizard_id = fields.Many2one('split.purchase.order', string="Wizard")


class SplitPurchaseOrder(models.TransientModel):
	_name = 'split.purchase.order'
	_description = 'Split Purchase Order'

	purchase_order = fields.Many2one('purchase.order')
	new_vendor = fields.Many2one('res.partner')
	line_ids = fields.One2many('split.purchase.order.line', 'wizard_id', 'Purchase Lines')

	@api.model
	def default_get(self, fields):
		res = super(SplitPurchaseOrder, self).default_get(fields)

		purchase_order_lines = []
		purchase_order = self.env['purchase.order'].browse(self.env.context.get('active_id'))
		if purchase_order:
			res.update({'purchase_order': purchase_order.id})
			
			for line in purchase_order.order_line:
				purchase_order_lines.append((0, 0, {'product_id': line.product_id.id, 'product_qty': line.product_qty, 'new_quantity': 0, 'purchase_order': purchase_order.id, 'line_id': line.id}))

			if not purchase_order_lines:
				raise UserError(_("No products to split!"))
			if 'line_ids' in fields:
				res.update({'line_ids': purchase_order_lines})
		return res

	def _prepare_line_default_values(self, line, new_purchase):
		vals = {
			'product_id': line.product_id.id,
			'product_qty': line.new_quantity,
			'order_id': new_purchase.id,
		}
		return vals

	def _split_purchase_order(self):
		# create new picking for returned products
		new_purchase = self.purchase_order.copy({
			'order_line': [],
			'partner_id': self.new_vendor.id,
			'state': 'draft',
			'origin': self.purchase_order.origin,
			'date_planned': self.purchase_order.date_planned})

		new_purchase.message_post_with_view('mail.message_origin_link',
			values={'self': new_purchase, 'origin': self.purchase_order},
			subtype_id=self.env.ref('mail.mt_note').id)

		order_line = 0
		for line in self.line_ids:
			if not line.purchase_order:
				raise UserError(_("You have manually created product lines, please delete them to proceed"))
			if line.new_quantity:
				order_line += 1
				new_product_qty = line.product_qty -  line.new_quantity
				vals = self._prepare_line_default_values(line, new_purchase)
				line.line_id.copy(vals)
				line.line_id.write({'product_qty':new_product_qty})
		if not order_line:
			raise UserError(_("Please specify at least one non-zero quantity."))

		return new_purchase.id

	def split_purchase_order(self):
		for wizard in self:
			new_purchase = wizard._split_purchase_order()
		# Override the context to disable all the potential filters that could have been set previously
		ctx = dict(self.env.context)
		# ctx.update({
		# 	'search_default_picking_type_id': pick_type_id,
		# 	'search_default_draft': False,
		# 	'search_default_assigned': False,
		# 	'search_default_confirmed': False,
		# 	'search_default_ready': False,
		# 	'search_default_late': False,
		# 	'search_default_available': False,
		# })
		return {
			'name': _('New Purchase Order'),
			'view_type': 'form',
			'view_mode': 'form,tree',
			'res_model': 'purchase.order',
			'res_id': new_purchase,
			'type': 'ir.actions.act_window',
			'context': ctx,
		}