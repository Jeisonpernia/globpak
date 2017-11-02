from odoo import models, fields, api, _ 

class StudioSalesOrder(models.Model):
	_inherit = 'sale.order'

	x_clientpo = fields.Many2one(string='Client PO No.', store=True, copy=True)