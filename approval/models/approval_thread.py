# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ApprovalThread(models.AbstractModel):
    """
    Approval Thread Model
    Defines the common fields and methods for approval processes
    """
    _name = "approval.thread"
    _description = "Approval Thread"

    approval_is_passed = fields.Boolean(
        string='Approval Passed',default=False,
        readonly=True,
        copy=False, compute='_compute_approval_is_passed',
        help='Indicates if the approval process has passed')

    approval_comment = fields.Text(
        string='Approval Comment',
        help='Comment provided by the approver')

    approval_item_ids = fields.One2many(
        comodel_name='approval.item',
        inverse_name='approval_thread_id',
        string='Approval Item',compute='_compute_approval_item_ids',
        help='Approval Item associated with this approval process')

    approval_history_ids = fields.One2many(
        comodel_name='approval.history',
        inverse_name='res_id',
        string='Approval Histories',
        domain=[('res_model', '=', _name)])

    def _compute_approval_is_passed(self):
        for rec in self:
            rec.approval_is_passed = self.env['approval.history'].search(
                [('res_id', '=', rec.id),('res_model','=',self._name)],order='create_date DESC',limit=1).compute_approval_status()
            # record.approval_is_passed = record.approval_history_ids[-1].compute_approval_status()

    @api.onchange('approval_comment')
    def onchange_approval_comment(self):
        """
        Odoo 默认排序 ：Odoo 的 One2many 字段默认按 id 升序排列（从小到大），所以 [-1] 确实会获取最后创建的记录
        """
        for rec in self:
            self.env['approval.history'].search(
                [('res_id', '=', rec.id),('res_model','=',self._name)], order='create_date DESC', limit=1).approval_comment = rec.approval_comment

    @api.depends('approval_history_ids')
    def _compute_approval_item_ids(self):
        """
        计算 approval_item_ids 字段的值
        """
        for record in self:
            # 获取最新创建的approval.history记录
            latest_history = record.approval_history_ids.sorted('create_date desc')[:1]
            print([(6,0,latest_history.approval_item_ids.ids)])
            if latest_history:
                # 将approval_item_ids赋值给目标字段
                record.approval_item_ids = [(6,0,latest_history.approval_item_ids.ids)]
            else:
                record.approval_item_ids = False

    # ------------------------------------------------------
    # History API
    # ------------------------------------------------------

    def Approval_add_new_item(self, comment, items, **kwargs):
        """
        'items': [[0, 0, {'sequence': 1, 'approval_thread_id': False, 'approval_history_id': False, '
                            role': '起草', 'group_ids': [[6, False, [14, 13]]], 'user_ids': [[6, False, [2]]],
                            'approval_comment': '12345'}], ..., ...]
        """
        self.env['approval.history']._insert_items(self._name, self.id, comment, items, **kwargs)

        return True

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