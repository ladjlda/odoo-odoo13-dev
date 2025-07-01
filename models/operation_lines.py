from odoo import models, fields

class OperationLines(models.AbstractModel):
    _name = 'operation.lines'
    _description = 'Operation Lines'

    picking_id = fields.Many2one('stock.picking', string='Picking')
    move_line_ids = fields.One2many('stock.move.line', string='Move Lines')