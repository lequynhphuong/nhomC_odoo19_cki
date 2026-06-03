from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    length = fields.Float(string='Length (m)', digits=(16, 2))
    width = fields.Float(string='Width (m)', digits=(16, 2))
    area_m2 = fields.Float(string='Area (m²)', compute='_compute_area_m2', store=True, readonly=True, digits=(16, 4))

    @api.depends('length', 'width')
    def _compute_area_m2(self):
        for line in self:
            line.area_m2 = round((line.length or 0.0) * (line.width or 0.0), 4) if (line.length or 0.0) and (line.width or 0.0) else 0.0

    @api.depends('length', 'width', 'area_m2', 'product_qty', 'price_unit', 'tax_ids')
    def _compute_amount(self):
        for line in self:
            qty_for_amount = (line.area_m2 or 0.0) * (line.product_qty or 0.0)
            if qty_for_amount <= 0:
                qty_for_amount = line.product_qty or 0.0
            line.price_subtotal = qty_for_amount * (line.price_unit or 0.0)
            line.price_total = line.price_subtotal
            line.price_tax = 0.0

    def _prepare_stock_moves(self, picking):
        vals_list = super()._prepare_stock_moves(picking)
        for vals in vals_list:
            vals.update({'length': self.length, 'width': self.width, 'area_m2': self.area_m2})
        return vals_list
