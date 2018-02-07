import base64

from odoo import http, _
from odoo.exceptions import AccessError
from odoo.http import request
from odoo.tools import consteq
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager

# Sales Quote
class CustomerPortal(CustomerPortal):
	def _order_check_access(self, order_id, access_token=None):
		order = request.env['sale.order'].browse([order_id])
		order_sudo = order.sudo()
		try:
			order.check_access_rights('read')
			order.check_access_rule('read')
		except AccessError:
			if not access_token or not consteq(order_sudo.access_token, access_token):
				raise
		return order_sudo

	def _portal_quote_user_can_validate(self, order_id):
		return request.env['ir.config_parameter'].sudo().get_param('sale.sale_portal_confirmation_options', default='none') in ('pay', 'sign')

	@http.route(['/my/quotes/validate'], type='json', auth="public", website=True)
	def portal_quote_validate(self, res_id, access_token=None, partner_name=None, signature=None, client_po_no=None):
		if not self._portal_quote_user_can_validate(res_id):
			return {'error': _('Operation not allowed')}
		if not signature:
			return {'error': _('Signature is missing.')}
		# if not client_po:
		# 	return {'error': _('Purchase Order is missing.')}

		try:
			order_sudo = self._order_check_access(res_id, access_token=access_token)
		except AccessError:
			return {'error': _('Invalid order')}
		if order_sudo.state != 'sent':
			return {'error': _('Order is not in a state requiring customer validation.')}

		order_sudo.write({'x_clientpo': client_po_no, 'state': 'confirm'})
		# order_sudo.action_confirm()

		_message_post_helper(
			res_model='sale.order',
			res_id=order_sudo.id,
			# message=_('Order signed by %s. \nPurchase Order Number: %s') % (partner_name,client_po_no,),
			# attachments=[('purchase.pdf', base64.b64decode(client_po))] if client_po else [],
			message=_('Order signed by %s. Purchase Order Number: %s') % (partner_name,client_po_no),
			attachments=[('signature.png', base64.b64decode(signature))] if signature else [],
			**({'token': access_token} if access_token else {}))
		return {
			'success': _('Your order has been confirmed.'),
			'redirect_url': '/my/orders/%s?%s' % (order_sudo.id, access_token and 'access_token=%s' % order_sudo.access_token or ''),
		}