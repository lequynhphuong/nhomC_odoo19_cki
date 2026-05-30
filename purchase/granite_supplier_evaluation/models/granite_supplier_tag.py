from odoo import models, fields


class GraniteSupplierTag(models.Model):
    _name = 'granite.supplier.tag'
    _description = 'Nhãn Nhà Cung Cấp Đá'
    _order = 'name'

    name = fields.Char(
        string='Tên Nhãn',
        required=True,
        translate=True,
    )
    color = fields.Integer(
        string='Màu',
        default=0,
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Tên nhãn phải là duy nhất!'),
    ]