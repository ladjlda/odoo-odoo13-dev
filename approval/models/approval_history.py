# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ApprovalHistory(models.Model):
    """
    Approval History Model
    Tracks the approval process for documents
    """
    _name = "approval.history"
    _description = "Approval History"

    reference = fields.Char(
        string='Reference',
        readonly=True,
        help='Unique reference identifier for this approval history')

    res_model = fields.Char(
        string='Related Document Model', 
        required=True, 
        index=True,
        help='Model name of the document being approved')
        
    res_id = fields.Many2oneReference(
        string='Related Document ID', 
        index=True, 
        model_field='res_model',
        help='ID of the document being approved')

    approval_comment = fields.Text(
        string='Approval Comment',
        help='Comment provided by the approver')

    approval_item_ids = fields.One2many(
        comodel_name='approval.item',
        inverse_name='approval_history_id',
        string='Approval Item',
        help='Approval Item associated with this approval process')

    def compute_approval_status(self):
        self.ensure_one()
        return all(item.approval_status == 'approved' for item in self.approval_item_ids)

class ApprovalItem(models.Model):
    """
    Approval Stage Model
    Defines each approval stage in the workflow
    """
    _name = "approval.item"
    _description = "Approval Stage"
    _order = 'sequence, id'

    approval_thread_id = fields.Many2one(
        comodel_name='approval.thread',
        string='Approval Thread',
        ondelete='cascade',
        required=True,
        help='Related approval thread record')

    approval_history_id = fields.Many2one(
        comodel_name='approval.history',
        string='Approval History',
        ondelete='cascade',
        required=True,
        help='Related approval history record')

    sequence = fields.Integer(
        string='Sequence', 
        default=10,
        help='Defines the order of approval stages')

    name = fields.Char(
        string='Stage Name', 
        required=True,
        help='Name of this approval stage')

    group_ids = fields.Many2many(
        comodel_name='res.groups',
        relation='approval_item_group_rel',
        column1='approval_item_id',
        column2='group_id',
        string='Approver Groups',
        help='User groups that can approve this stage')

    user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='approval_item_user_rel',
        column1='approval_item_id',
        column2='user_id',
        string='Approvers',
        help='Specific users who can approve this stage')

    # 审批意见  审批意见可以为空
    approval_comment = fields.Text(string='Approval Comment', tracking=True)

    # 审批状态
    approval_status = fields.Selection([
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending'),
    ], string='Approval Status',default='pending',
        readonly=True, tracking=True)

    # 审批人
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Approver',
        readonly=True,
        help='User who approved this stage')

    # 审批时间
    approval_date = fields.Datetime(string='Approval Date',
        readonly=True, tracking=True)

    def _is_user_authorized_approver(self):
        """
        检查当前用户是否是授权的审批人
        返回True/False
        """
        self.ensure_one()
        current_user = self.env.user
        return (current_user in self.user_ids or 
                any(g in current_user.groups_id for g in self.group_ids))
    
    def _update_approval_status(self, status):
        """
        更新审批状态的通用方法
        """
        return self.write({
            'approval_status': status,
            'approver_id': self.env.user.id,
            'approval_date': fields.Datetime.now()
        })

    def action_approve(self):
        if self._is_user_authorized_approver():
            return self._update_approval_status('approved')
        return False
    
    def action_reject(self):
        if self._is_user_authorized_approver():
            return self._update_approval_status('rejected')
        return False
