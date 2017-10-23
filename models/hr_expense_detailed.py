from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, RedirectWarning, ValidationError

class HrExpenseDetailedLine(models.Model):
    _name = 'hr.expense.detailed.line'
    _description = 'HR Expense Detailed Line'

    name = fields.Text(string='Description', required=True)
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', index=True, domain=[('can_be_expensed', '=', True)], required=True)
    uom_id = fields.Many2one('product.uom', string='Unit of Measure', ondelete='set null', index=True, oldname='uos_id')
    quantity = fields.Float()
    price_unit = fields.Float(string='Price Unit')
    # tax_ids = fields.Many2many('account.tax', 'detailed_expense_tax', 'detailed_expense_id', 'tax_id', string='Taxes', states={'done': [('readonly', True)], 'post': [('readonly', True)]})
    tax_ids = fields.Many2many('account.tax', 'detailed_expense_tax', 'detailed_expense_id', 'tax_id', string='Taxes')
    untaxed_amount = fields.Float(string='Subtotal', store=True, compute='_compute_amount', digits=dp.get_precision('Account'))
    total_amount = fields.Float(string='Total', store=True, compute='_compute_amount', digits=dp.get_precision('Account'))

    # reference = fields.Char()
    # date = fields.Datetime()

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, states={'submit': [('readonly', False)]}, default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))
    # partner_id = fields.Many2one('res.partner', 'Vendor')
    account_id = fields.Many2one('account.account', string='Account', states={'post': [('readonly', True)], 'done': [('readonly', True)]}, default=lambda self: self.env['ir.property'].get('property_account_expense_categ_id', 'product.category'))
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)], 'cancel': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)], 'cancel': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    account_analytic_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('submit', 'To Approve'),
        ('validate', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
        ], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True, help="Status of the expense.")

    summary_id = fields.Many2one('hr.expense.detailed.summary', string="Detailed Expense Summary", readonly=True, copy=False)

    @api.depends('summary_id', 'summary_id.account_move_id', 'summary_id.state')
    def _compute_state(self):
        for expense in self:
            if expense.summary_id.state == "draft":
                expense.state = "draft"
            elif expense.summary_id.state == "cancel":
                expense.state = "cancel"
            elif expense.summary_id.state == "submit":
                expense.state = "submit"
            elif expense.summary_id.state == "validate":
                expense.state = "validate"
            elif expense.summary_id.state == "post":
                expense.state = "post"
            else:
                expense.state = "done"

    @api.depends('quantity', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_amount(self):
        for expense in self:
            expense.untaxed_amount = expense.price_unit * expense.quantity
            taxes = expense.tax_ids.compute_all(expense.price_unit, expense.currency_id, expense.quantity, expense.product_id, expense.employee_id.user_id.partner_id)
            expense.total_amount = taxes.get('total_included')

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
        partner_id = self.employee_id.address_home_id.commercial_partner_id.id
        return {
            'date_maturity': line.get('date_maturity'),
            'partner_id': partner_id,
            'name': line['name'][:64],
            'debit': line['price'] > 0 and line['price'],
            'credit': line['price'] < 0 and - line['price'],
            'account_id': line['account_id'],
            'analytic_line_ids': line.get('analytic_line_ids'),
            'amount_currency': line['price'] > 0 and abs(line.get('amount_currency')) or - abs(line.get('amount_currency')),
            'currency_id': line.get('currency_id'),
            'tax_line_id': line.get('tax_line_id'),
            'tax_ids': line.get('tax_ids'),
            'quantity': line.get('quantity', 1.00),
            'product_id': line.get('product_id'),
            'product_uom_id': line.get('uom_id'),
            'analytic_account_id': line.get('account_analytic_id'),
            'payment_id': line.get('payment_id'),
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
        for expense in self:
            journal = expense.summary_id.bank_journal_id if expense.summary_id.payment_mode == 'company_account' else expense.summary_id.journal_id
            #create the move that will contain the accounting entries
            acc_date = expense.summary_id.accounting_date or expense.summary_id.date
            move = self.env['account.move'].create({
                'journal_id': journal.id,
                'company_id': self.env.user.company_id.id,
                'date': acc_date,
                'ref': expense.summary_id.name,
                # force the name to the default value, to avoid an eventual 'default_name' in the context
                # to set it to '' which cause no number to be given to the account.move when posted.
                'name': '/',
            })
            company_currency = expense.company_id.currency_id
            diff_currency_p = expense.currency_id != company_currency
            #one account.move.line per expense (+taxes..)
            move_lines = expense._move_line_get()

            #create one more move line, a counterline for the total on payable account
            payment_id = False
            total, total_currency, move_lines = expense._compute_expense_totals(company_currency, move_lines, acc_date)
            if expense.summary_id.payment_mode == 'company_account':
                if not expense.summary_id.bank_journal_id.default_credit_account_id:
                    raise UserError(_("No credit account found for the %s journal, please configure one.") % (expense.sheet_id.bank_journal_id.name))
                emp_account = expense.summary_id.bank_journal_id.default_credit_account_id.id
                journal = expense.summary_id.bank_journal_id
                #create payment
                payment_methods = (total < 0) and journal.outbound_payment_method_ids or journal.inbound_payment_method_ids
                journal_currency = journal.currency_id or journal.company_id.currency_id
                payment = self.env['account.payment'].create({
                    'payment_method_id': payment_methods and payment_methods[0].id or False,
                    'payment_type': total < 0 and 'outbound' or 'inbound',
                    'partner_id': expense.employee_id.address_home_id.commercial_partner_id.id,
                    'partner_type': 'supplier',
                    'journal_id': journal.id,
                    'payment_date': expense.date,
                    'state': 'reconciled',
                    'currency_id': diff_currency_p and expense.currency_id.id or journal_currency.id,
                    'amount': diff_currency_p and abs(total_currency) or abs(total),
                    'name': expense.name,
                })
                payment_id = payment.id
            else:
                if not expense.employee_id.address_home_id:
                    raise UserError(_("No Home Address found for the employee %s, please configure one.") % (expense.employee_id.name))
                emp_account = expense.employee_id.address_home_id.property_account_payable_id.id

            aml_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            move_lines.append({
                    'type': 'dest',
                    'name': aml_name,
                    'price': total,
                    'account_id': emp_account,
                    'date_maturity': acc_date,
                    'amount_currency': diff_currency_p and total_currency or False,
                    'currency_id': diff_currency_p and expense.currency_id.id or False,
                    'payment_id': payment_id,
                    })

            #convert eml into an osv-valid format
            lines = map(lambda x: (0, 0, expense._prepare_move_line(x)), move_lines)
            move.with_context(dont_create_taxes=True).write({'line_ids': lines})
            expense.summary_id.write({'account_move_id': move.id})
            move.post()
            if expense.summary_id.payment_mode == 'company_account':
                expense.summary_id.paid_expense()
        return True

    @api.multi
    def _move_line_get(self):
        account_move = []
        for expense in self:
            if expense.account_id:
                account = expense.account_id
            elif expense.product_id:
                account = expense.product_id.product_tmpl_id._get_product_accounts()['expense']
                if not account:
                    raise UserError(_("No Expense account found for the product %s (or for it's category), please configure one.") % (expense.product_id.name))
            else:
                account = self.env['ir.property'].with_context(force_company=expense.company_id.id).get('property_account_expense_categ_id', 'product.category')
                if not account:
                    raise UserError(_('Please configure Default Expense account for Product expense: `property_account_expense_categ_id`.'))

            aml_name = expense.employee_id.name + ': ' + expense.name.split('\n')[0][:64]
            move_line = {
                    'type': 'src',
                    'name': aml_name,
                    'price_unit': expense.price_unit,
                    'quantity': expense.quantity,
                    'price': expense.total_amount,
                    'account_id': account.id,
                    'product_id': expense.product_id.id,
                    'uom_id': expense.uom_id.id,
                    'analytic_account_id': expense.account_analytic_id.id,
            }
            account_move.append(move_line)

            # Calculate tax lines and adjust base line
            taxes = expense.tax_ids.compute_all(expense.price_unit, expense.currency_id, expense.quantity, expense.product_id)
            account_move[-1]['price'] = taxes['total_excluded']
            account_move[-1]['tax_ids'] = expense.tax_ids.ids
            for tax in taxes['taxes']:
                account_move.append({
                    'type': 'tax',
                    'name': tax['name'],
                    'price_unit': tax['amount'],
                    'quantity': 1,
                    'price': tax['amount'],
                    'account_id': tax['account_id'] or move_line['account_id'],
                    'tax_line_id': tax['id'],
                })
        return account_move

class HrExpenseDetailedSummary(models.Model):
    _name = 'hr.expense.detailed.summary'
    _description = 'HR Expense for detailed input of taxes using Vendor Bill format'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    name = fields.Char(string='Expense Summary', required=True)
    payment_mode = fields.Selection([("own_account", "Employee (to reimburse)"), ("company_account", "Company")], default='own_account', readonly=True, string="Payment By")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1))
    address_id = fields.Many2one('res.partner', string="Employee Home Address")
    department_id = fields.Many2one('hr.department', string='Department', states={'post': [('readonly', True)], 'done': [('readonly', True)]})
    company_id = fields.Many2one('res.company', string='Company', readonly=True, states={'draft': [('readonly', False)], 'cancel': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, states={'draft': [('readonly', False)], 'cancel': [('readonly', False)]}, default=lambda self: self.env.user.company_id.currency_id)
    ob_id = fields.Many2one('hr.employee.official.business', string='Official Business', required=True)
    account_move_id = fields.Many2one('account.move', string='Journal Entry', copy=False)
    journal_id = fields.Many2one('account.journal', string='Expense Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]},
        default=lambda self: self.env['ir.model.data'].xmlid_to_object('hr_expense.hr_expense_account_journal') or self.env['account.journal'].search([('type', '=', 'purchase')], limit=1),
        help="The journal used when the expense is done.")
    bank_journal_id = fields.Many2one('account.journal', string='Bank Journal', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, default=lambda self: self.env['account.journal'].search([('type', 'in', ['case', 'bank'])], limit=1), help="The payment method used when the expense is paid by the company.")

    partner_id = fields.Many2one('res.partner', 'Vendor', required=True)
    reference = fields.Char()
    date = fields.Datetime()

    accounting_date = fields.Datetime(string='Accounting Date')
    line_ids = fields.One2many('hr.expense.detailed.line', 'summary_id', string='Detailed Expense Lines', states={'done': [('readonly', True)], 'post': [('readonly', True)]}, copy=False)
    tax_line_ids = fields.One2many('hr.expense.detailed.tax', 'summary_id', string='Tax Lines', oldname='tax_line', readonly=True, states={'done': [('readonly', True)], 'post': [('readonly', True)]}, copy=True)
    total_amount = fields.Monetary(string='Total Amount', store=True, compute='_compute_amount', digits=dp.get_precision('Account'))
    total_amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, compute='_compute_amount', digits=dp.get_precision('Account'))
    total_amount_tax = fields.Monetary(string='Tax', store=True, compute='_compute_amount', digits=dp.get_precision('Account'))
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('submit', 'To Approve'),
        ('validate', 'Approved'),
        ('post', 'Posted'),
        ('done', 'Paid'),
        ('cancel', 'Refused')
    ], string='Status', index=True, readonly=True, track_visibility='onchange', copy=False, default='draft', required=True, help='Detailed Expense State')
    approver_id = fields.Many2one('hr.employee','Approver', store=True, compute='_set_employee_details')
    responsible_id = fields.Many2one('res.user','Responsible', store=True, readonly=True)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')

    @api.one
    @api.depends('line_ids', 'line_ids.total_amount', 'tax_line_ids', 'tax_line_ids.amount')
    def _compute_amount(self):
        self.total_amount = sum(self.line_ids.mapped('total_amount'))
        self.total_amount_untaxed = sum(self.line_ids.mapped('untaxed_amount'))
        self.total_amount_tax = sum(line.amount for line in self.tax_line_ids)

    @api.multi
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'hr.expense.detailed.summary'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0)

    @api.model
    def create(self, vals):
        # if not vals.get('account_id',False):
            # raise UserError(_('Configuration error!\nCould not find any account to create the invoice, are you sure you have a chart of account installed?'))

        result = super(HrExpenseDetailedSummary, self).create(vals)

        if any(line.tax_ids for line in result.line_ids) and not result.tax_line_ids:
            result.compute_taxes()

        return result

    @api.multi
    def compute_taxes(self):
        """Function used in other module to compute the taxes on a fresh invoice created (onchanges did not applied)"""
        expense_summary_tax = self.env['hr.expense.detailed.tax']
        ctx = dict(self._context)
        for summary in self:
            # Delete non-manual tax lines
            self._cr.execute("DELETE FROM hr_expense_detailed_tax WHERE summary_id=%s AND manual is False", (summary.id,))
            self.invalidate_cache()

            # Generate one tax line per tax, however many invoice lines it's applied to
            tax_grouped = summary.get_taxes_values()

            # Create new tax lines
            for tax in tax_grouped.values():
                expense_summary_tax.create(tax)

        # dummy write on self to trigger recomputations
        return self.with_context(ctx).write({'invoice_line_ids': []})

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        self.address_id = self.employee_id.address_home_id
        self.department_id = self.employee_id.department_id
        self.approver_id = self.employee_id.parent_id

    @api.onchange('ob_id')
    def _onchange_ob_id(self):
        self.date = self.ob_id.date

    @api.depends('employee_id')
    def _set_employee_details(self):
        for ob in self:
            ob.approver_id = ob.employee_id.parent_id

    def _prepare_tax_line_vals(self, line, tax):
        """ Prepare values to create an account.invoice.tax line

        The line parameter is an account.invoice.line, and the
        tax parameter is the output of account.tax.compute_all().
        """
        vals = {
            'summary_id': self.id,
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
            # price_unit = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            price_unit = line.price_unit
            taxes = line.tax_ids.compute_all(price_unit, self.currency_id, line.quantity, line.product_id, self.partner_id)['taxes']
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
        tax_lines = self.tax_line_ids.browse([])
        for tax in taxes_grouped.values():
            tax_lines += tax_lines.new(tax)
        self.tax_line_ids = tax_lines
        return

    @api.multi
    def submit_expense(self):
        self.write({'state': 'submit'})

    @api.multi
    def approve_expense(self):
        self.write({'state': 'validate', 'responsible_id': self.env.user.id})

    @api.multi
    def refuse_expense(self, reason):
        self.write({'state': 'cancel'})
        for summary in self:
            body = (_("Your Expense %s has been refused.<br/><ul class=o_timeline_tracking_value_list><li>Reason<span> : </span><span class=o_timeline_tracking_value>%s</span></li></ul>") % (summary.name, reason))
            summary.message_post(body=body)

    @api.multi
    def paid_expense(self):
        self.write({'state': 'done'})

    @api.multi
    def reset_expense(self):
        return self.write({'state': 'submit'})

    @api.multi
    def action_summary_move_create(self):
        if any(summary.state != 'validate' for summary in self):
            raise UserError(_("You can only generate accounting entry for approved expense(s)."))

        if any(not summary.journal_id for summary in self):
            raise UserError(_("Expenses must have an expense journal specified to generate accounting entries."))

        res = self.mapped('line_ids').action_move_create()

        if not self.accounting_date:
            self.accounting_date = self.account_move_id.date

        if self.payment_mode=='own_account':
            self.write({'state': 'post'})
        else:
            self.write({'state': 'done'})
        return res

    @api.multi
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('base', 'action_attachment')
        res['domain'] = [('res_model', '=', 'hr.expense.detailed.summary'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'hr.expense.detailed.summary', 'default_res_id': self.id}
        return res

    @api.multi
    def action_open_journal_entries(self):
        res = self.env['ir.actions.act_window'].for_xml_id('account', 'action_move_journal_line')
        res['domain'] = [('id', 'in', self.mapped('account_move_id').ids)]
        res['context'] = {}
        return res

class HrExpenseDetailedTax(models.Model):
    _name = "hr.expense.detailed.tax"
    _description = "HR Expense Detailed Tax"
    _order = 'sequence'

    def _compute_base_amount(self):
        tax_grouped = {}
        for summary in self.mapped('summary_id'):
            tax_grouped[summary.id] = summary.get_taxes_values()
        for tax in self:
            tax.base = 0.0
            if tax.tax_id:
                key = tax.tax_id.get_grouping_key({
                    'tax_id': tax.tax_id.id,
                    'account_id': tax.account_id.id,
                    'account_analytic_id': tax.account_analytic_id.id,
                })
                if tax.summary_id and key in tax_grouped[tax.summary_id.id]:
                    tax.base = tax_grouped[tax.summary_id.id][key]['base']
                else:
                    _logger.warning('Tax Base Amount not computable probably due to a change in an underlying tax (%s).', tax.tax_id.name)

    summary_id = fields.Many2one('hr.expense.detailed.summary', string='Expense Summary', ondelete='cascade', index=True)
    name = fields.Char(string='Tax Description', required=True)
    tax_id = fields.Many2one('account.tax', string='Tax', ondelete='restrict')
    account_id = fields.Many2one('account.account', string='Tax Account', required=True, domain=[('deprecated', '=', False)])
    account_analytic_id = fields.Many2one('account.analytic.account', string='Analytic account')
    amount = fields.Monetary()
    manual = fields.Boolean(default=True)
    sequence = fields.Integer(help="Gives the sequence order when displaying a list of expense tax.")
    company_id = fields.Many2one('res.company', string='Company', related='account_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', related='summary_id.currency_id', store=True, readonly=True)
    base = fields.Monetary(string='Base', compute='_compute_base_amount')

