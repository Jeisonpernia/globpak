from odoo import models, fields, api

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('invoice_line_ids', 'invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount_sales(self):
        vat_sales = 0
        vat_exempt = 0
        zero_rated = 0
        for line in self.invoice_line_ids:
            if line.invoice_line_tax_ids:
                for tax in line.invoice_line_tax_ids:
                    # Check if zero rated sales or vatable sales
                    if tax.amount <= 0:
                        # Zero Rated Sales
                        zero_rated += line.price_subtotal
                    else:
                        # Vatable Sales
                        vat_sales += line.price_subtotal
            else:
                # Vat Exempt Sales
                vat_exempt += line.price_subtotal
        self.vat_sales = vat_sales
        self.vat_exempt_sales = vat_exempt
        self.zero_rated_sales = zero_rated

    vat_sales = fields.Monetary(string='Vatable Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
    vat_exempt_sales = fields.Monetary(string='Vat Exempt Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
    zero_rated_sales = fields.Monetary(string='Vat Exempt Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')

    po_no = fields.Char(string='PO No.')
    dr_no = fields.Char(string='DR No.')
    dr_date = fields.Datetime(string='DR Date')
