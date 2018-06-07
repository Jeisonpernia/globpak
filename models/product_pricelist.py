from odoo import models, fields, api, _ 

class ProductPricelist(models.Model):
	_inherit = 'product.pricelist.item'

	location_id = fields.Many2one('res.country.state', string='Location')