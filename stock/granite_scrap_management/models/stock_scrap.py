# -*- coding: utf-8 -*-
from odoo import models, fields

class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    def action_validate(self):
        res = super(StockScrap, self).action_validate()
        for scrap in self:
            order = self.env['granite.scrap.order'].search([('scrap_id', '=', scrap.id)], limit=1)
            if order and order.state != 'done':
                order.write({
                    'state': 'done',
                    'scrap_date': fields.Datetime.now(),
                    'warehouse_user_id': self.env.user.id
                })
                if order.sale_order_id:
                    order.sale_order_id.message_post(
                        body=f"Hệ thống xác nhận hoàn tất nhập kho phế phẩm từ phiếu {order.name}."
                    )
        return res