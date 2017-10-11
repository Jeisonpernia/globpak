from odoo import models, fields, api, _

class AcknowledgementReceipt(models.Model):
    _name = 'account.acknowledgement.receipt'
    _decription = 'Acknowledgement Receipt'

    name = fields.Char(string='AR #', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))

    @api.model
    def create(self, values):
        if values.get('name', 'New') == 'New':
            values['name'] = self.env['ir.sequence'].next_by_code('account.acknowledgement.receipt') or 'New'

        result = super(AcknowledgementReceipt, self).create(values)
    
        return result