# -*- coding: utf-8 -*-
{
    'name': "Globpak",

    'summary': """
        Globpak Customizations""",

    'description': """
        Acccounting Customizations
            - Expense Report
            - Account Payable Voucher
            - Check Print
            - Check Voucher
            - Sales Invoice
            - Acknowledgement Receipt
            - Collection Receipt
            - Credit Memo
            - Debit Memo
            - Journal Voucher
            - Purchase Transaction Reconciliation of Listing Enforcement
            - Sales Transaction Reconciliation of Listing Enforcement
            - Alphabetical List of Payees from whom Taxes were Withheld
            - BIR Compilation
                - Sales Summary Report
                - Summary of Expanded Withholding Tax Deduction
                - Summary of Accounts Payable
                - SUmmary of Accounts Receivable 
                - Summary of Taxes and Licenses
    """,

    'author': "Excode Innovations Inc.",
    'website': "http://www.excodeinnovations.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Custom',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_expense', 'report', 'l10n_us_check_printing'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/us_check_printing.xml',
        'data/account_ewt_structure_data.xml',
        'views/layout_templates.xml',
        'views/account_tax_view.xml',
        'views/account_ewt_structure_view.xml',
        'views/account_invoice_view.xml',
        'views/account_payment_view.xml',
        'views/hr_expense_view.xml',
        'views/report_expense_sheet.xml',
        'views/report_account_payable_voucher.xml',
        'views/report_invoice.xml',
        'views/report_acknowledgement_receipt.xml',
        'views/report_collection_receipt.xml',
        'views/report_journal_voucher.xml',
        'views/report_credit_memo.xml',
        'views/report_debit_memo.xml',
        'report/print_check.xml',
        'report/print_check_top.xml',
        'report/print_check_bottom.xml',
        # 'report/account_receivable_summary_report_views.xml', # END OF ACCOUNTING
        'report/report_deliveryslip.xml', # START OF PURCHASING AND INVENTORY
        'views/report.xml',
        'wizard/account_report_alphalist_payee_view.xml',
        'wizard/account_report_sales_transaction_view.xml',
        'wizard/account_report_purchase_transaction_view.xml',
        'wizard/account_report_sales_summary_view.xml',
        'wizard/account_report_ewt_deduction_summary_view.xml',
        # 'wizard/account_report_asset_summary_view.xml',
        'wizard/account_report_payable_summary_view.xml',
        'wizard/account_report_receivable_summary_view.xml',
        'wizard/account_report_taxes_licenses_summary_view.xml',
        'views/custom_report_menu.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}