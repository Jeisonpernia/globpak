from odoo import models, fields

class StudioResPartner(models.Model):
	_inherit = 'res.partner'

	x_tin = fields.Char('TIN No.', required=True, store=True, copy=True)
	x_fax = fields.Char()
	x_account_type = fields.Selection([('direct','Direct'),('indirect','Indirect')])
	x_industry = fields.Selection([('food','Food'),('nonfood','Non-Food'),('pharma','Pharma'),('agri','Agri'),('other','Other')])
	x_annual_revenue = fields.Float()