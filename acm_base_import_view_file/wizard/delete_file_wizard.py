# -*- coding: utf-8 -*-
from odoo import models, fields


# 导入页面
class DeleteFileWizard(models.TransientModel):
    _name = 'acm_base.delete_view_file_wizard'

    view_ids = fields.Many2many('ir.ui.view', relation='delete_view_ids_table', column1='id', string='imported view')

    def delete_actions(self):
        res_ids = self.view_ids.ids

        parent_env = self.env['acm_base.import_view_file'].browse([self.env.context.copy().get('parent_id')])
        delete_ids = list(set(parent_env.view_ids.ids) - set(res_ids))
        # print(parent_env.view_ids.ids,res_ids,delete_ids)

        for rec in self.env['ir.ui.view'].browse(delete_ids):
            rec.unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'delete dome.',
                'message': 'delete dome.',
                'sticky': False,
                'type': 'info'
            }}

    def refresh_view_ids(self):
        parent_env = self.env['acm_base.import_view_file'].browse([self.env.context.copy().get('parent_id')])
        # print(parent_env.view_ids.ids, self.view_ids.ids)
        context = {
            # 'default_view_ids': [(6, 0, list(set(parent_env.view_ids.ids) - set(self.view_ids.ids)))],
            'default_view_ids': [(6, 0, parent_env.view_ids.ids)],
        }
        return {
            'name': 'Delete File',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'acm_base.delete_view_file_wizard',
            'target': 'new',
            'context': context
        }
