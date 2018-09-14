from odoo import models, fields, api, _
from odoo.tools.misc import formatLang, format_date

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    collection_receipt_id = fields.Many2one('account.collection.receipt', string='Collection Receipt')
    acknowledgement_receipt_id = fields.Many2one('account.acknowledgement.receipt', string='Acknowledgement Receipt')
    # vendor_bill_description = fields.Text(compute='_get_bill_details')

    # CUSTOMER PAYMENT DETAILS
    cp_cash = fields.Float(string='Cash')
    cp_check_no = fields.Char(string='Check No.')
    cp_check_date = fields.Date(string='Check Date')
    cp_bank_id = fields.Many2one('res.bank', string='Bank / Branch')
    cp_amount = fields.Monetary(string='Amount')

    @api.multi
    def action_generate_collection_receipt(self):
        for record in self:
            cr_id = self.env['account.collection.receipt'].create({})
            record.collection_receipt_id = cr_id.id

    @api.multi
    def action_print_collection_receipt(self):
        # return self.env['report'].get_action(self, 'globpak.report_account_collection_receipt')
        return self.env.ref('globpak.account_collection_receipt').report_action(self)

    @api.multi
    def action_generate_acknowledgement_receipt(self):
        for record in self:
            cr_id = self.env['account.acknowledgement.receipt'].create({})
            record.acknowledgement_receipt_id = cr_id.id

    @api.multi
    def action_print_acknowledgement_receipt(self):
        # return self.env['report'].get_action(self, 'globpak.report_account_acknowledgement_receipt')
        return self.env.ref('globpak.account_acknowledgement_receipt').report_action(self)

    # @api.multi
    # def _get_bill_details(self):
    #     for record in self:
    #         description = ''
    #         for invoice in record.invoice_ids:
    #             if invoice.x_description:
    #                 description += invoice.x_description
    #                 description += " \n"
    #         record.vendor_bill_description = description

    def make_stub_line(self, invoice):
        """ Return the dict used to display an invoice/refund in the stub
        """
        # Find the account.partial.reconcile which are common to the invoice and the payment
        if invoice.type in ['in_invoice', 'out_refund']:
            invoice_sign = 1
            invoice_payment_reconcile = invoice.move_id.line_ids.mapped('matched_debit_ids').filtered(lambda r: r.debit_move_id in self.move_line_ids)
        else:
            invoice_sign = -1
            invoice_payment_reconcile = invoice.move_id.line_ids.mapped('matched_credit_ids').filtered(lambda r: r.credit_move_id in self.move_line_ids)

        if self.currency_id != self.journal_id.company_id.currency_id:
            amount_paid = abs(sum(invoice_payment_reconcile.mapped('amount_currency')))
        else:
            amount_paid = abs(sum(invoice_payment_reconcile.mapped('amount')))

        amount_residual = invoice_sign * invoice.residual

        description = invoice.x_description
        # if not description:
        #     description = invoice.reference and invoice.number + ' - ' + invoice.reference or invoice.number

        return {
            'due_date': format_date(self.env, invoice.date_due),
            # 'number': invoice.reference and invoice.number + ' - ' + invoice.reference or invoice.number,
            'number': description,
            'amount_total': formatLang(self.env, invoice_sign * invoice.amount_total, currency_obj=invoice.currency_id),
            'amount_residual': formatLang(self.env, amount_residual, currency_obj=invoice.currency_id) if amount_residual*10**4 != 0 else '-',
            'amount_paid': formatLang(self.env, invoice_sign * amount_paid, currency_obj=invoice.currency_id),
            'currency': invoice.currency_id,
        }
