# -*- coding: utf-8 -*-

import logging

from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class IrUiView(models.Model):
    _inherit = 'ir.ui.view'

    import_view_file_id = fields.Many2one(comodel_name='acm_base.import_view_file', ondelete='set null', readonly=True, copy=False)

    def unlink(self):
        try:
            if self.import_view_file_id:
                self.import_view_file_id.message_post(body=_('view: {} deleted'.format(self.name)))
        finally:
            super(IrUiView, self).unlink()
