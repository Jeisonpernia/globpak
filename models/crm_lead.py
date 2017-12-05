from odoo import models, fields, api

class CrmLead(models.Model):
	_inherit = 'crm.lead'

	fax = fields.Char('Fax')

	account_type = fields.Selection([
		('direct','Direct'),
		('indirect','Indirect'),
	], string='Account Type')

	industry = fields.Selection([
		('food','Food'),
		('nonfood','Non-Food'),
		('pharma','Pharma'),
		('agri','Agri'),
		('other','Other'),
	])

	annual_revenue = fields.Float('Annual Revenue')