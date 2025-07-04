# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ApprovalTestForm(models.Model):
    _name = "approval.test.form"
    _inherit = ['approval.thread']

    name = fields.Char(string='Name')

