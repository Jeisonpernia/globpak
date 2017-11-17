from odoo import models, fields, api, _

class CollectionReceipt(models.Model):
    _name = 'account.collection.receipt'
    _description = 'Collection Receipt'

    name = fields.Char(string='CR #', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    # invoice_id = fields.Many2one('account.invoice', 'Invoice')
    
    @api.model
    def create(self, values):
        if values.get('name', 'New') == 'New':
            values['name'] = self.env['ir.sequence'].next_by_code('account.collection.receipt') or 'New'

        result = super(CollectionReceipt, self).create(values)
    
        return result