# -*- coding: utf-8 -*-
from odoo import models, fields, api


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

    name = fields.Char(string="approval group name")

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

    is_seq = fields.Boolean(string='is sequence approval', default=False)

    approval_item_ids = fields.One2many(
        comodel_name='approval.item',
        inverse_name='approval_history_id',
        string='Approval Item',
        help='Approval Item associated with this approval process')

    def name_get(self):
        res = []
        for rec in self:
            res.append("{}-{}".format(rec.reference, rec.name))
        return res

    def compute_approval_status(self):
        return all(item.approval_status == 'approved' for item in self.approval_item_ids)



    @api.model
    def create(self, vals_list):
        print(vals_list)
        res = super(ApprovalHistory, self).create(vals_list)
        return res

    # {'approval_item_ids': [[4, 3, False], [0, 'virtual_21', {'sequence': 2, 'approval_thread_id': False, 'approval_history_id': False, 'role': '初审', 'group_ids': [[6, False, [10, 11]]], 'user_ids': [[6, False, [2]]], 'approval_comment': '1234563'}]]}
    # {'res_model': 'stock.picking', 'res_id': 18, 'approval_comment': '1234', 'approval_item_ids': [[0, 'virtual_362', {'sequence': 1, 'approval_thread_id': False, 'approval_history_id': False, 'role': '起草', 'group_ids': [[6, False, [14, 13]]], 'user_ids': [[6, False, [2]]], 'approval_comment': '12345'}],
    # [0, 'virtual_684', {'sequence': 2, 'approval_thread_id': False, 'approval_history_id': False, 'role': '初审', 'group_ids': [[6, False, [10, 11]]], 'user_ids': [[6, False, [2]]], 'approval_comment': '1234556'}]]}
    def write(self, vals_list):
        print(vals_list)
        res = super(ApprovalHistory, self).write(vals_list)
        return res


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
        help='Related approval thread record')

    approval_history_id = fields.Many2one(
        comodel_name='approval.history',
        string='Approval History',
        ondelete='cascade',
        help='Related approval history record')

    sequence = fields.Integer(
        string='Sequence',
        default=1,
        help='Defines the order of approval stages')

    role = fields.Char(
        string='role',
        required=True,
        help='role of this approval stage')

    group_ids = fields.Many2many(
        comodel_name='res.groups',
        relation='approval_item_group_rel',
        column1='approval_item_id',
        column2='group_id',
        string='Authorized Groups',
        help='User groups that can approve this stage')

    is_authorized_approval = fields.Boolean(string='Authorized', default=False,
                                            compute='_compute_is_authorized_approval')

    user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='approval_item_user_rel',
        column1='approval_item_id',
        column2='user_id',
        string='Authorized user',
        help='Specific users who can approve this stage')

    # 审批意见  审批意见可以为空
    approval_comment = fields.Text(string='Approval Comment', tracking=True)

    # 审批状态
    approval_status = fields.Selection(selection=[
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('pending', 'Pending'),
    ], string='Approval Status', default='pending',
        readonly=True, tracking=True)

    # 审批人
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Approver',
        readonly=True,
        help='User who approved this stage')

    # 审批时间
    approval_date = fields.Datetime(string='Approval Date', readonly=True, tracking=True)

    def _compute_is_authorized_approval(self):
        for rec in self:
            rec.is_authorized_approval = rec._is_user_authorized_approval()

   def _is_user_authorized_approval(self):
    """
    检查当前用户是否是授权的审批人
    使用Odoo内置方法优化群组检查
    返回True/False
    """
    current_user = self.env.user
    # 检查用户是否在user_ids中
    user_check = current_user in self.user_ids
    # 使用has_group方法检查用户是否属于任何授权群组
    group_check = any(
        current_user.has_group(f"{g._original_module}.{g.xml_id.split('.')[1]}")
        for g in self.group_ids
    )
    return user_check or group_check

    def _update_approval_status(self, status):
        """
        更新审批状态的通用方法
        """
        return self.write({
            'approval_status': status,
            'user_id': self.env.user.id,
            'approval_date': fields.Datetime.now()
        })

    def action_approve(self):
        if self._is_user_authorized_approval():
            return self._update_approval_status('approved')
        return False

    def action_pending(self):
        if self._is_user_authorized_approval():
            return self._update_approval_status('pending')
        return False

    def action_reject(self):
        if self._is_user_authorized_approval():
            return self._update_approval_status('rejected')
        return False
