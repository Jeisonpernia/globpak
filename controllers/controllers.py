# -*- coding: utf-8 -*-
from odoo import http

# class Globpak(http.Controller):
#     @http.route('/globpak/globpak/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/globpak/globpak/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('globpak.listing', {
#             'root': '/globpak/globpak',
#             'objects': http.request.env['globpak.globpak'].search([]),
#         })

#     @http.route('/globpak/globpak/objects/<model("globpak.globpak"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('globpak.object', {
#             'object': obj
#         })