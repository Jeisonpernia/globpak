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
				- Summary of Purchases and Expenses
				- Summary of Expanded Withholding Tax Deduction
				- Summary of Accounts Payable
				- SUmmary of Accounts Receivable 
				- Summary of Taxes and Licenses
				- Asset Summary Report
			- Landed Cost

		Purchasing and Inventory Customizations
			- RFQ
			- Purchase Order
			- Delivery Slip
			- Picking Operation

		Others
			- Official Business
			- HR Expense Detailed
			- Trip Ticket
	""",

	'author': "Excode Innovations Inc.",
	'website': "http://www.excodeinnovations.com",

	# Categories can be used to filter modules in modules listing
	# Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
	# for the full list
	'category': 'Custom',
	'version': '0.1',

	# any module necessary for this one to work correctly
	'depends': ['base', 'web', 'web_editor', 'account', 'hr', 'hr_contract', 'hr_expense', 'hr_holidays', 'l10n_us_check_printing', 'sale', 'sale_stock', 'purchase', 'stock', 'crm', 'account_asset', 'website_quote', 'portal', 'calendar', 'website_calendar'],

	# always loaded
	'data': [
		'security/ir.model.access.csv',
		'security/globpak_security.xml',
		'data/ir_sequence_data.xml',
		'data/us_check_printing.xml',
		'data/account_ewt_structure_data.xml',
		'data/report_paper_format_data.xml',
		'views/assets.xml',
		'views/portal_templates.xml',
		'views/layout_templates.xml',
		'views/account_tax_view.xml',
		'views/account_ewt_structure_view.xml',
		'views/account_invoice_view.xml',
		'views/account_payment_view.xml',
		'views/hr_expense_view.xml',
		'views/hr_employee_official_business_view.xml',
		'views/fleet_trip_ticket_view.xml',
		'views/studio_hr_employee_view.xml',
		'views/studio_purchase_order_view.xml',
		'views/studio_sale_order_view.xml',
		'views/studio_stock_picking_view.xml',
		'views/studio_res_partner_view.xml',
		'views/account_landed_cost_view.xml',
		'views/product_view.xml',
		'views/product_pricelist_view.xml',
		'views/hr_holidays_view.xml',
		'views/crm_lead_view.xml',
		'views/website_quote_templates.xml',
		'views/salesperson_reports.xml',
		'report/print_check.xml',
		'report/print_check_top.xml',
		'report/print_check_middle.xml',
		'report/print_check_bottom.xml',
		'report/report_purchaseorder.xml',
		'report/report_purchasequotation.xml',
		'report/report_picking.xml',
		'report/report_deliveryslip.xml',
		'report/report_saleorder.xml',
		'report/report_invoice.xml',
		'report/report_journal_voucher.xml',
		'report/report_credit_memo.xml',
		'report/report_debit_memo.xml',
		'report/report_acknowledgement_receipt.xml',
		'report/report_collection_receipt.xml',
		'report/report_account_payable_voucher.xml',
		'report/report_expense_sheet.xml',
		'report/report_official_business.xml',
		'report/report_expense.xml',
		'report/report_trip_ticket.xml',
		'report/report_account_payment_receipt.xml',
		'report/report.xml',
		'wizard/account_report_alphalist_payee_view.xml',
		'wizard/account_report_sales_transaction_view.xml',
		'wizard/account_report_purchase_transaction_view.xml',
		'wizard/account_report_import_transaction_view.xml',
		'wizard/account_report_sales_summary_view.xml',
		'wizard/account_report_purchase_expense_summary_view.xml',
		'wizard/account_report_ewt_deduction_summary_view.xml',
		'wizard/account_report_asset_summary_view.xml',
		'wizard/account_report_payable_summary_view.xml',
		'wizard/account_report_receivable_summary_view.xml',
		'wizard/account_report_taxes_licenses_summary_view.xml',
		'wizard/report_trip_ticket_view.xml',
		'wizard/split_purchase_order_view.xml',
		'views/custom_report_menu.xml',
	],
	'qweb': [
		'static/src/xml/portal_sale_validate.xml',
	],
	# only loaded in demonstration mode
	'demo': [
		# 'demo/demo.xml',
	],
}