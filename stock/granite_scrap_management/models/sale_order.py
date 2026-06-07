# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    scrap_order_ids = fields.One2many('granite.scrap.order', 'sale_order_id', string='Danh sách phiếu phế phẩm')
    scrap_order_count = fields.Integer(string='Số lượng phiếu phế phẩm', compute='_compute_scrap_order_count', store=True)

    @api.depends('scrap_order_ids')
    def _compute_scrap_order_count(self):
        for rec in self:
            rec.scrap_order_count = len(rec.scrap_order_ids)

    def action_open_scrap_wizard(self):
        self.ensure_one()
        # Lọc danh sách ID các sản phẩm đá có trong đơn hàng để truyền bộ lọc sang cho Wizard chọn nhanh
        product_ids = self.order_line.mapped('product_id').ids
        return {
            'name': 'Khai báo xử lý biến cố phế phẩm đá',
            'type': 'ir.actions.act_window',
            'res_model': 'granite.scrap.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'allowed_product_ids': product_ids
            }
        }