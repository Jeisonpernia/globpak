from odoo import models, fields, api, _ 

class StudioAccountInvoice(models.Model):
	_inherit = 'account.invoice'

	x_checked_by = fields.Many2one('res.partner', 'Checked By', store=True, copy=True)
	x_description = fields.Text('Description', store=True, copy=True)