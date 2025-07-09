# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ApprovalThread(models.AbstractModel):
    """
    Approval Thread Model
    Defines the common fields and methods for approval processes
    """
    _name = "approval.thread"
    _description = "Approval Thread"

    # 设置的审批流程是否都通过，由计算方法得到，全部通过才为True
    approval_is_passed = fields.Boolean(
        string='Approval Passed',default=False,
        readonly=True,
        copy=False, compute='_compute_approval_is_passed',
        help='Indicates if the approval process has passed')

    # 该审批的目的备注
    approval_comment = fields.Text(
        string='Approval Comment', compute="_get_approval_comment", inverse="_set_approval_comment",
        help='Comment provided by the approver')

    # 需要审批的条目，可以是按顺序由职位高低，也可以是各核心领导的审批
    approval_item_ids = fields.One2many(
        comodel_name='approval.item',
        inverse_name='approval_thread_id',
        string='Approval Item',compute='_compute_approval_item_ids',
        help='Approval Item associated with this approval process')
    
    # 挑出一组审批记录来待操作
    approval_history_id = fields.Many2one(
        comodel_name='approval.history',
        string='Approval History',
        domain="[('res_model','=',self._name),('res_id','=',self.id))]",
        help='Approval History associated with this approval process')

    # 该审批的审批历史记录，记录每个审批的审批人、审批时间、审批结果、审批备注等，每一条记录为一次审批流程，每一条记录中也存储这一组approval_item_ids条目。
    # 多条记录则是对应一个表单需要多次审批的场景
    approval_history_ids = fields.One2many(
        comodel_name='approval.history',
        inverse_name='res_id',
        string='Approval Histories',
        domain=[('res_model', '=', _name)])

    def _compute_approval_is_passed(self):
        """
        计算当前审批组是否全数通过
        """
        for rec in self:
            # rec.approval_is_passed = self.env['approval.history'].search(
            #     [('res_id', '=', rec.id),('res_model','=',self._name)],order='create_date DESC',limit=1).compute_approval_status()
            rec.approval_is_passed = rec.approval_history_id.compute_approval_status()

    def _get_approval_comment(self):
        """
        获取当前审批组目的
        """
        for rec in self:
            rec.approval_comment = rec.approval_history_id.approval_comment

    def _set_approval_comment(self):
        """
        更新当前审批组目的
        """
        for rec in self:
            rec.approval_history_id.approval_comment = rec.approval_comment

    @api.depends('approval_history_id')
    def _compute_approval_item_ids(self):
        """
        approval_history_id变动时，会计算出approval_history_id中原始条目，复制一份到当前表单的条目中
        计算 approval_item_ids 字段的值
        """
        for rec in self:
            # 获取最新创建的approval.history记录
            # latest_history = record.approval_history_ids.sorted('create_date desc')[:1]
            latest_history = rec.approval_history_id
            print([(6,0,latest_history.approval_item_ids.ids)])
            if latest_history:
                # 将approval_item_ids赋值给目标字段
                rec.approval_item_ids = [(6,0,latest_history.approval_item_ids.ids)]
            else:
                rec.approval_item_ids = False

    # ------------------------------------------------------
    # History API
    # ------------------------------------------------------
    def Approval_add_new_item(self, comment, items, **kwargs):
        """
        'items': [[0, 0, {'sequence': 1, 'approval_thread_id': False, 'approval_history_id': False, '
                            role': '起草', 'group_ids': [[6, False, [14, 13]]], 'user_ids': [[6, False, [2]]],
                            'approval_comment': '12345'}], ..., ...]
        """
        res = self._insert_items(self._name, self.id, comment, items, **kwargs)
        return res

    def _insert_items(self, res_model, res_id, comment, items, **kwargs):
        res = self.env['approval.history'].sudo().create(
            {'res_model': res_model, 'res_id': res_id, 'approval_comment': comment, 'approval_item_ids': items,
             'is_seq': kwargs.get('is_seq', False)})
        return res

    def action_self_by_wizard(self):
        self.ensure_one()
        return {
            'name': '修改审批',
            'type': 'ir.actions.act_window',
            'res_model': 'approval.thread',  # 向导模型为approval.thread
            'view_mode': 'form',  # 指定form视图
            'view_id': self.env.ref('approval.approval_thread_wizard_view_form').id,  # 指定具体form视图的XML ID
            'target': 'new',
            'context': {
                'default_approval_history_id': self.approval_history_id.id if self.approval_history_id else False,
                'is_wizard': True  # 添加标记表示这是向导模式
            }
        }

    # def message_unsubscribe(self, partner_ids=None, channel_ids=None):
    #     """ Remove partners from the records followers. """
    #     # not necessary for computation, but saves an access right check
    #     if not partner_ids and not channel_ids:
    #         return True
    #     user_pid = self.env.user.partner_id.id
    #     if not channel_ids and set(partner_ids) == set([user_pid]):
    #         self.check_access_rights('read')
    #         self.check_access_rule('read')
    #     else:
    #         self.check_access_rights('write')
    #         self.check_access_rule('write')
    #     self.env['mail.followers'].sudo().search([
    #         ('res_model', '=', self._name),
    #         ('res_id', 'in', self.ids),
    #         '|',
    #         ('partner_id', 'in', partner_ids or []),
    #         ('channel_id', 'in', channel_ids or [])
    #     ]).unlink()


# class ApprovalThreadWizard(models.AbstractModel):
#     """
#     Approval Thread Wizard Model
#     add or delete history and items
#     """
#     _name = "approval.thread.wizard"
#     _description = "Approval Thread Wizard"

#     # 审批历史ID
#     approval_history_id = fields.Many2one(
#         comodel_name='approval.history',
#         string='Approval History', readonly=True,
#         help='Approval History associated with this approval process')

#     # 审批目的
#     approval_comment = fields.Text(
#         string='Approval Comment',
#         help='Comment provided by the approver')