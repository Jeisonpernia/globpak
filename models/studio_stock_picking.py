from odoo import models, fields, api, _ 

class StudioStockPicking(models.Model):
	_inherit = 'stock.picking'

	x_end_user_po = fields.Char('End User PO', related='purchase_id.x_client_po_no')
	x_received_by = fields.Many2one('res.partner', 'Received By', store=True, copy=True)
	x_approved_by = fields.Many2one('res.partner', 'Approved By', store=True, copy=True)