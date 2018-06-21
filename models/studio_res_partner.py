from odoo import models, fields, api

class StudioResPartner(models.Model):
	_inherit = 'res.partner'

	# x_tin = fields.Char('TIN No.', required=True, store=True, copy=True)
	# x_fax = fields.Char()
	# x_account_type = fields.Selection([('direct','Direct'),('indirect','Indirect')])
	# x_industry = fields.Selection([('food','Food'),('nonfood','Non-Food'),('pharma','Pharma'),('agri','Agri'),('other','Other')])
	# x_annual_revenue = fields.Float()

	partner_supplier = fields.Boolean(string='Is a Partner Supplier')

	@api.multi
	def name_get(self):
		res = []
		for partner in self:
			name = partner.name or ''

			if partner.company_name or partner.parent_id:
				if not name and partner.type in ['invoice', 'delivery', 'other']:
					# name = dict(self.fields_get(['type'])['type']['selection'])[partner.type]
					name = "%s, %s " % (partner.city, dict(self.fields_get(['type'])['type']['selection'])[partner.type])
				if not partner.is_company:
					name = "%s, %s" % (partner.commercial_company_name or partner.parent_id.name, name)
			if self._context.get('show_address_only'):
				name = partner._display_address(without_company=True)
			if self._context.get('show_address'):
				name = name + "\n" + partner._display_address(without_company=True)
			name = name.replace('\n\n', '\n')
			name = name.replace('\n\n', '\n')
			if self._context.get('show_email') and partner.email:
				name = "%s <%s>" % (name, partner.email)
			if self._context.get('html_format'):
				name = name.replace('\n', '<br/>')
			res.append((partner.id, name))
		return res