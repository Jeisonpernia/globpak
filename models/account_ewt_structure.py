from odoo import models, fields, api, _

class EwtStructure(models.Model):
    _name = 'account.ewt.structure'
    _description = 'Withholding Tax Rates Structure'

    name = fields.Char(string='ATC Code')
    description = fields.Text()
    tax_type = fields.Char()
    tax_rate = fields.Float()
    bir_form = fields.Char(string='BIR Form')