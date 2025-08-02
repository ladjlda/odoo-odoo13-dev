# -*- coding: utf-8 -*-
import base64

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RuntimeExecutionContent(models.Model):
    _name = "runtime.execution.content"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name')

    file = fields.Binary(string='File', attachment=False)

    origin_file = fields.Binary(string='Origin File', compute='_compute_origin_file', store=True, attachment=False)

    text = fields.Text(string='Text', compute='_compute_text', inverse='_inverse_text', store=True)

    @api.depends('file')
    def _compute_origin_file(self):
        for rec in self:
            if rec.file:
                rec.origin_file = rec.file
            else:
                rec.origin_file = False

    @api.depends('file')
    def _compute_text(self):
        for rec in self:
            if rec.file:
                rec.text = str(base64.b64decode(rec.file).decode('utf-8'))
            else:
                rec.text = False

    def _inverse_text(self):
        pass

    def reset_file(self):
        for rec in self:
            if rec.origin_file:
                rec.file = rec.origin_file
            else:
                raise UserError(_('origin file 为空'))