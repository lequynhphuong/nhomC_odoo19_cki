from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    length = fields.Float(string='Length (m)', digits=(16, 2))
    width = fields.Float(string='Width (m)', digits=(16, 2))
    area_m2 = fields.Float(string='Area (m²)', compute='_compute_area_m2', store=True, readonly=True, digits=(16, 4))

    @api.depends('length', 'width')
    def _compute_area_m2(self):
        for line in self:
            line.area_m2 = round((line.length or 0.0) * (line.width or 0.0), 4) if (line.length or 0.0) and (line.width or 0.0) else 0.0

    @api.onchange('lot_id')
    def _onchange_lot_id(self):
        if self.lot_id:
            self.length = self.lot_id.length if self.lot_id.length else self.length
            self.width = self.lot_id.width if self.lot_id.width else self.width

    def create(self, vals):
        record = super().create(vals)
        if record.lot_id and ('length' in vals or 'width' in vals):
            update = {}
            if 'length' in vals and vals['length'] is not None:
                update['length'] = vals['length']
            if 'width' in vals and vals['width'] is not None:
                update['width'] = vals['width']
            if update:
                record.lot_id.write(update)
        return record

    def write(self, vals):
        res = super().write(vals)
        for line in self:
            if line.lot_id and ('length' in vals or 'width' in vals):
                update = {}
                if 'length' in vals and vals['length'] is not None:
                    update['length'] = vals['length']
                if 'width' in vals and vals['width'] is not None:
                    update['width'] = vals['width']
                if update:
                    line.lot_id.write(update)
        return res
