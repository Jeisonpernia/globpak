from odoo import models, fields, api, _

class CreditMemo(models.Model):
    _name = 'account.credit.memo'
    _description = 'Credit Memo'

    name = fields.Char(string='CM #', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    # invoice_id = fields.Many2one('account.invoice', 'Invoice')
    
    @api.model
    def create(self, values):
        if values.get('name', 'New') == 'New':
            values['name'] = self.env['ir.sequence'].next_by_code('account.credit.memo') or 'New'

        result = super(CreditMemo, self).create(values)
    
        return result