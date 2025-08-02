# -*- coding: utf-8 -*-
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

VIEW_TYPE = [
    ('tree', 'Tree'),
    ('form', 'Form'),
    ('graph', 'Graph'),
    ('pivot', 'Pivot'),
    ('calendar', 'Calendar'),
    ('diagram', 'Diagram'),
    ('gantt', 'Gantt'),
    ('kanban', 'Kanban'),
    ('search', 'Search'),
    ('qweb', 'QWeb')
]


class AcmBaseImportViewFile(models.Model):
    _name = 'acm_base.import_view_file'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'import view file to ir_ui_view table in database.'

    name = fields.Char(default='Import view')

    view_type = fields.Selection(VIEW_TYPE, default='', string='View Type', required=True, help='视图类型')

    view_ids = fields.One2many(comodel_name='ir.ui.view', inverse_name='import_view_file_id')

    def import_file_action(self):
        self.ensure_one()
        context = {
            'self_id': self.id
        }
        return {
            'name': 'Import File',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'acm_base.import_view_file_wizard',
            'target': 'new',
            'context': context
        }

    def delete_file_action(self):
        self.ensure_one()
        context = {
            'default_view_ids': [(6, 0, self.view_ids.ids)],
            'parent_id': self.id
        }
        return {
            'name': 'Delete File',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'acm_base.delete_view_file_wizard',
            'target': 'new',
            'context': context
        }
