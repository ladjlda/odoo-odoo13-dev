# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ApprovalHistory(models.Model):
    """
    Approval History Model
    Tracks the approval process for documents
    """
    _name = "approval.history"
    _description = "Approval History"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    is_lock = fields.Boolean(string='Locked', default=False, readonly=True, tracking=True, help="创建后上锁，无法修改任何数据")

    reference = fields.Char(
        string='Reference',
        help='Unique reference identifier for this approval history')

    name = fields.Char(string="approval group name", tracking=True)

    res_model = fields.Char(
        string='RES Model',
        required=False,
        index=True,
        help='Model name of the document being approved')

    res_id = fields.Many2oneReference(
        string='RES ID',
        required=False,
        index=True,
        model_field='res_model',
        help='ID of the document being approved')

    approval_comment = fields.Text(
        string='Approval Comment',
        help='Comment provided by the approver', tracking=True)

    is_rule_sequence = fields.Boolean(string='is rule sequence', default=False, tracking=True)

    approval_item_ids = fields.One2many(
        comodel_name='approval.item',
        inverse_name='approval_history_id',
        string='Approval Item',
        help='Approval Item associated with this approval process')

    def name_get(self):
        res = []
        for rec in self:
            res.append((rec.id, "{}-{}".format(rec.reference, rec.name)))
        return res

    def compute_approval_status(self):
        return all(item.approval_status == 'approved' for item in self.approval_item_ids)

    @api.onchange('is_rule_sequence')
    def _check_approval_item_ids_is_sequence(self):
        for rec in self:
            if rec.is_rule_sequence and rec.approval_item_ids and len(rec.approval_item_ids) > 1:
                seqs = rec.approval_item_ids.mapped('sequence')
                print(seqs)
                for i in range(len(seqs)-1):
                    if seqs[i] + 1 != seqs[i+1]:
                        raise UserError(_('The sequence numbers of the approval process must increase in sequence and have an interval difference of 1'))

    @api.model
    def create(self, vals_list):
        print(vals_list)
        vals_list['is_lock'] = True
        res = super(ApprovalHistory, self).create(vals_list)
        res._check_approval_item_ids_is_sequence()
        return res

    # {'approval_item_ids': [[4, 3, False], [0, 'virtual_21', {'sequence': 2, 'approval_thread_id': False, 'approval_history_id': False, 'role': '初审', 'group_ids': [[6, False, [10, 11]]], 'user_ids': [[6, False, [2]]], 'approval_comment': '1234563'}]]}
    # {'res_model': 'stock.picking', 'res_id': 18, 'approval_comment': '1234', 'approval_item_ids': [[0, 'virtual_362', {'sequence': 1, 'approval_thread_id': False, 'approval_history_id': False, 'role': '起草', 'group_ids': [[6, False, [14, 13]]], 'user_ids': [[6, False, [2]]], 'approval_comment': '12345'}],
    # [0, 'virtual_684', {'sequence': 2, 'approval_thread_id': False, 'approval_history_id': False, 'role': '初审', 'group_ids': [[6, False, [10, 11]]], 'user_ids': [[6, False, [2]]], 'approval_comment': '1234556'}]]}
    def write(self, vals):
        print(vals)
        if 'is_rule_sequence' in vals.keys() and vals['is_rule_sequence']:
            self._check_approval_item_ids_is_sequence()
        res = super(ApprovalHistory, self).write(vals)
        if 'is_rule_sequence' not in vals.keys() and self.is_rule_sequence:
            self._check_approval_item_ids_is_sequence()
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
        required=True,
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

    def _check_sequence_approval(self):
        """
        针对撤销或待定的修改前的顺序检查
        """
        for rec in self:
            rel_approval_item = rec.approval_history_id.approval_item_ids
            current_seq = rec.sequence
            max_seq = max(rel_approval_item.mapped('sequence'))
            approved_item_ids = rel_approval_item.filtered(lambda x: current_seq < x.sequence <= max_seq).filtered(
                lambda y: y.approval_status == 'approved')
            if current_seq != max_seq and approved_item_ids:
                result = ["{}-{}".format(approved_item_id.sequence, approved_item_id.role) for approved_item_id in
                          approved_item_ids.sorted(key='sequence', reverse=True)]
                raise UserError(
                    _("Currently, it is in the sequential approval flow mode.\nThe current approval can only be modified when the following approvals are rejected or pending.\n{}".format(
                        '\n'.join(result))))

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
        group_check = any(current_user.id in g.users.ids for g in self.group_ids)

        return user_check or group_check or not (user_check and group_check)

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
        if self.approval_history_id.is_rule_sequence:
            rel_approval_item = self.approval_history_id.approval_item_ids
            current_seq = self.sequence
            unapproved_item_ids = rel_approval_item.filtered(lambda x: x.sequence < current_seq and not x.approval_status == 'approved')
            if current_seq != 1 and unapproved_item_ids:
                result = ["{}-{}".format(unapproved_item_id.sequence, unapproved_item_id.role) for unapproved_item_id in unapproved_item_ids]
                raise UserError(_("Currently, it is in the sequential approval flow mode.\nThe previous process has not been approved.\n{}".format('\n'.join(result))))
        if self._is_user_authorized_approval():
            return self._update_approval_status('approved')
        return False

    def action_pending(self):
        if self.approval_history_id.is_rule_sequence:
            self._check_sequence_approval()
        if self._is_user_authorized_approval():
            return self._update_approval_status('pending')
        return False

    def action_reject(self):
        if self.approval_history_id.is_rule_sequence:
            self._check_sequence_approval()
        if self._is_user_authorized_approval():
            return self._update_approval_status('rejected')
        return False
