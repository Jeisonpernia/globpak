from odoo import models, fields, api, _

from odoo.exceptions import UserError

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
	def _compute_order_details(self):
		if self.origin:

			# PURCHASE
			purchase_order = self.env['purchase.order'].search([('name','=',self.origin)], limit=1)
			if purchase_order:
				self.is_purchase = True
				self.x_origin = purchase_order.x_origin
				self.po_type = purchase_order.po_type
				self.importation_date = purchase_order.date_planned

			# SALES
			sale_order = self.env['sale.order'].search([('name','=',self.origin)], limit=1)
			if sale_order:
				self.po_no = sale_order.x_clientpo

				invoiced_quantities = 0
				for line in self.invoice_line_ids:
					invoiced_quantities += line.quantity

				delivery = False
				for pick in sale_order.picking_ids:
					if pick.state == 'done':
						delivered_quantities = 0
						for line in pick.move_lines:
							delivered_quantities += line.quantity_done
						if invoiced_quantities == delivered_quantities:
							delivery = pick
							continue

				if delivery == False:
					delivered_quantities = 0
					
					for pick in sale_order.picking_ids:
						if pick.state == 'done':
							for line in pick.move_lines:
								delivered_quantities += line.quantity_done
					
					if invoiced_quantities == delivered_quantities:
						delivery = pick
				if delivery:
					self.dr_no = delivery.name
					self.dr_date = delivery.scheduled_date

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

	po_no = fields.Char(string='PO No.', compute='_compute_order_details')
	dr_no = fields.Char(string='DR No.', compute='_compute_order_details')
	dr_date = fields.Datetime(string='DR Date', compute='_compute_order_details')

	# IMPORTATION
	is_purchase = fields.Boolean(store=True, readonly=True, compute='_compute_order_details')
	x_origin = fields.Many2one('res.country', string='Country of Origin', store=True, readonly=True, compute='_compute_order_details')
	po_type = fields.Selection([
		('local', 'Local'),
		('import', 'Import'),
	], string='Purchase Order Type', default='local', store=True, readonly=True, compute='_compute_order_details')
	importation_date = fields.Datetime(store=True, readonly=True, compute='_compute_order_details')

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
	comment = fields.Text(default="All accounts are payable on the terms stated above. Interest of 36% per annum will be charged on all overdue counts. All claims of corrections to invoice must be made within two days of receipt of goods. Parties  expressly submit to the jurisdiction of the courts of Paranaque City on any legal action arising from this transaction and an additional sum equal to twenty-five 25 percent of the amount due will be charge for attorney's fees and other costs.")

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

	@api.model
	def create(self, values):
		
		if values.get('comment'):
			values['comment'] = "All accounts are payable on the terms stated above. Interest of 36% per annum will be charged on all overdue counts. All claims of corrections to invoice must be made within two days of receipt of goods. Parties  expressly submit to the jurisdiction of the courts of Paranaque City on any legal action arising from this transaction and an additional sum equal to twenty-five 25 percent of the amount due will be charge for attorney's fees and other costs."

		result = super(AccountInvoice, self).create(values)
		
		return result

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

# class SaleAdvancePaymentInv(models.TransientModel):
# 	_inherit = "sale.advance.payment.inv"

# 	@api.multi
# 	def _create_invoice(self, order, so_line, amount):
# 		inv_obj = self.env['account.invoice']
# 		ir_property_obj = self.env['ir.property']

# 		account_id = False
# 		if self.product_id.id:
# 			account_id = self.product_id.property_account_income_id.id
# 		if not account_id:
# 			inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
# 			account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
# 		if not account_id:
# 			raise UserError(
# 				_('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') %
# 				(self.product_id.name,))

# 		if self.amount <= 0.00:
# 			raise UserError(_('The value of the down payment amount must be positive.'))
# 		if self.advance_payment_method == 'percentage':
# 			amount = order.amount_untaxed * self.amount / 100
# 			name = _("Down payment of %s%%") % (self.amount,)
# 		else:
# 			amount = self.amount
# 			name = _('Down Payment')
# 		taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
# 		if order.fiscal_position_id and taxes:
# 			tax_ids = order.fiscal_position_id.map_tax(taxes).ids
# 		else:
# 			tax_ids = taxes.ids

# 		invoice = inv_obj.create({
# 			'name': order.client_order_ref or order.name,
# 			'origin': order.name,
# 			'type': 'out_invoice',
# 			'reference': False,
# 			'account_id': order.partner_id.property_account_receivable_id.id,
# 			'partner_id': order.partner_invoice_id.id,
# 			'partner_shipping_id': order.partner_shipping_id.id,
# 			'invoice_line_ids': [(0, 0, {
# 				'name': name,
# 				'origin': order.name,
# 				'account_id': account_id,
# 				'price_unit': amount,
# 				'quantity': 1.0,
# 				'discount': 0.0,
# 				'uom_id': self.product_id.uom_id.id,
# 				'product_id': self.product_id.id,
# 				'sale_line_ids': [(6, 0, [so_line.id])],
# 				'invoice_line_tax_ids': [(6, 0, tax_ids)],
# 				'account_analytic_id': order.analytic_account_id.id or False,
# 			})],
# 			'currency_id': order.pricelist_id.currency_id.id,
# 			'payment_term_id': order.payment_term_id.id,
# 			'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
# 			'team_id': order.team_id.id,
# 			'user_id': order.user_id.id,
# 			# 'comment': order.note,
# 		})
# 		invoice.compute_taxes()
# 		invoice.message_post_with_view('mail.message_origin_link',
# 					values={'self': invoice, 'origin': order},
# 					subtype_id=self.env.ref('mail.mt_note').id)
# 		return invoice