# -*- coding: utf-8 -*-
{
    'name': "Globpak",

    'summary': """
        Globpak Customizations""",

    'description': """
        - Account Payable Voucher
    """,

    'author': "Excode Innovations Inc.",
    'website': "http://www.excodeinnovations.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Custom',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_expense'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/report_expense_sheet.xml',
        'views/report_account_payable_voucher.xml',
        'views/report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}