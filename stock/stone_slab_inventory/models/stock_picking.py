from collections import defaultdict
from odoo import models, fields
from odoo.exceptions import ValidationError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    slab_line_ids = fields.One2many(
        'stone.slab.line', 'picking_id', 'Danh Sách Tấm Đá',
    )

    def action_sync_slab_quantity(self):
        self.ensure_one()
        if self.picking_type_code != 'incoming':
            return

        # Group accepted slab lines by (product_id, lot_id)
        groups = defaultdict(float)
        for slab in self.slab_line_ids:
            if slab.quality_status == 'normal':
                key = (slab.product_id.id, slab.lot_id.id)
                groups[key] += slab.area_m2

        for (product_id, lot_id), area in groups.items():
            product = self.env['product.product'].browse(product_id)

            # Find existing stock.move for this product in this picking
            move = self.move_ids.filtered(
                lambda m: m.product_id.id == product_id
                and m.state not in ('done', 'cancel')
            )
            if not move:
                move = self.env['stock.move'].create({
                    'name': product.display_name,
                    'product_id': product_id,
                    'product_uom': product.uom_id.id,
                    'product_uom_qty': area,
                    'picking_id': self.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'company_id': self.company_id.id,
                })
            else:
                move = move[0]
                move.product_uom_qty = area

            # Find or create stock.move.line for this product+lot
            existing_line = move.move_line_ids.filtered(
                lambda ml: ml.lot_id.id == lot_id
            )
            if existing_line:
                existing_line[0].quantity = area
            else:
                self.env['stock.move.line'].create({
                    'move_id': move.id,
                    'picking_id': self.id,
                    'product_id': product_id,
                    'lot_id': lot_id,
                    'quantity': area,
                    'product_uom_id': product.uom_id.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'company_id': self.company_id.id,
                })

    def button_validate(self):
        for picking in self:
            if picking.picking_type_code != 'incoming':
                continue

            if not picking.slab_line_ids:
                continue

            # Block if any slab line is still pending
            pending_lines = picking.slab_line_ids.filtered(
                lambda s: s.quality_status == 'pending'
            )
            if pending_lines:
                raise ValidationError(
                    'Còn %d slab line đang ở trạng thái "Chờ Xử Lý". '
                    'Vui lòng giải quyết trước khi xác nhận phiếu nhập.'
                    % len(pending_lines)
                )

            # Check requires_dimension_input for slab products without slab lines
            slab_moves = picking.move_ids.filtered(
                lambda m: m.product_id.product_tmpl_id.is_slab_product
                and m.product_id.product_tmpl_id.requires_dimension_input
            )
            for move in slab_moves:
                has_lines = picking.slab_line_ids.filtered(
                    lambda s: s.product_id.id == move.product_id.id
                )
                if not has_lines:
                    raise ValidationError(
                        'Sản phẩm "%s" bắt buộc phải nhập chi tiết kích thước tấm đá. '
                        'Vui lòng thêm Slab Lines trong tab "Chi Tiết Tấm Đá".'
                        % move.product_id.display_name
                    )

            # Verify quantities match between slab lines and move lines
            expected = defaultdict(float)
            for slab in picking.slab_line_ids:
                if slab.quality_status == 'normal' and slab.product_id and slab.lot_id:
                    key = (slab.product_id.id, slab.lot_id.id)
                    expected[key] += slab.area_m2

            if expected:
                actual = defaultdict(float)
                for ml in picking.move_line_ids:
                    if ml.lot_id and ml.product_id.product_tmpl_id.is_slab_product:
                        key = (ml.product_id.id, ml.lot_id.id)
                        actual[key] += ml.quantity

                mismatch = any(
                    abs(expected[key] - actual.get(key, 0.0)) > 0.001
                    for key in expected
                )
                if mismatch:
                    raise ValidationError(
                        'Số lượng slab lines chưa được đồng bộ vào phiếu nhập. '
                        'Vui lòng bấm "Sync Slab Quantity" trước khi xác nhận.'
                    )

        return super().button_validate()
