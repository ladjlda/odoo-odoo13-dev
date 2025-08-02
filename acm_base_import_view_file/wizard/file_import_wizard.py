# -*- coding: utf-8 -*-
import base64

from odoo import models, fields, _, api
from odoo.exceptions import UserError

# from odoo.addons.base.models.ir_ui_view import get_view_arch_from_file

VIEW_TYPE = [
    # ('tree', 'Tree'),
    # ('form', 'Form'),
    # ('graph', 'Graph'),
    # ('pivot', 'Pivot'),
    # ('calendar', 'Calendar'),
    # ('diagram', 'Diagram'),
    # ('gantt', 'Gantt'),
    # ('kanban', 'Kanban'),
    # ('search', 'Search'),
    ('qweb', 'QWeb')
]


# 导入页面
class ImportViewFileWizard(models.TransientModel):
    _name = 'acm_base.import_view_file_wizard'

    import_file = fields.Binary('file', required=True)

    import_file_name = fields.Char('file name')

    name = fields.Char("view name", required=False)

    key = fields.Char(required=True,
                      help='以key值来搜索模板，例如：模块.模板或模板id，视ir.report和模板文件中id的定义为准。')

    priority = fields.Integer(default=16, required=True)

    type = fields.Selection(VIEW_TYPE, default='qweb', string='View Type', required=True, help='导入的视图类型')

    arch_db = fields.Text(compute='_compute_arch_db', store=True)

    mode = fields.Selection([('primary', "Base view"), ('extension', "Extension View")],
                            string="View inheritance mode", default='primary', required=True,
                            help="""Only applies if this view inherits from an other one (inherit_id is not False/Null).
                                    * if extension (default), if this view is requested the closest primary view
                                    is looked up (via inherit_id), then all views inheriting from it with this
                                    view's model are applied
                                    * if primary, the closest primary view is fully resolved (even if it uses a
                                    different model than this one), then this view's inheritance specs
                                    (<xpath/>) are applied, and the result is used as if it were this view's
                                    actual arch.
                                """)

    active = fields.Boolean(default=True,
                            help="""If this view is inherited,
                                    * if True, the view always extends its parent
                                    * if False, the view currently does not extend its parent but can be enabled
                                """)

    @api.onchange('import_file')
    @api.depends('import_file')
    def _compute_arch_db(self):
        for rec in self:
            if rec.import_file:
                file_data = (str(base64.b64decode(rec.import_file).decode('utf-8')))
                if rec.type == 'qweb':
                    rec.arch_db = rec.qweb_parse(file_data)
            else:
                rec.arch_db = False

    def qweb_parse(self, data):
        data = data.replace('<?xml version="1.0" encoding="UTF-8" ?>', '')
        data = data.replace('<template id="', '<t t-name="')
        data = data.replace('</template>', '</t>')
        data = data.replace('<odoo>', '')
        data = data.replace('</odoo>', '')
        return data

    def get_arch_db(self):
        for rec in self:
            if rec.import_file:
                print(base64.b64decode(rec.import_file).decode('utf-8').split(('\n')))

    def action_import(self):
        try:
            self.ensure_one()

            res_id = self.env.context.get('self_id')
            mode = self.env['acm_base.import_view_file'].browse([res_id])
            if not mode:
                raise UserError(_('not find view_ids in context'))
            else:
                # 创建ir_ui_view记录
                value = {'name': self.name, 'key': 'custom_key.' + self.key, 'priority': self.priority, 'type': self.type,
                         'arch_db': self.arch_db, 'mode': self.mode, 'active': self.active, }
                # print(value)
                mode.view_ids = [(0, 0, value)]
                mode.message_post(body=_('{} Imported, view name: {}'.format(self.import_file_name, self.name)))
        except Exception as e:
            raise UserError(_("Import failed: %s") % str(e))
