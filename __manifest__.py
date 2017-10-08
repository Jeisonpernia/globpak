<<<<<<< HEAD
# -*- coding: utf-8 -*-
{
    'name': "Globpak",

    'summary': """
        Globpak Customizations""",

    'description': """
        - Expense Report
        - Account Payable Voucher
        - Check Print
        - Check Voucher
        - Sales Invoice
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
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'data/us_check_printing.xml',
        'views/layout_templates.xml',
        'views/account_invoice_view.xml',
        'views/hr_expense_view.xml',
        'views/report_expense_sheet.xml',
        'views/report_account_payable_voucher.xml',
        'views/report_invoice.xml',
        'report/print_check.xml',
        'report/print_check_top.xml',
        'report/print_check_bottom.xml',
        'views/report_collection_receipt.xml',
        'views/report_journal_voucher.xml',
        'views/report_credit_memo.xml',
        'views/report_debit_memo.xml',
        'views/report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
=======
# -*- coding: utf-8 -*-
{
    'name': "Globpak",

    'summary': """
        Globpak Customizations""",

    'description': """
        - Expense Report
        - Account Payable Voucher
        - Check Print
        - Check Voucher
        - Sales Invoice
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
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'data/us_check_printing.xml',
        'views/layout_templates.xml',
        'views/account_invoice_view.xml',
        'views/hr_expense_view.xml',
        'views/report_expense_sheet.xml',
        'views/report_account_payable_voucher.xml',
        'views/report_invoice.xml',
        'report/print_check.xml',
        'report/print_check_top.xml',
        'report/print_check_bottom.xml',
        'views/report_collection_receipt.xml',
        'views/report_journal_voucher.xml',
        'views/report_credit_memo.xml',
        'views/report_debit_memo.xml',
        'views/report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
>>>>>>> 38d76b6e2eecc31ac32a4e9d1250e6a4f64b8912
}