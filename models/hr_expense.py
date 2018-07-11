from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

from odoo.exceptions import UserError
from odoo.exceptions import ValidationError

import logging
_logger = logging.getLogger(__name__)

class HrExpenseSheet(models.Model):
	_inherit = 'hr.expense.sheet'

	# NEW FIELDS
	x_checked_by = fields.Many2one('res.partner', string="Checked By")
	x_approved_by = fields.Many2one('res.partner', string="Approved By")
	untaxed_amount = fields.Float(string='Subtotal', store=True, compute='_compute_amount_untaxed', digits=dp.get_precision('Account'))
	approver_id = fields.Many2one('hr.employee','Approver', store=True, required=True)
	current_user = fields.Many2one('res.users', compute='_get_current_user')
	reimbursement_mode = fields.Selection([
		('petty_cash', 'Petty Cash'),
		('reimbursement', 'Reimbursement'),
		('cash_advance', 'Liquidation for Cash Advance'),
		('credit_card', 'Credit Card Expenses'),
	], string='Reimbursement Mode', default='petty_cash', readonly=True, states={'submit': [('readonly', False)], 'cancel': [('readonly', False)]})

	# OVERRIDE FIELDS
	payment_mode = fields.Selection([
		("own_account", "Employee (to reimburse)"),
		("company_account", "Company"),
	])
	expense_line_ids = fields.One2many('hr.expense', 'sheet_id', string='Expense Lines', states={'approve': [('readonly', True)], 'done': [('readonly', True)], 'post': [('readonly', True)]}, copy=False)

	# OVERRIDE ACTION
	@api.multi
	def check_consistency(self):

		# if any(sheet.employee_id != self[0].fund_custodian_id for sheet in self):
		# 	raise UserError(_("Expenses must belong to the same Employee."))

		expense_lines = self.mapped('expense_line_ids')
		if expense_lines and any(expense.payment_mode != expense_lines[0].payment_mode for expense in expense_lines):
			raise UserError(_("Expenses must have been paid by the same entity (Company or employee)"))

	# @api.model
	# def create(self, vals):
	# 	# Add the followers at creation, so they can be notified
	# 	if vals.get('employee_id'):
	# 		employee = self.env['hr.employee'].browse(vals['employee_id'])
	# 		users = self._get_users_to_subscribe(employee=employee) - self.env.user
	# 		vals['message_follower_ids'] = []
	# 		for partner in users.mapped('partner_id'):
	# 			vals['message_follower_ids'] += self.env['mail.followers']._add_follower_command(self._name, [], {partner.id: None}, {})[0]
	# 	sheet = super(HrExpenseSheet, self).create(vals)
	# 	# self.check_consistency()
	# 	return sheet

	# @api.multi
	# def write(self, vals):
	# 	res = super(HrExpenseSheet, self).write(vals)
	# 	# self.check_consistency()
	# 	if vals.get('employee_id'):
	# 		self._add_followers()
	# 	return res

	@api.one
	@api.constrains('expense_line_ids')
	def _check_employee(self):

		fund_custodian_ids = self.expense_line_ids.mapped('fund_custodian_id')
		employee_ids = self.expense_line_ids.mapped('employee_id')

		if self.reimbursement_mode == 'petty_cash':
			if len(fund_custodian_ids) > 1 or (len(fund_custodian_ids) == 1 and fund_custodian_ids != self.employee_id):
				raise ValidationError(_('You cannot add expense lines of another fund custodian.'))
		else:
			if len(employee_ids) > 1 or (len(employee_ids) == 1 and employee_ids != self.employee_id):
				raise ValidationError(_('You cannot add expense lines of another employee.'))

	# NEW ACTION
	@api.one
	@api.depends('expense_line_ids', 'expense_line_ids.untaxed_amount')
	def _compute_amount_untaxed(self):
		self.untaxed_amount = sum(self.expense_line_ids.mapped('untaxed_amount'))

	# @api.depends('employee_id')
	# def _set_employee_details(self):
	# 	for ob in self:
	# 		ob.approver_id = ob.employee_id.parent_id

	@api.onchange('employee_id')
	def _set_employee_details(self):
		self.approver_id = self.employee_id.parent_id

	@api.depends()
	def _get_current_user(self):
		for rec in self:
			rec.current_user = self.env.uid

	@api.multi
	def approve_expense_sheets(self): # RETURN
		user = self.env['res.users'].sudo().browse(self.env.uid)
		for record in self:
			if not user.has_group('account.group_account_user'):
				raise UserError(_("You cannot validate this expense report. Only accounting users are allowed to approve/refuse expense report."))

		# APPROVE
		self.write({'state': 'approve', 'responsible_id': self.env.user.id})

	@api.multi
	def refuse_sheet(self, reason):
		user = self.env['res.users'].sudo().browse(self.env.uid)
		for record in self:
			if not user.has_group('account.group_account_user'):
				raise UserError(_("You cannot validate this expense report. Only accounting users are allowed to approve/refuse expense report."))

		# REFUSE
		self.write({'state': 'cancel', 'responsible_id': self.env.user.id})
		for sheet in self:
			sheet.message_post_with_view('hr_expense.hr_expense_template_refuse_reason', values={'reason': reason ,'is_sheet':True ,'name':self.name})

	@api.multi
	def get_tax_details(self, line, tax):
		currency = self.currency_id or self.company_id.currency_id
		amount = tax.compute_all(line.price_unit, currency, line.quantity, line.product_id, line.employee_id.user_id.partner_id)['taxes'][0]['amount']
		return amount

	# def _get_users_to_subscribe(self, employee=False):
	# 	users = self.env['res.users']
	# 	employee = employee or self.employee_id
	# 	if employee.user_id:
	# 		users |= employee.user_id
	# 	if employee.parent_id:
	# 		users |= employee.parent_id.user_id
	# 	if employee.department_id and employee.department_id.manager_id and employee.parent_id != employee.department_id.manager_id:
	# 		users |= employee.department_id.manager_id.user_id
	# 	return users

class HrExpenseTax(models.Model):
	_name = "hr.expense.tax"
	_description = "HR Expense Tax"
	_order = 'sequence'

	def _compute_base_amount(self):
		tax_grouped = {}
		for expense in self.mapped('expense_id'):
			tax_grouped[expense.id] = expense.get_taxes_values()
		for tax in self:
			tax.base = 0.0
			if tax.tax_id:
				key = tax.tax_id.get_grouping_key({
					'tax_id': tax.tax_id.id,
					'account_id': tax.account_id.id,
					'account_analytic_id': tax.account_analytic_id.id,
				})
				if tax.expense_id and key in tax_grouped[tax.expense_id.id]:
					tax.base = tax_grouped[tax.expense_id.id][key]['base']
				else:
					_logger.warning('Tax Base Amount not computable probably due to a change in an underlying tax (%s).', tax.tax_id.name)

	expense_id = fields.Many2one('hr.expense', string='Expense', ondelete='cascade', index=True)
	name = fields.Char(string='Tax Description', required=True)
	tax_id = fields.Many2one('account.tax', string='Tax', ondelete='restrict')
	account_id = fields.Many2one('account.account', string='Tax Account', required=True, domain=[('deprecated', '=', False)])
	account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account')
	amount = fields.Monetary()
	manual = fields.Boolean(default=True)
	sequence = fields.Integer(help="Gives the sequence order when displaying a list of expense tax.")
	company_id = fields.Many2one('res.company', string='Company', related='account_id.company_id', store=True, readonly=True)
	currency_id = fields.Many2one('res.currency', related='expense_id.currency_id', store=True, readonly=True)
	base = fields.Monetary(string='Base', compute='_compute_base_amount')

class HrExpenseLine(models.Model):
	_name = 'hr.expense.line'
	_description = 'HR Expense Line'

	@api.one
	@api.depends('untaxed_amount', 'tax_ids')
	def _compute_amount_sales(self):
		vat_sales = 0
		vat_exempt = 0
		zero_rated = 0
		is_recompute_base = False
		if self.tax_ids:
			for tax in self.tax_ids:
				# Check if zero rated sales or vatable sales
				if tax.amount == 0:
					# Zero Rated Sales
					zero_rated += self.untaxed_amount
				else:
					# Vatable Sales
					vat_sales += self.untaxed_amount

				# RECOMPUTE BASE
				if tax.amount_type == 'base_deduction':
					is_recompute_base = True

		else:
			# Vat Exempt Sales
			vat_exempt += self.untaxed_amount

		self.vat_sales = vat_sales
		self.vat_exempt_sales = vat_exempt
		self.zero_rated_sales = zero_rated
		self.is_recompute_base = is_recompute_base
	
	name = fields.Text(string='Description', required=True)
	product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', index=True, domain=[('can_be_expensed', '=', True)], required=True)
	uom_id = fields.Many2one('product.uom', string='Unit of Measure', ondelete='set null', index=True, oldname='uos_id')
	quantity = fields.Float(default=1.00)
	price_unit = fields.Float(string='Price Unit')
	tax_ids = fields.Many2many('account.tax', 'expense_line_tax', 'expense_line_id', 'tax_id', string='Taxes')

	untaxed_amount = fields.Float(string='Subtotal', store=True, compute='_compute_amount', digits=dp.get_precision('Account'))
	tax_amount = fields.Float(string='Tax Amount', store=True, compute='_compute_amount', digits=dp.get_precision('Account'))
	total_amount = fields.Float(string='Total', store=True, compute='_compute_amount', digits=dp.get_precision('Account'))

	vat_sales = fields.Monetary(string='Vatable Sales', store=True, readonly=True, compute='_compute_amount_sales')
	vat_exempt_sales = fields.Monetary(string='Vat Exempt Sales', store=True, readonly=True, compute='_compute_amount_sales')
	zero_rated_sales = fields.Monetary(string='Zero Rated Sales', store=True, readonly=True, compute='_compute_amount_sales')

	allowed_expense_amount = fields.Monetary('Allowed Expense Amount')
	is_recompute_base = fields.Boolean(string='Recompute Base', compute='_compute_amount_sales')

	expense_id = fields.Many2one('hr.expense', string="Expense", readonly=True, copy=False)
	partner_id = fields.Many2one('res.partner', 'Vendor')
	reference = fields.Char(string='Receipt #')
	# date = fields.Date(compute='_compute_date', inverse='_compute_date_inverse', store=True)
	date = fields.Date(store=True)
	
	employee_id = fields.Many2one('hr.employee', string="Employee", compute='_compute_employee', store=True)
	account_id = fields.Many2one('account.account', string='Account', states={'post': [('readonly', True)], 'done': [('readonly', True)]}, default=lambda self: self.env['ir.property'].get('property_account_expense_categ_id', 'product.category'))
	company_id = fields.Many2one('res.company', string='Company', related='expense_id.company_id', store=True, readonly=True)
	currency_id = fields.Many2one('res.currency', related='expense_id.currency_id', store=True, readonly=True)
	account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account', compute='_compute_analytic', store=True)

	state = fields.Selection([
		('draft', 'To Submit'),
		('confirm', 'Pending'),
		('validate', 'Approved'),
		('reported', 'Reported'),
		('done', 'Posted'),
		('refused', 'Refused'),
	], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True, help="Status of the expense.")

	reimbursement_mode = fields.Selection([
		('petty_cash', 'Petty Cash'),
		('reimbursement', 'Reimbursement'),
		('cash_advance', 'Liquidation for Cash Advance'),
		('credit_card', 'Credit Card Expenses'),
	], string='Reimbursement Mode', compute='_compute_mode')

	@api.depends('expense_id', 'expense_id.state')
	def _compute_state(self):
		for expense in self:
			if expense.expense_id.state == "draft":
				expense.state = "draft"
			elif expense.expense_id.state == "confirm":
				expense.state = "confirm"
			elif expense.expense_id.state == "validate":
				expense.state = "validate"
			elif expense.expense_id.state == "reported":
				expense.state = "reported"
			elif expense.expense_id.state == "done":
				expense.state = "done"
			else:
				expense.state = "refused"

	@api.depends('expense_id', 'expense_id.reimbursement_mode')
	def _compute_mode(self):
		for expense in self:
			if expense.expense_id.reimbursement_mode == "petty_cash":
				expense.reimbursement_mode = "petty_cash"
				# expense.date = expense.expense_id.date
			
			if expense.expense_id.reimbursement_mode == "reimbursement":
				expense.reimbursement_mode = "reimbursement"
			
			if expense.expense_id.reimbursement_mode == "cash_advance":
				expense.reimbursement_mode = "cash_advance"
			
			if expense.expense_id.reimbursement_mode == "credit_card":
				expense.reimbursement_mode = "credit_card"
	
	@api.depends('quantity', 'price_unit', 'tax_ids', 'currency_id')
	def _compute_amount(self):
		for expense in self:
			taxes = expense.tax_ids.compute_all(expense.price_unit, expense.currency_id, expense.quantity, expense.product_id, expense.employee_id.user_id.partner_id)
			tax_amount = taxes.get('total_included') - taxes.get('total_excluded')

			untaxed_amount = expense.price_unit * expense.quantity
			total_amount = taxes.get('total_included')
			
			if expense.is_recompute_base == True:
				untaxed_amount = (expense.price_unit * expense.quantity) - tax_amount
				total_amount = (expense.price_unit * expense.quantity)

			if expense.allowed_expense_amount > 0:
				untaxed_amount = expense.allowed_expense_amount - tax_amount
				total_amount = expense.allowed_expense_amount

			expense.tax_amount = tax_amount
			expense.untaxed_amount = untaxed_amount
			expense.total_amount = total_amount

	# @api.depends('expense_id', 'expense_id.date')
	# def _compute_date(self):
	# 	for expense in self:
	# 		if expense.reimbursement_mode == 'petty_cash':
	# 			expense.date = expense.expense_id.date

	@api.depends('expense_id', 'expense_id.employee_id')
	def _compute_employee(self):
		for expense in self:
			expense.employee_id = expense.expense_id.employee_id

	@api.depends('expense_id', 'expense_id.analytic_account_id')
	def _compute_analytic(self):
		for expense in self:
			expense.account_analytic_id = expense.expense_id.analytic_account_id

	@api.onchange('product_id')
	def _onchange_product_id(self):
		if self.product_id:
			if not self.name:
				self.name = self.product_id.display_name or ''
			self.price_unit = self.product_id.price_compute('standard_price')[self.product_id.id]
			self.uom_id = self.product_id.uom_id
			self.tax_ids = self.product_id.supplier_taxes_id
			account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
			if account:
				self.account_id = account

	def _prepare_move_line(self, line):
		'''
		This function prepares move line of account.move related to an expense
		'''

		# if self.expense_id.reimbursement_mode == 'petty_cash':
		partner_id = self.expense_id.fund_custodian_id.address_home_id.commercial_partner_id.id
		# else:
		# partner_id = self.employee_id.address_home_id.commercial_partner_id.id

		return {
			'date_maturity': line.get('date_maturity'),
			'partner_id': partner_id,
			'name': line['name'][:64],
			'debit': line['price'] > 0 and line['price'],
			'credit': line['price'] < 0 and - line['price'],
			'account_id': line['account_id'],
			'analytic_line_ids': line.get('analytic_line_ids'),
			'amount_currency': line['price'] > 0 and abs(line.get('amount_currency')) or - abs(line.get('amount_currency')),
			# 'amount_currency': line.get('amount_currency'),
			'currency_id': line.get('currency_id'),
			'tax_line_id': line.get('tax_line_id'),
			'tax_ids': line.get('tax_ids'),
			'quantity': line.get('quantity', 1.00),
			'product_id': line.get('product_id'),
			'product_uom_id': line.get('uom_id'),
			'analytic_account_id': line.get('analytic_account_id'),
			'payment_id': line.get('payment_id'),
			'expense_id': line.get('expense_id'),
		}
	
	@api.multi
	def _compute_expense_totals(self, company_currency, account_move_lines, move_date):
		'''
		internal method used for computation of total amount of an expense in the company currency and
		in the expense currency, given the account_move_lines that will be created. It also do some small
		transformations at these account_move_lines (for multi-currency purposes)

		:param account_move_lines: list of dict
		:rtype: tuple of 3 elements (a, b ,c)
		a: total in company currency
		b: total in hr.expense currency
		c: account_move_lines potentially modified
		'''

		self.ensure_one()
		total = 0.0
		total_currency = 0.0
		for line in account_move_lines:
			line['currency_id'] = False
			line['amount_currency'] = False
			if self.currency_id != company_currency:
				line['currency_id'] = self.currency_id.id
				line['amount_currency'] = line['price']
				line['price'] = self.currency_id.with_context(date=move_date or fields.Date.context_today(self)).compute(line['price'], company_currency)
			total -= line['price']
			total_currency -= line['amount_currency'] or line['price']
		return total, total_currency, account_move_lines
			
	@api.multi
	def action_move_create(self):
		'''
		main function that is called when trying to create the accounting entries related to an expense
		'''
		move_group_by_sheet = {}
		for expense in self:
			journal = expense.expense_id.sheet_id.bank_journal_id if expense.expense_id.payment_mode == 'company_account' else expense.expense_id.sheet_id.journal_id
			#create the move that will contain the accounting entries
			acc_date = expense.expense_id.sheet_id.accounting_date or expense.expense_id.date
			if not expense.expense_id.sheet_id.id in move_group_by_sheet:
				move = self.env['account.move'].create({
					'journal_id': journal.id,
					'company_id': self.env.user.company_id.id,
					'date': acc_date,
					'ref': expense.expense_id.sheet_id.name,
					# force the name to the default value, to avoid an eventual 'default_name' in the context
					# to set it to '' which cause no number to be given to the account.move when posted.
					'name': '/',
				})
				move_group_by_sheet[expense.expense_id.sheet_id.id] = move
			else:
				move = move_group_by_sheet[expense.expense_id.sheet_id.id]
			company_currency = expense.expense_id.company_id.currency_id
			diff_currency_p = expense.expense_id.currency_id != company_currency
			#one account.move.line per expense (+taxes..)
			move_lines = expense._move_line_get()

			#create one more move line, a counterline for the total on payable account
			payment_id = False
			total, total_currency, move_lines = expense._compute_expense_totals(company_currency, move_lines, acc_date)
			if expense.expense_id.payment_mode == 'company_account':
				if not expense.expense_id.sheet_id.bank_journal_id.default_credit_account_id:
					raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.expense_id.sheet_id.bank_journal_id.name))
				emp_account = expense.expense_id.sheet_id.bank_journal_id.default_credit_account_id.id
				journal = expense.expense_id.sheet_id.bank_journal_id
				#create payment
				payment_methods = (total < 0) and journal.outbound_payment_method_ids or journal.inbound_payment_method_ids
				journal_currency = journal.currency_id or journal.company_id.currency_id
				payment = self.env['account.payment'].create({
					'payment_method_id': payment_methods and payment_methods[0].id or False,
					'payment_type': total < 0 and 'outbound' or 'inbound',
					'partner_id': expense.expense_id.employee_id.address_home_id.commercial_partner_id.id,
					'partner_type': 'supplier',
					'journal_id': journal.id,
					'payment_date': expense.expense_id.date,
					'state': 'reconciled',
					'currency_id': diff_currency_p and expense.expense_id.currency_id.id or journal_currency.id,
					'amount': diff_currency_p and abs(total_currency) or abs(total),
					'name': expense.expense_id.name,
				})
				payment_id = payment.id
			else:
				# if expense.expense_id.reimbursement_mode == 'petty_cash':
				if not expense.expense_id.fund_custodian_id.address_home_id:
					raise UserError(_("No Home Address found for the fund custodian %s, please configure one.") % (expense.expense_id.fund_custodian_id.name))
				emp_account = expense.expense_id.fund_custodian_id.address_home_id.property_account_payable_id.id
				# else:
				# if not expense.expense_id.employee_id.address_home_id:
					# raise UserError(_("No Home Address found for the employee %s, please configure one.") % (expense.expense_id.employee_id.name))
				# emp_account = expense.expense_id.employee_id.address_home_id.property_account_payable_id.id

			aml_name = expense.expense_id.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
			move_lines.append({
					'type': 'dest',
					'name': aml_name,
					'price': total,
					'account_id': emp_account,
					'date_maturity': acc_date,
					'amount_currency': diff_currency_p and total_currency or False,
					'currency_id': diff_currency_p and expense.currency_id.id or False,
					'payment_id': payment_id,
					'expense_id': expense.expense_id.id,
					})

			#convert eml into an osv-valid format
			lines = [(0, 0, expense._prepare_move_line(x)) for x in move_lines]
			move.with_context(dont_create_taxes=True).write({'line_ids': lines})
			expense.expense_id.sheet_id.write({'account_move_id': move.id})
			if expense.expense_id.payment_mode == 'company_account':
				expense.sheet_id.paid_expense_sheets()
		for move in move_group_by_sheet.values():
			move.post()
		return True

	@api.multi
	def _prepare_move_line_value(self):
		self.ensure_one()
		if self.account_id:
			account = self.account_id
		elif self.product_id:
			account = self.product_id.product_tmpl_id._get_product_accounts()['expense']
			if not account:
				raise UserError(
					_("No Expense account found for the product %s (or for its category), please configure one.") % (self.product_id.name))
		else:
			account = self.env['ir.property'].with_context(force_company=self.company_id.id).get('property_account_expense_categ_id', 'product.category')
			if not account:
				raise UserError(
					_('Please configure Default Expense account for Product expense: `property_account_expense_categ_id`.'))
		aml_name = self.expense_id.employee_id.name + ': ' + self.name.split('\n')[0][:64]
		move_line = {
			'type': 'src',
			'name': aml_name,
			'price_unit': self.price_unit,
			'quantity': self.quantity,
			'price': self.total_amount,
			'account_id': account.id,
			'product_id': self.product_id.id,
			'uom_id': self.uom_id.id,
			'analytic_account_id': self.account_analytic_id.id,
			'expense_id': self.expense_id.id,
		}
		return move_line
	
	@api.multi
	def _move_line_get(self):
		account_move = []
		for expense in self:
			move_line = expense._prepare_move_line_value()
			account_move.append(move_line)

			# Calculate tax lines and adjust base line
			taxes = expense.tax_ids.with_context(round=True).compute_all(expense.price_unit, expense.currency_id, expense.quantity, expense.product_id)
			account_move[-1]['price'] = taxes['total_excluded']
			account_move[-1]['tax_ids'] = [(6, 0, expense.tax_ids.ids)]
			for tax in taxes['taxes']:
				account_move.append({
					'type': 'tax',
					'name': tax['name'],
					'price_unit': tax['amount'],
					'quantity': 1,
					'price': tax['amount'],
					'account_id': tax['account_id'] or move_line['account_id'],
					'tax_line_id': tax['id'],
					'expense_id': expense.expense_id.id,
				})
		return account_move

class HrExpense(models.Model):
	_inherit = 'hr.expense'

	@api.one
	@api.depends('line_ids', 'line_ids.untaxed_amount')
	def _compute_amount_sales(self):
		vat_sales = 0
		vat_exempt = 0
		zero_rated = 0
		for line in self.line_ids:
			if line.tax_ids:
				for tax in line.tax_ids:
					# Check if zero rated sales or vatable sales
					if tax.amount == 0:
						# Zero Rated Sales
						zero_rated += line.untaxed_amount
					else:
						# Vatable Sales
						vat_sales += line.untaxed_amount
			else:
				# Vat Exempt Sales
				vat_exempt += line.untaxed_amount

		self.vat_sales = vat_sales
		self.vat_exempt_sales = vat_exempt
		self.zero_rated_sales = zero_rated

	@api.one
	@api.depends('line_ids')
	def _compute_amount_product_type(self):
		amount_services = 0
		amount_capital = 0
		amount_goods = 0
		for line in self.line_ids:
			if line.product_id.type == 'service':
				amount_services += line.untaxed_amount

			if line.product_id.type == 'consu' or line.product_id.type == 'product':
				amount_goods += line.untaxed_amount

		self.amount_services = amount_services
		self.amount_goods = amount_goods
	
	# NEW FIELDS
	line_ids = fields.One2many('hr.expense.line', 'expense_id', string='Expense Lines', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'refused': [('readonly', False)]}, copy=False)
	tax_line_ids = fields.One2many('hr.expense.tax', 'expense_id', string='Tax Lines', oldname='tax_line', readonly=True, states={'draft': [('readonly', False)], 'confirm': [('readonly', False)], 'refused': [('readonly', False)]}, copy=True)

	is_approved = fields.Boolean()
	approver_id = fields.Many2one('hr.employee','Approver')
	current_user = fields.Many2one('res.users', compute='_get_current_user')
	responsible_id = fields.Many2one('res.user','Responsible', store=True, readonly=True, default=lambda self: self.env.uid)
	
	tax_amount = fields.Float(string='Taxes', store=True, compute='_compute_amount', digits=dp.get_precision('Account'))

	vat_sales = fields.Monetary(string='Vatable Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
	vat_exempt_sales = fields.Monetary(string='Vat Exempt Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
	zero_rated_sales = fields.Monetary(string='Zero Rated Sales', store=True, readonly=True, compute='_compute_amount_sales', track_visibility='always')
	
	amount_services = fields.Monetary(string='Amount of Services', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')
	amount_capital = fields.Monetary(string='Amount of Capital', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')
	amount_goods = fields.Monetary(string='Amount of Goods', store=True, readonly=True, compute='_compute_amount_product_type', track_visibility='always')

	expense_type = fields.Selection([
		('ob', 'OB Expense'),
		('direct', 'Direct Expense'),
		], string='Expense Type', default='ob', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]})
	ob_id = fields.Many2one('hr.employee.official.business', string='Official Business', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)]})


	reimbursement_mode = fields.Selection([
		('petty_cash', 'Petty Cash'),
		('reimbursement', 'Reimbursement'),
		('cash_advance', 'Liquidation for Cash Advance'),
		('credit_card', 'Credit Card Expenses'),
	], string='Reimbursement Mode', default='petty_cash', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)], 'validate': [('readonly', False)]})
	fund_custodian_id = fields.Many2one('hr.employee', 'Fund Custodian', readonly=True, states={'draft': [('readonly', False)], 'refused': [('readonly', False)], 'validate': [('readonly', False)]})
	
	# OVERRIDE FIELDS
	product_id = fields.Many2one(required=False)
	product_uom_id = fields.Many2one(required=False)
	unit_amount = fields.Float(required=False)
	quantity = fields.Float(required=False)
	date = fields.Date(required=True)
	payment_mode = fields.Selection([
		("own_account", "Employee (to reimburse)"),
		("company_account", "Company"),
	])
	state = fields.Selection([
		('draft', 'To Submit'),
		('confirm', 'Pending'),
		('validate', 'Approved'),
		('reported', 'Reported'),
		('done', 'Posted'),
		('refused', 'Refused')
	], string='Status', copy=False, index=True, readonly=True, store=True, help="Status of the expense.")

	@api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
	def _compute_state(self):
		for expense in self:
			if not expense.sheet_id:
				if expense.is_approved == True:
					expense.state = "validate"
				else:
					expense.state = "draft"
			elif expense.sheet_id.state == "cancel":
				expense.state = "refused"
			elif not expense.sheet_id.account_move_id:
				expense.state = "reported"
			else:
				expense.state = "done"
	
	# NEW FUNCTIONS
	@api.onchange('ob_id')
	def _onchange_ob_id(self):
		self.date = self.ob_id.date_ob

	@api.onchange('employee_id')
	def _set_employee_details(self):
		self.approver_id = self.employee_id.parent_id

	def _get_current_user(self):
		for rec in self:
			rec.current_user = self.env.uid

	@api.multi
	def compute_taxes(self):
		"""Function used in other module to compute the taxes on a fresh invoice created (onchanges did not applied)"""
		expense_tax = self.env['hr.expense.tax']
		ctx = dict(self._context)
		for expense in self:
			# Delete non-manual tax lines
			self._cr.execute("DELETE FROM hr_expense_tax WHERE expense_id=%s AND manual is False", (expense.id,))
			self.invalidate_cache()
			
			# Generate one tax line per tax, however many invoice lines it's applied to
			tax_grouped = expense.get_taxes_values()
			
			# Create new tax lines
			for tax in tax_grouped.values():
				expense_tax.create(tax)
				
		# dummy write on self to trigger recomputations
		return self.with_context(ctx).write({'expense_line_ids': []})

	def _prepare_tax_line_vals(self, line, tax):
		""" Prepare values to create an account.invoice.tax line
		The line parameter is an account.invoice.line, and the
		tax parameter is the output of account.tax.compute_all().
		"""
		
		vals = {
			'expense_id': self.id,
			'name': tax['name'],
			'tax_id': tax['id'],
			'amount': tax['amount'],
			'base': tax['base'],
			'manual': False,
			'sequence': tax['sequence'],
			'account_analytic_id': tax['analytic'] and line.account_analytic_id.id or False,
			'account_id': (tax['account_id'] or line.account_id.id) or (tax['refund_account_id'] or line.account_id.id),
		}

		# If the taxes generate moves on the same financial account as the invoice line,
		# propagate the analytic account from the invoice line to the tax line.
		# This is necessary in situations were (part of) the taxes cannot be reclaimed,
		# to ensure the tax move is allocated to the proper analytic account.
		if not vals.get('account_analytic_id') and line.account_analytic_id and vals['account_id'] == line.account_id.id:
			vals['account_analytic_id'] = line.account_analytic_id.id
			
		return vals
	
	@api.multi
	def get_taxes_values(self):
		tax_grouped = {}
		for line in self.line_ids:
			price_unit = line.price_unit
			taxes = line.tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.employee_id.user_id.partner_id)['taxes']
			for tax in taxes:
				val = self._prepare_tax_line_vals(line, tax)
				key = self.env['account.tax'].browse(tax['id']).get_grouping_key(val)
				
				if key not in tax_grouped:
					tax_grouped[key] = val
				else:
					tax_grouped[key]['amount'] += val['amount']
					tax_grouped[key]['base'] += val['base']

		return tax_grouped
	
	@api.onchange('line_ids')
	def _onchange_line_ids(self):
		taxes_grouped = self.get_taxes_values()
		tax_lines = self.tax_line_ids.filtered('manual')
		for tax in taxes_grouped.values():
			tax_lines += tax_lines.new(tax)
		self.tax_line_ids = tax_lines
		return

	# OVERRIDE FUNCTIONS
	@api.model
	def create(self, vals):
		result = super(HrExpense, self).create(vals)
		
		if any(line.tax_ids for line in result.line_ids) and not result.tax_line_ids:
			result.compute_taxes()

		if vals['expense_type'] == 'ob' and vals['ob_id']:
			# UPDATE OB STATE
			ob = self.env['hr.employee.official.business'].search([('id','=',vals['ob_id'])])
			ob.write({'state':'expense'})
			
		return result

	@api.multi
	def action_move_create(self):
		res = self.mapped('line_ids').action_move_create()
		for expense in self:
			ob = self.env['hr.employee.official.business'].search([('id','=',expense.ob_id.id)])
			ob.write({'state':'done'})
		return res
	
	@api.depends('line_ids', 'line_ids.total_amount', 'tax_line_ids', 'tax_line_ids.amount')
	def _compute_amount(self):
		for expense in self:
			untaxed_amount = sum(expense.line_ids.mapped('untaxed_amount'))
			tax_amount = sum(line.amount for line in expense.tax_line_ids)
			total_amount = sum(expense.line_ids.mapped('total_amount'))
			expense.untaxed_amount = untaxed_amount
			expense.tax_amount = tax_amount
			expense.total_amount = total_amount

	@api.multi
	def write(self, vals):
		for expense in self:
			ob_id = expense.ob_id
			expense_type = vals.get('expense_type')
			new_ob_id =  vals.get('ob_id')

			if not expense_type:
				expense_type = expense.expense_type

			if expense_type == 'ob':
				if ob_id == new_ob_id:
					new_ob = self.env['hr.employee.official.business'].search([('id','=',new_ob_id)])
					new_ob.write({'state':'expense'})
				else:
					if new_ob_id:
						ob = self.env['hr.employee.official.business'].search([('id','=',ob_id.id)])
						ob.write({'state':'validate'})

						new_ob = self.env['hr.employee.official.business'].search([('id','=',new_ob_id)])
						new_ob.write({'state':'expense'})

			else:
				if ob_id:
					ob = self.env['hr.employee.official.business'].search([('id','=',ob_id.id)])
					ob.write({'state':'validate'})
					vals['ob_id'] = False

		result = super(HrExpense, self).write(vals)
		return result

	@api.multi
	def unlink(self):
		for expense in self:
			if expense.expense_type == 'ob' and expense.ob_id:
					ob = self.env['hr.employee.official.business'].search([('id','=',expense.ob_id.id)])
					ob.write({'state':'validate'})
		res = super(HrExpense, self).unlink()
		return res

	@api.multi
	def submit_expenses(self):
		for expense in self:
			expense.write({'state':'confirm'})

	@api.multi
	def approve_expenses(self):
		if self.approver_id:
			if self.approver_id.user_id != self.current_user:
			# if self.approver_id.user_id != self.env.uid:
				raise UserError("You cannot approve/refuse your own epense. Expense Approver: %s" % (self.approver_id.name))
		else:
			raise UserError("No approver was set. Please assign an approver to employee.")
		# self.write({'state': 'validate', 'responsible_id': self.env.user.id, 'is_approved': True})
		self.write({'state': 'validate', 'is_approved': True})

	@api.multi
	def refuse_expenses(self):
		if self.approver_id:
			if self.approver_id.user_id != self.current_user:
			# if self.approver_id.user_id != self.env.uid:
				raise UserError("You cannot approve/refuse your own epense. Expense Approver: %s" % (self.approver_id.name))
		else:
			raise UserError("No approver was set. Please assign an approver to employee.")
		self.write({'state': 'refused'})

	@api.multi
	def draft_expenses(self):
		for expense in self:
			expense.write({'state':'draft'})

	@api.multi
	def create_sheet(self):

		if self.fund_custodian_id.user_id != self.current_user:
		# if self.fund_custodian_id.user_id != self.env.uid:
			raise UserError(_("You're not allowed to create this report. Fund Custodian: %s" % (self.fund_custodian_id.name)))

		if any(expense.state != 'validate' for expense in self):
			raise UserError(_("You cannot report twice the same line!"))

		if len(self.mapped('employee_id')) != 1:
			raise UserError(_("You cannot report expenses for different employees in the same report!"))

		return {
			'type': 'ir.actions.act_window',
			'view_mode': 'form',
			'res_model': 'hr.expense.sheet',
			'target': 'current',
			'context': {
				'default_expense_line_ids': [line.id for line in self],
				'default_employee_id': self[0].employee_id.id,
				'default_name': self[0].name if len(self.ids) == 1 else ''
			}
		}