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

    target_id = fields.Integer(compute='_compute_target_ref')
    target_model = fields.Char()

    # 控制显示隐藏审批流程板块
    is_show = fields.Boolean(default=False)

    # 设置的审批流程是否都通过，由计算方法得到，全部通过才为True
    approval_is_passed = fields.Boolean(
        string='Approval Passed', default=False,
        readonly=True, copy=False, compute='_compute_approval_is_passed',
        help='Indicates if the approval process has passed')

    # 该审批的目的备注
    # approval_comment = fields.Text(
    #     string='Approval Comment', compute="_get_approval_comment", inverse="_set_approval_comment", tracking=True,
    #     help='Comment provided by the approver')
    approval_comment = fields.Text(
        string='Approval Comment', compute="_get_approval_comment", tracking=True,
        help='Comment provided by the approver')

    # 需要审批的条目，可以是按顺序由职位高低，也可以是各核心领导的审批
    approval_item_ids = fields.Many2many(
        comodel_name='approval.item', column1='approval_thread_id',
        column2='approval_item_id',
        string='Approval Item', compute='_compute_approval_item_ids', store=False,
        help='Approval Item associated with this approval process')

    # 挑出一组审批记录来待操作
    approval_history_id = fields.Many2one(
        comodel_name='approval.history',
        string='Approval History', compute='_compute_approval_history_id', inverse='_inverse_approval_history_id',
        domain="[('res_model','=', target_model),('res_id','=',target_id)]", tracking=True,
        help='Approval History associated with this approval process')

    # 该审批的审批历史记录，记录每个审批的审批人、审批时间、审批结果、审批备注等，每一条记录为一次审批流程，每一条记录中也存储这一组approval_item_ids条目。
    # 多条记录则是对应一个表单需要多次审批的场景
    approval_history_ids = fields.One2many(
        comodel_name='approval.history',
        inverse_name='res_id',
        string='Approval Histories',
    )

    # 为了通用适配的特性，保持子类继承后能识别到记录的阶段stage切换，将子类的阶段字段名赋值给stage_field，后续的处理方法会以stage_field去匹配子类的阶段字段值去处理
    # 要被当前父类approval.thread模型识别上阶段，规定阶段名只能是以'aflow'开头和整型的数字结尾，间隔阶段之间数字步长为1，以代表第几个审批阶段，例如：aflow1、aflow2、aflow3、
    stage_field = fields.Char(string='ref state field', default='state', readonly=False)

    flow_current_state = fields.Char(compute='_compute_state_value')

    def visible_approval_flow_panel(self):
        self.ensure_one()
        if self.is_show:
            self.is_show = False
        else:
            self.is_show = True

    def _compute_state_value(self):
        for rec in self:
            if rec.stage_field in self.fields_get_keys():
                rec.flow_current_state = rec.read(fields=[rec.stage_field])[0][rec.stage_field]
            else:
                rec.flow_current_state = False

    def _check_state_value(self):
        self.ensure_one()
        if self.flow_current_state.startswith('aflow') and isinstance(eval(self.flow_current_state[5:]), int):
            return True
        else:
            return False

    def _compute_approval_history_id(self):
        for rec in self:
            if rec._check_state_value():
                sequence = int(rec.flow_current_state[5:])
                rec.approval_history_id = rec.approval_history_ids.sorted(key='sequence')[sequence-1].id
                rec._compute_approval_item_ids()
            else:
                rec.approval_history_id = False

    def _inverse_approval_history_id(self):
        pass

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

    # @api.onchange('approval_history_id')
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

    # @api.depends('approval_history_id')
    @api.onchange('approval_history_id')
    def _compute_approval_item_ids(self):
        """
        approval_history_id变动时，会计算出approval_history_id中原始条目，将原始条目的ids关联到approval_item_ids 字段
        """
        for rec in self:
            # 获取最新创建的approval.history记录
            if rec.approval_history_id:
                # 将approval_item_ids赋值给目标字段
                rec.approval_item_ids = [(6, 0, rec.approval_history_id.approval_item_ids.ids)]
            else:
                rec.approval_item_ids = False

    # @api.model
    # def create(self, vals_list):
    #     for one_vals in vals_list:
    #         print(one_vals)

    # ------------------------------------------------------
    # History API
    # ------------------------------------------------------
    def action_update_approval_item_ids(self):
        self.ensure_one()
        return self._compute_approval_item_ids()

    def action_modify_history_wizard(self):
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

    # def action_approval_flow_panel_wizard(self):
    #     self.ensure_one()
    #     if not self.approval_history_id:
    #         raise UserError(_('请选择 Approval History'))
    #
    #     return {
    #         'name': '审批',
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'approval.history',
    #         'res_id': self.approval_history_id.id,
    #         'view_mode': 'form',  # 指定form视图
    #         'view_id': self.env.ref('approval.view_form_approval_flow_panel_wizard').id,  # 指定具体form视图的XML ID
    #         'target': 'current',
    #
    #     }
