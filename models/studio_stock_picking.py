from odoo import models, fields, api, _ 

class StudioStockPicking(models.Model):
	_inherit = 'stock.picking'

	# x_end_user_po = fields.Char('End User PO', related='purchase_id.x_client_po_no')
	x_end_user_po = fields.Char('End User PO', compute='_get_source_details')
	x_client_billing_address = fields.Many2one('res.partner', 'Client Billing Address', compute='_get_source_details')
	x_client_delivery_address = fields.Many2one('res.partner', 'Client Delivery Address', compute='_get_source_details')
	x_received_by = fields.Many2one('res.partner', 'Received By', store=True, copy=True)
	x_approved_by = fields.Many2one('res.partner', 'Approved By', store=True, copy=True)

	@api.multi
	def _get_source_details(self):
		for record in self:
			if record.purchase_id:
				record.x_end_user_po = record.purchase_id.x_client_po_no
				record.x_client_billing_address = record.purchase_id.x_client_billing_address
				record.x_client_delivery_address = record.purchase_id.x_client_delivery_address

			if record.sale_id:
				record.x_end_user_po = record.sale_id.x_clientpo
				record.x_client_billing_address = record.sale_id.partner_invoice_id
				record.x_client_delivery_address = record.sale_id.partner_shipping_id
