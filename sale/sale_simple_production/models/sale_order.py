from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    production_ids = fields.One2many(
        'simple.production', 'sale_order_id', 'Phiếu Sản Xuất',
    )
    production_count = fields.Integer(
        'Số Phiếu SX', compute='_compute_production_count',
    )

    @api.depends('production_ids')
    def _compute_production_count(self):
        for order in self:
            order.production_count = len(order.production_ids)

    def action_create_production(self):
        self.ensure_one()
        lines = [(0, 0, {
            'product_id': line.product_id.id,
            'product_uom_qty': line.product_uom_qty,
            'product_uom_id': line.product_uom_id.id,
        }) for line in self.order_line if line.product_id and not line.display_type]

        production = self.env['simple.production'].create({
            'sale_order_id': self.id,
            'line_ids': lines,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'simple.production',
            'view_mode': 'form',
            'res_id': production.id,
        }

    def action_view_productions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Phiếu Sản Xuất',
            'res_model': 'simple.production',
            'view_mode': 'list,form',
            'domain': [('sale_order_id', '=', self.id)],
            'context': {'default_sale_order_id': self.id},
        }
