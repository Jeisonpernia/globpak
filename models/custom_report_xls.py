from odoo import models, fields, api

class CustomReportXls(models.Model):
    _name = 'custom.report.xls'
    _description = 'Custom Report XLS'
    
    excel_file = fields.Binary('Excel Report')
    file_name = fields.Char('Excel File', size=64)
    custom_report_type = fields.Char('Custom Report Type')