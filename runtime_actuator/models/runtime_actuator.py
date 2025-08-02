# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError


class RuntimeActuator(models.TransientModel):
    _name = "runtime.actuator"

    runtime_execution_last_date = fields.Datetime(string='最后执行时间', readonly=True)

    runtime_execution_content = fields.Many2one(comodel_name='runtime.execution.content', string='执行内容')

    def action_runtime_logic(self, parameters: dict=None):
        self.ensure_one()
        if self.runtime_execution_content:
            try:
                """
                    exec(object[, globals[, locals]])
                    参数
                        object：必选参数，表示需要被指定的 Python 代码。它必须是字符串或 code 对象。如果 object 是一个字符串，该字符串会先被解析为一组 Python 语句，然后再执行（除非发生语法错误）。如果 object 是一个 code 对象，那么它只是被简单的执行。
                        globals：可选参数，表示全局命名空间（存放全局变量），如果被提供，则必须是一个字典对象。
                        locals：可选参数，表示当前局部命名空间（存放局部变量），如果被提供，可以是任何映射对象。如果该参数被忽略，那么它将会取与 globals 相同的值。
                    返回值
                        exec 返回值永远为 None。
                """
                result = {}
                exec(self.runtime_execution_content.text, parameters, result)
                return result['result']
            except Exception as e:
                raise UserError(_('执行异常：{}'.format(e)))
            finally:
                self.runtime_execution_last_date = fields.datetime.now()
                self.runtime_execution_content.message_post(
                    body=_('res_id: {}, res_model: {}, execution_date: {}'.format(self.id, self._name,
                                                                                  fields.datetime.now())))
        else:
            raise UserError(_('执行内容不可用'))
