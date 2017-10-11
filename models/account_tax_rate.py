from odoo import models, fields, api, _

class TaxRate(models.Model):
    _name = 'account.tax.rate'
    _description = 'Withholding Tax Rates'

    name = fields.Char(string='ATC Code')
    type = fields.Selection([
        ('we', 'WE'),
    ], string='Tax Type')
    description = fields.Text()
    amount = fields.Float()