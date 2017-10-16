from odoo import models, fields, api
from odoo import tools

class AccountReceiveableSummaryReport(models.Model):
    _name = 'account.receiveable.summary.report'
    _description = 'Account Receiveable Summary Report'
    _auto = False

    name = fields.Char(readonly=True)
    date = fields.Date(readonly=True)
    account_id = fields.Many2one('account.account', string='Account', readonly=True)
    # currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
    # price_average = fields.Float(string='Average Price', readonly=True, group_operator="avg")
    # residual = fields.Float(string='Total Residual', readonly=True)
    # journal_id = fields.Many2one('account.journal', string='Journal', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True)
    zero_rated_total = fields.Float(string='Zero Rated', readonly=True)
    exempt_total = fields.Float(string='Exempt', readonly=True)
    vatable_total = fields.Float(string='Vatable', readonly=True)
    tax_total = fields.Float(string='Input Tax (12%)', readonly=True)
    amount_total = fields.Float(string='Total', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('proforma', 'Pro-forma'),
        ('proforma2', 'Pro-forma'),
        ('open', 'Open'),
        ('paid', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Invoice Status', readonly=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'account_receiveable_summary_report')
        self._cr.execute("""
            create or replace view account_receiveable_summary_report as (
                select
                    min(inv.id) as id,
                    inv.name as name,
                    inv.date as date,
                    inv.zero_rated_sales as zero_rated_total,
                    inv.vat_exempt_sales as exempt_total,
                    inv.vat_sales as vatable_total,
                    inv.amount_tax as tax_total,
                    inv.amount_total as amount_total,
                    inv.partner_id as partner_id,
                    inv.state as state,
                    inv.company_id as company_id
                from account_invoice inv
                group by
                    inv.name,inv.date,inv.state,inv.partner_id,inv.company_id,inv.zero_rated_sales,inv.vat_exempt_sales,inv.vat_sales,inv.amount_tax,inv.amount_total
        )""")