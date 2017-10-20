from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.misc import xlwt
from xlsxwriter.workbook import Workbook

class AccountReportTaxesLicensesSummary(models.TransientModel):
    _name = 'account.report.taxes.licenses.summary'
    _description = 'SUMJMARY OF TAXES AND LICENSES'

    def _default_acount_id(self):
        account_id = self.env['account.account'].search([('name','=','Taxes and Licenses')], limit=1)
        return account_id

    company_id = fields.Many2one('res.company', string='Company', readonly=True, default=lambda self: self.env.user.company_id)
    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    account_id = fields.Many2one('account.account', string='Account', required=True, default=lambda self: self._default_acount_id())

    def _print_report(self, data):
        filename = 'account_taxes_license_summary_report.xls'
        title = 'SUMMARY OF TAXES AND LICENSES'
        company_id = data['company_id']['company_id'][0]
        date_from = data['date_from']['date_from']
        date_to = data['date_to']['date_to']
        account_id = data['account_id']['account_id'][0]
        
        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/export_xls/taxes_licenses?filename=%s&title=%s&company_id=%s&date_from=%s&date_to=%s&account_id=%s'%(filename,title,company_id,date_from,date_to,account_id),
            'target': 'self',
        }                     

    @api.multi
    def check_report(self):
        self.ensure_one()
        data = {}
        data['company_id'] = self.read(['company_id'])[0]
        data['date_from'] = self.read(['date_from'])[0]
        data['date_to'] = self.read(['date_to'])[0]
        data['account_id'] = self.read(['account_id'])[0]
        return self._print_report(data)