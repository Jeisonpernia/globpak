from odoo import models, fields, api, _

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

        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1

        self.vat_sales = vat_sales
        self.vat_exempt_sales = vat_exempt
        self.zero_rated_sales = zero_rated

        self.vat_sales_signed = vat_sales * sign
        self.vat_exempt_sales_signed = vat_exempt * sign
        self.zero_rated_sales_signed = zero_rated * sign

    # NEW FIELDS
    vat_sales = fields.Monetary(string='Vatable Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
    vat_exempt_sales = fields.Monetary(string='Vat Exempt Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
    zero_rated_sales = fields.Monetary(string='Zero Rated Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')

    vat_sales_signed = fields.Monetary(string='Vatable Sales Signed', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
    vat_exempt_sales_signed = fields.Monetary(string='Vat Exempt Sales Signed', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
    zero_rated_sales_signed = fields.Monetary(string='Zero Rated Sales Signed', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')

    po_no = fields.Char(string='PO No.')
    dr_no = fields.Char(string='DR No.')
    dr_date = fields.Datetime(string='DR Date')

    assessment_date = fields.Date(string='Assessment Date')
    supplier_invoice_no = fields.Char(string='Supplier Invoice No')
    bl_awb_no = fields.Char(string='BL/AWB No.')
    import_entry_no = fields.Char(string='Import Entry No.')
<<<<<<< HEAD
    landed_cost_line_id = fields.Many2one('account.landed.cost', 'Landed Cost')
=======
>>>>>>> 80172243da9ab8c20a53be2ffaaf0487131cbbeb

    # STUDIO
    x_description = fields.Text('Description', store=True, copy=True)
    x_checked_by = fields.Many2one('res.partner', 'Checked By', store=True, copy=True) 
    x_approved_by = fields.Many2one('res.partner', 'Approved By')

    # REPORTS
    # collection_receipt_id = fields.Many2one('account.collection.receipt', string='Collection Receipt')
    debit_memo_id = fields.Many2one('account.debit.memo', string='Debit Memo')
    credit_memo_id = fields.Many2one('account.credit.memo', string='Credit Memo')

    # OVERRIDE FIELDS
    comment = fields.Text(default="All accounts are payable on the terms stated above. Interest of 36% per annum will be charged on all overdue counts. All claims of corrections to invoice must be made within two days of receipt of goods. Parties  expressly submit to the jurisdiction of the courts of Paranaque City on any legal action arrising from this transaction and an additional sum equal to twenty-five 25 percent of the amount due will be charge for attorney's fees and other costs.")

    @api.multi
    def action_generate_debit_memo(self):
        for record in self:
            dm_id = self.env['account.debit.memo'].create({})
            record.debit_memo_id = dm_id.id

    @api.multi
    def action_print_debit_memo(self):
        return self.env['report'].get_action(self, 'globpak.report_debit_memo')

    @api.multi
    def action_generate_credit_memo(self):
        for record in self:
            cm_id = self.env['account.credit.memo'].create({})
            record.credit_memo_id = cm_id.id

    @api.multi
    def action_print_credit_memo(self):
        return self.env['report'].get_action(self, 'globpak.report_credit_memo')