from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        """Override: Sau khi validate Receipt, tự động mở wizard đánh giá."""
        result = super().button_validate()

        # Chỉ trigger cho Receipt (incoming) có liên kết PO
        purchase_pickings = self.filtered(
            lambda p: p.picking_type_code == 'incoming'
            and p.purchase_id
            and p.state == 'done'
        )

        if purchase_pickings and len(purchase_pickings) == 1:
            picking = purchase_pickings[0]
            # Kiểm tra chưa có đánh giá
            existing = self.env['granite.supplier.evaluation'].search([
                ('stock_picking_id', '=', picking.id)
            ], limit=1)
            if not existing:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'supplier.evaluation.wizard',
                    'view_mode': 'form',
                    'target': 'new',
                    'context': {
                        'default_stock_picking_id': picking.id,
                        'default_partner_id': picking.partner_id.id,
                        'default_purchase_order_id': picking.purchase_id.id,
                    },
                }

        return result