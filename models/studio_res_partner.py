from odoo import models, fields, api, _ 

class StudioResPartner(models.Model):
	_inherit = 'res.partner'

	x_tin = fields.Char('TIN No.', required=True, store=True, copy=True)
	