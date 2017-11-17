from odoo import models, fields, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    collection_receipt_id = fields.Many2one('account.collection.receipt', string='Collection Receipt')
    acknowledgement_receipt_id = fields.Many2one('account.acknowledgement.receipt', string='Acknowledgement Receipt')

    @api.multi
    def action_generate_collection_receipt(self):
        for record in self:
            cr_id = self.env['account.collection.receipt'].create({})
            record.collection_receipt_id = cr_id.id

    @api.multi
    def action_print_collection_receipt(self):
        return self.env['report'].get_action(self, 'globpak.report_account_collection_receipt')

    @api.multi
    def action_generate_acknowledgement_receipt(self):
        for record in self:
            cr_id = self.env['account.acknowledgement.receipt'].create({})
            record.acknowledgement_receipt_id = cr_id.id

    @api.multi
    def action_print_acknowledgement_receipt(self):
        return self.env['report'].get_action(self, 'globpak.report_account_acknowledgement_receipt')