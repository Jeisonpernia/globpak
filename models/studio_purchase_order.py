from odoo import models, fields, api, _

from odoo.exceptions import UserError

class PortDischarge(models.Model):
	_name = 'port.discharge'

	name = fields.Char()

class StudioPurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	@api.one
	@api.depends('order_line', 'order_line.price_subtotal')
	def _compute_amount_sales(self):
		vat_sales = 0
		vat_exempt = 0
		zero_rated = 0
		for line in self.order_line:
			if line.taxes_id:
				for tax in line.taxes_id:
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

		self.vat_sales = vat_sales
		self.vat_exempt_sales = vat_exempt
		self.zero_rated_sales = zero_rated


	@api.one
	@api.depends('order_line', 'order_line.product_id', 'order_line.price_subtotal')
	def _compute_amount_product_type(self):
		amount_services = 0
		amount_capital = 0
		amount_goods = 0
		for line in self.order_line:
			if line.product_id.type == 'service':
				amount_services += line.price_subtotal

			if line.product_id.type == 'consu' or line.product_id.type == 'product':
				amount_goods += line.price_subtotal

		self.amount_services = amount_services
		self.amount_goods = amount_goods

	x_approved_by = fields.Many2one('hr.employee', 'Approver', compute='_set_employee_details')
	x_prepared_by = fields.Many2one('res.partner', 'Prepared By', store=True, copy=True)
	x_client_id = fields.Many2one('res.partner', 'Client', compute='_get_order_details')
	x_client_billing_address = fields.Many2one('res.partner', 'Client Billing Address', compute='_get_order_details')
	x_client_delivery_address = fields.Many2one('res.partner', 'Client Delivery Address', compute='_get_order_details')
	x_client_po_no = fields.Char(string='Client PO No.', compute='_get_order_details')
	x_origin = fields.Many2one('res.country', string='Origin', store=True, copy=True)

	port_discharge = fields.Many2one('port.discharge', string='Port of Discharge')

	current_user = fields.Many2one('res.users', compute='_get_current_user')

	po_type = fields.Selection([
		('local', 'Local'),
		('import', 'Import'),
	], string='Purchase Order Type', default='local')

	vat_sales = fields.Monetary(string='Vatable Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
	vat_exempt_sales = fields.Monetary(string='Vat Exempt Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
	zero_rated_sales = fields.Monetary(string='Zero Rated Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')

	amount_services = fields.Monetary(string='Amount of Services', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')
	amount_capital = fields.Monetary(string='Amount of Capital', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')
	amount_goods = fields.Monetary(string='Amount of Goods', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')

	@api.depends('partner_id')
	def _set_employee_details(self):
		for record in self:
			job_id = self.env['hr.job'].search([('name','=','Managing Director')], limit=1)
			employee_id = self.env['hr.employee'].search([('job_id','=',job_id.id)], limit=1)
			record.x_approved_by = employee_id.id

	@api.depends()
	def _get_current_user(self):
		for rec in self:
			rec.current_user = self.env.user
		# i think this work too so you don't have to loop
		self.update({'current_user' : self.env.user.id})

	@api.onchange('po_type')
	def _onchange_potype(self):
		local_note = 'Notes: \n 1. Delivery 3 - 5 days if on-stock upon receipt of the PO, otherwise 30 - 45 day \n 2. All items are vat inclusive \n 3. Subject to (1%) creditable expanded withholding tax per RR no. 14-2008 as ammended '

		import_note = "INSTRUCTION: \n 1. Suppply material in one lot only; -5% + 0% tollerance \n 2. Indicate material grade, batch number, manufacturing in expiration date on the label. End-user Purchase Order number must appear on roll and carton labels. \n 3. All deliveries are subject to requisitioner's inspectiona and approval. \n \n ORIGINAL SHIPPING DOCUMENTS REQUIRED: \n 1. Commercial Invoice 3 copies - indicate this PO reference. \n 2. Packaging List 3 copies - indicate this PO reference. \n 3. Full set of 3 / 3 clean on board Bills of Landing. \n 4. Detailed Packaging List - 2 copies. \n 5. Certificate of Analysis - 2 copies. \n 6. Certificate of Origin - Form D - ORIGINAL & TRIPLICATE COPY \n 7. Fumigation Certificate - minimum 3 copies. "

		if self.po_type == 'local':
			self.notes = local_note

		if self.po_type == 'import':
			self.notes = import_note

	@api.multi
	def _get_order_details(self):
		for record in self:
			if record.origin:
				sale_order = self.env['sale.order'].search([('name','=',record.origin)], limit=1)
				record.x_client_id = sale_order.partner_id
				record.x_client_billing_address = sale_order.partner_invoice_id
				record.x_client_delivery_address = sale_order.partner_shipping_id
				record.x_client_po_no = sale_order.x_clientpo

	@api.model
	def create(self, values):
		result = super(StudioPurchaseOrder, self).create(values)
						
		# if values.get('x_approved_by'):
		result._add_followers()

		return result

	def _add_followers(self):
		user_ids = []
		if self.x_approved_by.user_id:
			user_ids.append(self.x_approved_by.user_id.id)
		self.message_subscribe_users(user_ids=user_ids)

	@api.multi
	def button_approve(self, force=False):
		if self.x_approved_by.user_id != self.current_user:
			raise UserError("You're not allowed to approve this purchase. Approver: %s" % (self.x_approved_by.name))
		self.write({'state': 'purchase'})
		self._create_picking()
		if self.company_id.po_lock == 'lock':
			self.write({'state': 'done'})
		return {}

	@api.multi
	def button_confirm(self):
		for order in self:
			if order.state not in ['draft', 'sent']:
				continue
			order._add_supplier_to_product()
			# Deal with double validation process
			if order.company_id.po_double_validation == 'one_step'\
					or (order.company_id.po_double_validation == 'two_step'\
						and order.amount_total < self.env.user.company_id.currency_id.compute(order.company_id.po_double_validation_amount, order.currency_id)):
				# order.button_approve()
				order.write({'state': 'purchase'})
				order._create_picking()
				if order.company_id.po_lock == 'lock':
					order.write({'state': 'done'})
			else:
				order.write({'state': 'to approve'})
		return True