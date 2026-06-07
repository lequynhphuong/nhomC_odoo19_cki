# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class GraniteLeftoverStone(models.Model):
    _name = 'granite.leftover.stone'
    _description = 'Granite Leftover Stone'
    _order = 'create_date desc'

    name = fields.Char(string='Mã đá thừa', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    scrap_order_id = fields.Many2one('granite.scrap.order', string='Phiếu phế phẩm gốc', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Chất liệu đá', required=True)
    length_cm = fields.Float(string='Chiều dài (cm)', required=True)
    width_cm = fields.Float(string='Chiều rộng (cm)', required=True)
    
    # CHỈNH SỬA: Thêm thuộc tính digits=(16, 4) để Odoo cho phép hiển thị 4 chữ số thập phân siêu lẻ khi test dữ liệu nhỏ
    area_m2 = fields.Float(string='Diện tích (m2)', compute='_compute_area_m2', digits=(16, 4), store=True)
    
    stone_location_id = fields.Many2one('stock.location', string='Vị trí kho', required=True)
    state = fields.Selection([
        ('available', 'Còn hàng'),
        ('reserved', 'Đã đặt'),
        ('used', 'Đã dùng')
    ], string='Trạng thái', required=True, default='available')
    note = fields.Text(string='Ghi chú')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('granite.leftover.stone') or _('New')
        return super(GraniteLeftoverStone, self).create(vals_list)

    @api.depends('length_cm', 'width_cm')
    def _compute_area_m2(self):
        for rec in self:
            if rec.length_cm and rec.width_cm:
                rec.area_m2 = (rec.length_cm * rec.width_cm) / 10000.0
            else:
                rec.area_m2 = 0.0