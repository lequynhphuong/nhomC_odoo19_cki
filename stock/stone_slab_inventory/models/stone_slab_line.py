from odoo import models, fields, api
from odoo.exceptions import ValidationError


class StoneSLabLine(models.Model):
    _name = 'stone.slab.line'
    _description = 'Stone Slab Line'
    _order = 'lot_id, id'

    lot_id = fields.Many2one(
        'stock.lot', 'Lô Hàng', required=True, ondelete='cascade', index=True,
    )
    product_id = fields.Many2one(
        'product.product', 'Sản Phẩm',
        related='lot_id.product_id', store=True, readonly=True,
    )
    sku_code = fields.Char(
        'SKU', related='product_id.default_code', store=True, readonly=True,
    )
    picking_id = fields.Many2one(
        'stock.picking', 'Phiếu Nhập Kho', ondelete='set null', index=True,
    )
    length_cm = fields.Float('Chiều Dài (cm)', required=True, digits=(10, 2))
    width_cm = fields.Float('Chiều Rộng (cm)', required=True, digits=(10, 2))
    slab_count = fields.Integer('Số Tấm', default=1, required=True)
    area_m2 = fields.Float(
        'Diện Tích (m²)',
        compute='_compute_area_m2',
        store=True,
        readonly=True,
        digits=(10, 4),
    )
    quality_status = fields.Selection([
        ('normal', 'Đạt'),
        ('pending', 'Chờ Xử Lý'),
        ('defective', 'Lỗi'),
    ], string='Chất Lượng', default='normal', required=True)
    location_id = fields.Many2one(
        'stock.location', 'Vị Trí Kho',
        domain="[('usage', '=', 'internal')]",
    )
    note = fields.Text('Ghi Chú')
    company_id = fields.Many2one(
        'res.company', 'Công Ty',
        related='lot_id.company_id', store=True, readonly=True,
    )
    active = fields.Boolean('Hiệu Lực', default=True)

    @api.depends('length_cm', 'width_cm', 'slab_count')
    def _compute_area_m2(self):
        for line in self:
            line.area_m2 = line.length_cm * line.width_cm * line.slab_count / 10000.0

    @api.constrains('length_cm', 'width_cm', 'slab_count')
    def _check_dimensions(self):
        for line in self:
            if line.length_cm <= 0:
                raise ValidationError('Chiều dài phải lớn hơn 0.')
            if line.width_cm <= 0:
                raise ValidationError('Chiều rộng phải lớn hơn 0.')
            if line.slab_count <= 0:
                raise ValidationError('Số tấm phải lớn hơn 0.')
