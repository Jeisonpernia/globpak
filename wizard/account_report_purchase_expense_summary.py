from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import xlwt
from xlsxwriter.workbook import Workbook
import datetime

class AccountReportPurchaseExpenseSummary(models.TransientModel):
    _name = 'account.report.purchase.expense.summary'
    _description = 'Summary of Purchases and Expenses'

    def _default_journal_id(self):
        journal_id = self.env['account.journal'].search([('name','=','Vendor Bills')], limit=1)
        return journal_id

    def _default_date_from(self):
        # date_today = datetime.date.today()
        # if date_today.day > 25:
        #     date_today += datetime.timedelta(7)
        # return date_today.replace(day=1)
        return datetime.date.today().replace(day=1)

    def _default_date_to(self):
        date_today = datetime.date.today()
        next_month = date_today.replace(day=28) + datetime.timedelta(days=4)
        return next_month - datetime.timedelta(days=next_month.day)

    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    date_from = fields.Date(string='Start Date', required=True, default=lambda self: self._default_date_from())
    date_to = fields.Date(string='End Date', required=True, default=lambda self: self._default_date_to())
    # account_id = fields.Many2one('account.account', string='Account', required=True, default=lambda self: self._default_acount_id())
    journal_id = fields.Many2one('account.journal', string='Journal', required=True, default=lambda self: self._default_journal_id())

    def _print_report(self, data):
        filename = 'account_purchase_expense_summary_report.xls'
        title = 'SUMMARY OF PURCHASES AND EXPENSES'
        company_id = data['company_id']['company_id'][0]
        date_from = data['date_from']['date_from']
        date_to = data['date_to']['date_to']
        journal_id = data['journal_id']['journal_id'][0]
        
        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/export_xls/purchase_expense?filename=%s&title=%s&company_id=%s&date_from=%s&date_to=%s&journal_id=%s'%(filename,title,company_id,date_from,date_to,journal_id),
            'target': 'self',
        }                     

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['company_id'] = self.read(['company_id'])[0]
        data['date_from'] = self.read(['date_from'])[0]
        data['date_to'] = self.read(['date_to'])[0]
        data['journal_id'] = self.read(['journal_id'])[0]
        return self._print_report(data)