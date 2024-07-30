# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class DownloadController(http.Controller):

    @http.route('/ddjj/download_files', type='http', auth='user')
    def download_files(self, attachment_id, attachment2_id, **kw):
        attachment = request.env['ir.attachment'].sudo().browse(int(attachment_id))
        attachment2 = request.env['ir.attachment'].sudo().browse(int(attachment2_id))

        if attachment.exists():
            attachment_url = '/web/content/%s?download=true' % attachment.id
        if attachment2.exists():
            attachment2_url = '/web/content/%s?download=true' % attachment2.id

        return request.redirect(attachment_url + '|' + attachment2_url)