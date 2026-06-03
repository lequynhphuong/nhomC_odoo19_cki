from odoo import api, fields, models


class StockLot(models.Model):
    _inherit = 'stock.lot'

    supplier_id = fields.Many2one('res.partner', string='Supplier', domain=[('supplier_rank', '>', 0)])
    length = fields.Float(string='Length (m)', digits=(16, 2))
    width = fields.Float(string='Width (m)', digits=(16, 2))
    area_m2 = fields.Float(string='Area (m²)', compute='_compute_area_m2', store=True, readonly=True, digits=(16, 4))

    @api.depends('length', 'width')
    def _compute_area_m2(self):
        for lot in self:
            lot.area_m2 = round((lot.length or 0.0) * (lot.width or 0.0), 4) if (lot.length or 0.0) and (lot.width or 0.0) else 0.0
