from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_slab_product = fields.Boolean(
        'Là Sản Phẩm Đá',
        default=False,
        help='Tích để đánh dấu sản phẩm này là đá tự nhiên cần quản lý theo tấm.',
    )
    requires_dimension_input = fields.Boolean(
        'Bắt Buộc Nhập Kích Thước',
        default=False,
        help='Nếu bật, phiếu nhập kho bắt buộc phải có ít nhất một slab line trước khi xác nhận.',
    )

    @api.onchange('is_slab_product')
    def _onchange_is_slab_product(self):
        if self.is_slab_product:
            self.tracking = 'lot'

    @api.constrains('is_slab_product', 'tracking')
    def _check_slab_product_tracking(self):
        for tmpl in self:
            if tmpl.is_slab_product and tmpl.tracking != 'lot':
                raise ValidationError(
                    'Sản phẩm đá (Slab Product) phải được theo dõi theo Lô hàng (Lot). '
                    'Không được dùng Serial Number hoặc None cho sản phẩm đá.'
                )
