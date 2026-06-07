from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    length = fields.Float(string='Length (m)', digits=(16, 2))
    width = fields.Float(string='Width (m)', digits=(16, 2))
    area_m2 = fields.Float(string='Area (m²)', digits=(16, 4))

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super()._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        vals.update({
            'length': self.length,
            'width': self.width,
            'area_m2': self.area_m2,
        })
        return vals
