# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ApprovalThread(models.AbstractModel):
    """
    Approval Thread Model
    Defines the common fields and methods for approval processes
    """
    _name = "approval.thread"
    _description = "Approval Thread"

    is_wizard = fields.Boolean(string='向导模式', default=False)

    target_id = fields.Integer(compute='_compute_target_ref')
    target_model = fields.Char(compute='_compute_target_ref')

    # 设置的审批流程是否都通过，由计算方法得到，全部通过才为True
    approval_is_passed = fields.Boolean(
        string='Approval Passed', default=False,
        readonly=True,
        copy=False, compute='_compute_approval_is_passed',
        help='Indicates if the approval process has passed')

    # 该审批的目的备注
    approval_comment = fields.Text(
        string='Approval Comment', compute="_get_approval_comment", inverse="_set_approval_comment", tracking=True,
        help='Comment provided by the approver')

    # 需要审批的条目，可以是按顺序由职位高低，也可以是各核心领导的审批
    approval_item_ids = fields.Many2many(
        comodel_name='approval.item', relation='approval_thread_item_ref', column1='approval_thread_id',
        column2='approval_item_id',
        string='Approval Item',
        help='Approval Item associated with this approval process')

    # 挑出一组审批记录来待操作
    approval_history_id = fields.Many2one(
        comodel_name='approval.history',
        string='Approval History',
        domain="[('res_model','=', target_model),('res_id','=',target_id)]", tracking=True,
        help='Approval History associated with this approval process')

    # 该审批的审批历史记录，记录每个审批的审批人、审批时间、审批结果、审批备注等，每一条记录为一次审批流程，每一条记录中也存储这一组approval_item_ids条目。
    # 多条记录则是对应一个表单需要多次审批的场景
    approval_history_ids = fields.One2many(
        comodel_name='approval.history',
        inverse_name='res_id',
        string='Approval Histories',
    )

    def _compute_target_ref(self):
        for rec in self:
            rec.target_id = self.id or 0
            rec.target_model = self._name or False

    def _compute_approval_is_passed(self):
        """
        计算当前审批组是否全数通过
        """
        for rec in self:
            # rec.approval_is_passed = self.env['approval.history'].search(
            #     [('res_id', '=', rec.id),('res_model','=',self._name)],order='create_date DESC',limit=1).compute_approval_status()
            rec.approval_is_passed = rec.approval_history_id.compute_approval_status()

    @api.onchange('approval_history_id')
    def _get_approval_comment(self):
        """
        获取当前审批组目的
        """
        for rec in self:
            if rec.approval_history_id:
                rec.approval_comment = rec.approval_history_id.approval_comment
            else:
                rec.approval_comment = False

    def _set_approval_comment(self):
        """
        更新当前审批组目的
        """
        for rec in self:
            if rec.approval_history_id:
                rec.approval_history_id.approval_comment = rec.approval_comment

    @api.onchange('approval_history_id')
    def _compute_approval_item_ids(self):
        """
        approval_history_id变动时，会计算出approval_history_id中原始条目，将原始条目的ids关联到approval_item_ids 字段
        """
        for rec in self:
            # 获取最新创建的approval.history记录
            # latest_history = record.approval_history_ids.sorted('create_date desc')[:1]
            latest_history = rec.approval_history_id
            # print([(6, 0, latest_history.approval_item_ids.ids)])
            if latest_history:
                # 将approval_item_ids赋值给目标字段
                rec.approval_item_ids = [(6, 0, latest_history.approval_item_ids.ids)]
            else:
                rec.approval_item_ids = False

    @api.model
    def create(self, vals_list):
        for one_vals in vals_list:
            print(one_vals)

    # ------------------------------------------------------
    # History API
    # ------------------------------------------------------
    def action_update_approval_item_ids(self):
        self.ensure_one()
        return self._compute_approval_item_ids()

    def action_self_by_wizard(self):
        self.ensure_one()
        if not self.approval_history_id:
            raise UserError(_('请选择 Approval History'))

        return {
            'name': '修改审批',
            'type': 'ir.actions.act_window',
            'res_model': 'approval.history',
            'res_id': self.approval_history_id.id,
            'view_mode': 'form',  # 指定form视图
            'view_id': self.env.ref('approval.view_form_approval_history_wizard').id,  # 指定具体form视图的XML ID
            'target': 'new',
            # 'context': {
            #     'default_is_sequence': self.approval_history_id.is_sequence,
            #     'default_approval_comment': self.approval_history_id.approval_comment,
            #     'default_approval_item_ids': [(6, 0, self.approval_history_id.approval_item_ids.ids)]
            # }
        }
