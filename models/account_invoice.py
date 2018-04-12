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
                    if tax.amount == 0:
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

    @api.one
    @api.depends('invoice_line_ids', 'invoice_line_ids.product_id', 'invoice_line_ids.price_subtotal')
    def _compute_amount_product_type(self):
        amount_services = 0
        amount_capital = 0
        amount_goods = 0
        for line in self.invoice_line_ids:
            if line.product_id.type == 'service':
                amount_services += line.price_subtotal

            if line.product_id.type == 'consu' or line.product_id.type == 'product':
                amount_goods += line.price_subtotal

        self.amount_services = amount_services
        self.amount_goods = amount_goods

    @api.one
    @api.depends('amount_total', 'customs_duties', 'brokerage_fee', 'trucking_demurrage_mano', 'arrastre_storage_wharfage', 'other_charges_without_vat', 'bank_charges', 'other_charges_with_vat')
    def _compute_landed_cost(self):
        total_charges_custom = self.brokerage_fee + self.trucking_demurrage_mano + self.arrastre_storage_wharfage + self.other_charges_without_vat + self.bank_charges + self.other_charges_with_vat
        total_inland_cost = self.customs_duties + self.brokerage_fee + self.trucking_demurrage_mano + self.arrastre_storage_wharfage + self.other_charges_without_vat + self.bank_charges + self.other_charges_with_vat
        self.total_charges_custom = total_charges_custom
        self.total_inland_cost = total_inland_cost
        self.total_landed_cost = total_inland_cost + self.amount_total

    @api.one
    @api.depends('origin')
    def _compute_purchase_details(self):
        if self.origin:
            # is_purchase = False
            # x_origin = ''
            # po_type = ''
            # importation_date = ''
            
            purchase_order = self.env['purchase.order'].search([('name','=',self.origin)], limit=1)
            # if not purchase_order:
            #     for x in self.origin.split(','):
            #         origin = x.strip()
            #     purchase_order = self.env['purchase.order'].search([('name','=',origin)], limit=1)

            if purchase_order:
                self.is_purchase = True
                self.x_origin = purchase_order.x_origin
                self.po_type = purchase_order.po_type
                self.importation_date = purchase_order.date_planned

    # NEW FIELDS
    vat_sales = fields.Monetary(string='Vatable Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
    vat_exempt_sales = fields.Monetary(string='Vat Exempt Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
    zero_rated_sales = fields.Monetary(string='Zero Rated Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')

    vat_sales_signed = fields.Monetary(string='Vatable Sales Signed', store=True, readonly=True, compute='_compute_amount_sales')
    vat_exempt_sales_signed = fields.Monetary(string='Vat Exempt Sales Signed', store=True, readonly=True, compute='_compute_amount_sales')
    zero_rated_sales_signed = fields.Monetary(string='Zero Rated Sales Signed', store=True, readonly=True, compute='_compute_amount_sales')

    amount_services = fields.Monetary(string='Amount of Services', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')
    amount_capital = fields.Monetary(string='Amount of Capital', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')
    amount_goods = fields.Monetary(string='Amount of Goods', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')

    po_no = fields.Char(string='PO No.')
    dr_no = fields.Char(string='DR No.')
    dr_date = fields.Datetime(string='DR Date')

    # IMPORTATION
    is_purchase = fields.Boolean(store=True, readonly=True, compute='_compute_purchase_details')
    x_origin = fields.Many2one('res.country', string='Country of Origin', store=True, readonly=True, compute='_compute_purchase_details')
    po_type = fields.Selection([
        ('local', 'Local'),
        ('import', 'Import'),
    ], string='Purchase Order Type', default='local', store=True, readonly=True, compute='_compute_purchase_details')
    importation_date = fields.Datetime(store=True, readonly=True, compute='_compute_purchase_details')

    assessment_date = fields.Date(string='Assessment Date')
    supplier_invoice_no = fields.Char(string='Supplier Invoice No')
    bl_awb_no = fields.Char(string='BL/AWB No.')
    import_entry_no = fields.Char(string='Import Entry No.')
    lc_no = fields.Char(string='LC#')
    # Customs
    customs_duties = fields.Float(string='Duties (inc. IPF & CSF)')
    # Broker
    broker_id = fields.Many2one('res.partner', 'Broker')
    # Forwarding Charges
    brokerage_fee = fields.Float()
    trucking_demurrage_mano = fields.Float(string='Trucking / Demurrage / Mano')
    arrastre_storage_wharfage = fields.Float(string='Arrastre / Storage / Wharfage')
    other_charges_with_vat = fields.Float()
    bank_charges = fields.Float()
    other_charges_without_vat = fields.Float()

    # Totals
    total_charges_custom = fields.Float(string='Total Charges Before Release From Custom', help='Total Charges Before Release From Custom', store=True, readonly=True, compute='_compute_landed_cost')
    total_inland_cost = fields.Float(help='Custom Duties + Total Charges', store=True, readonly=True, compute='_compute_landed_cost')
    total_landed_cost = fields.Float(help='Inland Cost + Invoice Total', store=True, readonly=True, compute='_compute_landed_cost')

    # STUDIO
    x_description = fields.Text('Description', store=True, copy=True)
    x_checked_by = fields.Many2one('res.partner', 'Checked By', store=True, copy=True) 
    x_approved_by = fields.Many2one('res.partner', 'Approved By')

    # REPORTS
    # collection_receipt_id = fields.Many2one('account.collection.receipt', string='Collection Receipt')
    debit_memo_id = fields.Many2one('account.debit.memo', string='Debit Memo')
    credit_memo_id = fields.Many2one('account.credit.memo', string='Credit Memo')

    # RULES
    # is_allowed_vendor_bill_validate = fields.Boolean(compute='_compute_group')

    # OVERRIDE FIELDS
    comment = fields.Text(default="All accounts are payable on the terms stated above. Interest of 36% per annum will be charged on all overdue counts. All claims of corrections to invoice must be made within two days of receipt of goods. Parties  expressly submit to the jurisdiction of the courts of Paranaque City on any legal action arrising from this transaction and an additional sum equal to twenty-five 25 percent of the amount due will be charge for attorney's fees and other costs.")

    # @api.multi
    # def _compute_group(self):
    #     for record in self:
    #         user = self.env['res.users'].browse(self.env.uid)

    #         # Validation of Vendor Bill
    #         if record.type == 'in_invoice':
    #             if user.has_group('purchase.group_purchase_user') or user.has_group('purchase.group_purchase_manager'):
    #                 record.is_allowed_vendor_bill_validate = False
    #                 if user.has_group('account.group_account_user') or user.has_group('account.group_account_manager'):
    #                     record.is_allowed_vendor_bill_validate = True
    #         else:
    #             record.is_allowed_vendor_bill_validate = True

    @api.multi
    def action_generate_debit_memo(self):
        for record in self:
            dm_id = self.env['account.debit.memo'].create({})
            record.debit_memo_id = dm_id.id

    @api.multi
    def action_print_debit_memo(self):
        # return self.env['report'].get_action(self, 'globpak.report_debit_memo')
        return self.env.ref('globpak.account_debit_memo').report_action(self)

    @api.multi
    def action_generate_credit_memo(self):
        for record in self:
            cm_id = self.env['account.credit.memo'].create({})
            record.credit_memo_id = cm_id.id

    @api.multi
    def action_print_credit_memo(self):
        # return self.env['report'].get_action(self, 'globpak.report_credit_memo')
        return self.env.ref('globpak.account_credit_memo').report_action(self)

    @api.multi
    def action_print_account_payable_voucher(self):
        return self.env.ref('globpak.account_payable_voucher').report_action(self)

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    related_partner_id = fields.Many2one('res.partner', string='Related Vendor')
    related_partner_ref = fields.Char(string='Reference')