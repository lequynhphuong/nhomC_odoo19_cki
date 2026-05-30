from odoo import models, fields, api


class StockLot(models.Model):
    _inherit = 'stock.lot'

    supplier_lot_code = fields.Char('Mã Lô Nhà Cung Cấp')
    origin_country_id = fields.Many2one('res.country', 'Xuất Xứ')
    slab_line_ids = fields.One2many(
        'stone.slab.line', 'lot_id', 'Danh Sách Tấm Đá',
    )
    total_slab_count = fields.Integer(
        'Tổng Số Tấm', compute='_compute_lot_slab_stats', store=True,
    )
    total_area_m2 = fields.Float(
        'Tổng Diện Tích (m²)', compute='_compute_lot_slab_stats', store=True, digits=(10, 4),
    )
    accepted_slab_count = fields.Integer(
        'Số Tấm Đạt', compute='_compute_lot_slab_stats', store=True,
    )
    accepted_area_m2 = fields.Float(
        'Diện Tích Đạt (m²)', compute='_compute_lot_slab_stats', store=True, digits=(10, 4),
    )
    quality_status = fields.Selection([
        ('normal', 'Đạt'),
        ('pending', 'Chờ Xử Lý'),
        ('defective', 'Lỗi'),
    ], string='Trạng Thái Chất Lượng', compute='_compute_lot_slab_stats', store=True)

    @api.depends(
        'slab_line_ids.slab_count',
        'slab_line_ids.area_m2',
        'slab_line_ids.quality_status',
    )
    def _compute_lot_slab_stats(self):
        for lot in self:
            lines = lot.slab_line_ids
            lot.total_slab_count = sum(lines.mapped('slab_count'))
            lot.total_area_m2 = sum(lines.mapped('area_m2'))

            accepted = lines.filtered(lambda l: l.quality_status == 'normal')
            lot.accepted_slab_count = sum(accepted.mapped('slab_count'))
            lot.accepted_area_m2 = sum(accepted.mapped('area_m2'))

            if not lines:
                lot.quality_status = 'normal'
            else:
                statuses = set(lines.mapped('quality_status'))
                if 'pending' in statuses:
                    lot.quality_status = 'pending'
                elif 'defective' in statuses:
                    lot.quality_status = 'defective'
                else:
                    lot.quality_status = 'normal'
