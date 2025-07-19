# -*- coding: utf-8 -*-
from odoo import models, fields


class ApprovalTestForm(models.Model):
    _name = "approval.test.form"
    _inherit = ['approval.thread', 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', tracking=True)

    state = fields.Selection(selection=[('draft', 'Draft'), ('aflow1', 'Approval-1'), ('open', 'Open'), ('aflow2', 'Approval-2'), ('close','Close')], default='draft')

