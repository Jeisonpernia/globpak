from odoo import fields, models, _
from odoo.exceptions import UserError

class AccountReportPayableSummary(models.TransientModel):
    _name = 'account.report.payable.summary'
    _description = 'Accounts Payable Summary Report (Monthly)'
    _inherit = 'account.common.account.report'

    journal_ids = fields.Many2many('account.journal', 'account_report_payable_summary_journal_rel', 'account_id', 'journal_id', string='Journals', required=True)

    def _print_report(self, data):
        data = self.pre_print_report(data)
        # data['form'].update(self.read(['initial_balance', 'sortby'])[0])
        # if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            # raise UserError(_("You must define a Start Date"))
        records = self.env[data['model']].browse(data.get('ids', []))
        return self.env['report'].with_context(landscape=True).get_action(records, 'globpak.report_account_payable_summary', data=data)