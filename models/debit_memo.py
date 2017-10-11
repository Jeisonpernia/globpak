from odoo import models, fields, api, _

class DebitMemo(models.Model):
    _name = 'account.debit.memo'
    _description = 'Debit Memo'

    name = fields.Char(string='DM #', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    # invoice_id = fields.Many2one('account.invoice', 'Invoice')
    
    @api.model
    def create(self, values):
        if values.get('name', 'New') == 'New':
            values['name'] = self.env['ir.sequence'].next_by_code('account.debit.memo') or 'New'

        result = super(DebitMemo, self).create(values)
    
        return result