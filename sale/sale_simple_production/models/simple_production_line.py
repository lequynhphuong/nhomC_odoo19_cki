from odoo import models, fields


class SimpleProductionLine(models.Model):
    _name = 'simple.production.line'
    _description = 'Dòng Phiếu Sản Xuất'

    production_id = fields.Many2one(
        'simple.production', 'Phiếu Sản Xuất', required=True, ondelete='cascade',
    )
    product_id = fields.Many2one('product.product', 'Sản Phẩm', required=True)
    product_uom_qty = fields.Float('Số Lượng', default=1.0, required=True)
    product_uom_id = fields.Many2one('uom.uom', 'Đơn Vị')
    note = fields.Char('Ghi Chú')
