from odoo import models, fields, api, _

class AccountTax(models.Model):
    _inherit = 'account.tax'
    _description = 'Extend Tax to Add EWT Sturcture'

    ewt_structure_id = fields.Many2one('account.ewt.structure', string='EWT Structure')