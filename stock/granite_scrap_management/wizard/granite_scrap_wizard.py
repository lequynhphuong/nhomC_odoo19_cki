# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class GraniteScrapWizard(models.TransientModel):
    _name = 'granite.scrap.wizard'
    _description = 'Wizard Khai Báo Phế Phẩm Từ SO'

    sale_order_id = fields.Many2one('sale.order', string='Đơn hàng bán gốc', readonly=True)
    product_id = fields.Many2one('product.product', string='Sản phẩm đá bị hỏng', required=True)
    
    scrap_type = fields.Selection([
        ('crack', 'Nứt vỡ'),
        ('chip', 'Mẻ góc'),
        ('wrong_cut', 'Cắt sai'),
        ('other', 'Khác')
    ], string='Loại phế phẩm', required=True, default='crack')
    
    # ĐỒNG BỘ: Đổi trường nhập liệu từ m2 sang số Tấm đá hỏng của thợ cắt
    scrap_qty_tam = fields.Float(string='Số lượng tấm hỏng', required=True, default=1.0)
    reason = fields.Text(string='Mô tả lý do hỏng đá')

    def action_create_scrap(self):
        self.ensure_one()
        if self.scrap_qty_tam <= 0:
            raise ValidationError(_('Số lượng tấm đá hỏng khai báo bắt buộc phải lớn hơn 0.'))
        
        src_loc = self.env['stock.warehouse'].search([], limit=1).lot_stock_id.id
        scrap_loc = self.env['stock.location'].search([('barcode', '=', 'KHO-PHE-PHAM')], limit=1)
        if not scrap_loc:
            try:
                scrap_loc = self.env.ref('stock.stock_location_scrapped')
            except Exception:
                scrap_loc = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
        
        # Áp dụng cơ chế Delegation Inheritance tạo đồng thời bản ghi cha con cực kỳ an toàn
        scrap_custom_order = self.env['granite.scrap.order'].create({
            'sale_order_id': self.sale_order_id.id,
            'product_id': self.product_id.id,
            'scrap_type': self.scrap_type,
            'scrap_qty_tam': self.scrap_qty_tam,
            'reason': self.reason,
            'location_id': src_loc,
            'scrap_location_id': scrap_loc.id if scrap_loc else False,
            'state': 'draft'
        })
        
        scrap_custom_order.action_confirm_scrap()

        return {
            'name': 'Chi tiết phiếu phế phẩm',
            'type': 'ir.actions.act_window',
            'res_model': 'granite.scrap.order',
            'view_mode': 'form',
            'res_id': scrap_custom_order.id,
            'target': 'current',
        }