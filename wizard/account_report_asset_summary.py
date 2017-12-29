from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import xlwt
from xlsxwriter.workbook import Workbook
import datetime

class AccountReportAssetSummary(models.TransientModel):
    _name = 'account.report.asset.summary'
    _description = 'ASSET SUMMARY REPORT'

    # def _default_account_ids(self):
    #     account_id = self.env['account.account'].search([('type.name','=','Fixed Assets')], limit=1)
    #     return account_id

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
    # account_id = fields.Many2one('account.account', string='Account', required=True, default=lambda self: self._default_account_id())
    # account_ids = fields.One2many('account.account', string='Account', required=True, default=lambda self: self._default_account_ids())

    def _print_report(self, data):
        filename = 'account_asset_summary_report.xls'
        title = 'ASSET SUMMARY REPORT'
        company_id = data['company_id']['company_id'][0]
        date_from = data['date_from']['date_from']
        date_to = data['date_to']['date_to']
        # account_id = data['account_id']['account_id'][0]
        
        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/export_xls/asset_summary?filename=%s&title=%s&company_id=%s&date_from=%s&date_to=%s'%(filename,title,company_id,date_from,date_to),
            'target': 'self',
        }                     

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['company_id'] = self.read(['company_id'])[0]
        data['date_from'] = self.read(['date_from'])[0]
        data['date_to'] = self.read(['date_to'])[0]
        # data['account_id'] = self.read(['account_id'])[0]
        return self._print_report(data)