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
        string='Approval Passed',
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
        for record in self:
            # record.approval_is_passed = self.env['approval.history'].search(
            #     [('id','in',record.approval_history_ids.ids)],order='create_date DESC',limit=1).compute_approval_status()
            record.approval_is_passed = record.approval_history_ids[-1].compute_approval_status()

    @api.onchange('approval_comment')
    def onchange_approval_comment(self):
        """
        Odoo 默认排序 ：Odoo 的 One2many 字段默认按 id 升序排列（从小到大），所以 [-1] 确实会获取最后创建的记录
        """
        for record in self:
            record.approval_history_ids[-1].approval_comment = record.approval_comment

    @api.depends('approval_history_ids')
    def _compute_approval_item_ids(self):
        """
        计算 approval_item_ids 字段的值
        """
        for record in self:
            # 获取最新创建的approval.history记录
            latest_history = record.approval_history_ids.sorted('create_date desc')[:1]
            if latest_history:
                # 将approval_item_ids赋值给目标字段
                record.approval_item_ids = latest_history.approval_item_ids
            else:
                record.approval_item_ids = False