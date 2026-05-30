# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class GraniteScrapOrder(models.Model):
    _name = 'granite.scrap.order'
    _description = 'Granite Scrap Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'stock.scrap': 'scrap_id'}
    _order = 'create_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Mã phiếu', required=True, copy=False, readonly=True, default=lambda self: _('Phiếu xử lý phế phẩm (Mới)'))
    scrap_id = fields.Many2one('stock.scrap', string='Phiếu Scrap Odoo', required=True, ondelete='cascade')
    sale_order_id = fields.Many2one('sale.order', string='Đơn hàng bán (SO)', required=True)
    
    scrap_qty_tam = fields.Float(string='Số lượng tấm hỏng', related='scrap_id.scrap_qty', readonly=False, store=True)
    
    scrap_type = fields.Selection([
        ('crack', 'Nứt vỡ'),
        ('chip', 'Mẻ góc'),
        ('wrong_cut', 'Cắt sai'),
        ('other', 'Khác')
    ], string='Loại phế phẩm', required=True, default='crack')
    reason = fields.Text(string='Lý do phát sinh')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('waiting', 'Chờ xử lý'),
        ('ready', 'Chờ chuyển kho'),
        ('done', 'Hoàn tất'),
        ('cancel', 'Đã hủy')
    ], string='Trạng thái', required=True, default='draft')
    warehouse_user_id = fields.Many2one('res.users', string='Thợ kho xử lý', readonly=True)
    is_reusable = fields.Boolean(string='Có thể tái sử dụng', default=False)
    leftover_id = fields.Many2one('granite.leftover.stone', string='Bản ghi đá thừa', readonly=True)
    scrap_date = fields.Datetime(string='Ngày xử lý', readonly=True)

    length_cm = fields.Float(string='Chiều dài thực tế (cm)')
    width_cm = fields.Float(string='Chiều rộng thực tế (cm)')

    @api.model
    def default_get(self, fields_list):
        res = super(GraniteScrapOrder, self).default_get(fields_list)
        if 'location_id' not in res or not res.get('location_id'):
            warehouse = self.env['stock.warehouse'].search([], limit=1)
            if warehouse:
                res['location_id'] = warehouse.lot_stock_id.id
        if 'scrap_location_id' not in res or not res.get('scrap_location_id'):
            scrap_loc = self.env['stock.location'].search([('barcode', '=', 'KHO-PHE-PHAM')], limit=1)
            if not scrap_loc:
                try:
                    scrap_loc = self.env.ref('stock.stock_location_scrapped')
                except Exception:
                    scrap_loc = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
            if scrap_loc:
                res['scrap_location_id'] = scrap_loc.id
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Phiếu xử lý phế phẩm (Mới)')) == _('Phiếu xử lý phế phẩm (Mới)'):
                vals['name'] = self.env['ir.sequence'].next_by_code('granite.scrap.order') or _('Phiếu xử lý phế phẩm (Mới)')
            
            if 'scrap_qty_tam' in vals and 'scrap_qty' not in vals:
                vals['scrap_qty'] = vals['scrap_qty_tam']
                
            if 'product_id' in vals and ('product_uom_id' not in vals or not vals.get('product_uom_id')):
                product = self.env['product.product'].browse(vals['product_id'])
                vals['product_uom_id'] = product.uom_id.id
                
            if 'location_id' not in vals:
                warehouse = self.env['stock.warehouse'].search([], limit=1)
                if warehouse:
                    vals['location_id'] = warehouse.lot_stock_id.id
            if 'scrap_location_id' not in vals:
                scrap_loc = self.env['stock.location'].search([('barcode', '=', 'KHO-PHE-PHAM')], limit=1)
                if not scrap_loc:
                    try:
                        scrap_loc = self.env.ref('stock.stock_location_scrapped')
                    except Exception:
                        scrap_loc = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
                if scrap_loc:
                    vals['scrap_location_id'] = scrap_loc.id
        return super(GraniteScrapOrder, self).create(vals_list)

    def write(self, vals):
        if 'scrap_qty_tam' in vals:
            vals['scrap_qty'] = vals['scrap_qty_tam']
        return super(GraniteScrapOrder, self).write(vals)

    def action_confirm_scrap(self):
        for rec in self:
            rec._check_scrap_qty()
            rec.write({'state': 'waiting'})
            
            warehouse_user = False
            active_users = self.env['res.users'].search([('active', '=', True)], order='id desc')
            
            for user in active_users:
                if user.has_group('stock.group_stock_user') and not user.has_group('base.group_system'):
                    warehouse_user = user
                    break
            
            if not warehouse_user:
                for user in active_users:
                    if user.has_group('stock.group_stock_user'):
                        warehouse_user = user
                        break
            
            if warehouse_user:
                rec.activity_schedule(
                    'mail.mail_activity_data_todo',
                    note=f"Thợ kho cần thẩm định chất lượng tấm đá hỏng thuộc phiếu {rec.name}.",
                    user_id=warehouse_user.id
                )
                
            if rec.sale_order_id:
                rec.sale_order_id.message_post(body=f"Thợ cắt đã gửi yêu cầu duyệt phiếu phế phẩm tấm đá: {rec.name}.")

    def _check_scrap_qty(self):
        for rec in self:
            so_lines = rec.sale_order_id.order_line.filtered(lambda l: l.product_id == rec.product_id)
            if not so_lines:
                raise ValidationError(_('Sản phẩm đá hoa cương này không tồn tại trong danh mục mặt hàng của Đơn bán hàng gốc.'))
            
            total_ordered_tam = sum(line.product_uom_qty for line in so_lines)
            
            existing_scrap_tam = sum(
                order.scrap_qty_tam for order in self.search([
                    ('sale_order_id', '=', rec.sale_order_id.id),
                    ('product_id', '=', rec.product_id.id),
                    ('id', '!=', rec.id),
                    ('state', '!=', 'cancel')
                ])
            )
            if existing_scrap_tam + rec.scrap_qty_tam > total_ordered_tam:
                raise ValidationError(_('Số lượng tấm đá khai báo báo hỏng vượt quá hạn mức tổng số lượng tấm đặt hàng trên SO gốc.'))

    # SỬA ĐỔI LUỒNG HỦY: Chuyển sang Chờ chuyển kho (Ready) thay vì nhảy thẳng về Hoàn tất (Done)
    def action_validate_scrap(self):
        self.ensure_one()
        self.write({
            'state': 'ready',
            'is_reusable': False,
            'warehouse_user_id': self.env.user.id,
        })
        if self.sale_order_id:
            self.sale_order_id.message_post(body=f"Thợ kho đã duyệt HỦY phế phẩm đá cho phiếu {self.name}. Chờ thợ gia công chuyển vào Kho Phế Phẩm.")

    def action_validate_reusable(self):
        self.ensure_one()
        if self.length_cm <= 0 or self.width_cm <= 0:
            raise ValidationError(_('Yêu cầu nhập Chiều dài và Chiều rộng thực tế lớn hơn 0 để làm căn cứ tái sử dụng.'))
        
        location_dest = self.env['stock.location'].search([('barcode', '=', 'KHO-DA-THUA')], limit=1)
        if not location_dest:
            raise ValidationError(_('Không tồn tại bản ghi Kho Đá Thừa trên hệ thống.'))

        self.write({
            'state': 'ready',
            'is_reusable': True,
            'warehouse_user_id': self.env.user.id
        })

        leftover = self.env['granite.leftover.stone'].create({
            'scrap_order_id': self.id,
            'product_id': self.product_id.id,
            'length_cm': self.length_cm,
            'width_cm': self.width_cm,
            'stone_location_id': location_dest.id,
            'state': 'available'
        })
        self.write({'leftover_id': leftover.id})

        picking_type = self.env['stock.picking.type'].search([('code', '=', 'internal')], limit=1)
        src_location = self.env['stock.warehouse'].search([], limit=1).lot_stock_id
        
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id if picking_type else False,
            'location_id': src_location.id if src_location else self.location_id.id,
            'location_dest_id': location_dest.id,
            'origin': self.name,
        })

        self.env['stock.move'].create({
            'product_id': self.product_id.id,
            'product_uom_qty': self.scrap_qty_tam,
            'product_uom': self.product_id.uom_id.id,
            'location_id': picking.location_id.id,
            'location_dest_id': picking.location_dest_id.id,
            'picking_id': picking.id,
        })
        if self.sale_order_id:
            self.sale_order_id.message_post(body=f"Thợ kho đã duyệt TÁI CHẾ tấm đá thừa cho phiếu {self.name}. Chờ thợ gia công xếp kệ.")

    # ĐỒNG BỘ NÚT HOÀN TẤT CUỐI CÙNG: Xử lý đóng kho dựa theo từng nhánh (Hủy / Tái chế)
    def action_confirm_transferred(self):
        self.ensure_one()
        if not self.is_reusable:
            # Nhánh Hủy: Đến bước này mới kích hoạt trừ kho vật lý đẩy vào Virtual Kho phế phẩm của Odoo core
            scrap_loc = self.env['stock.location'].search([('barcode', '=', 'KHO-PHE-PHAM')], limit=1)
            if not scrap_loc:
                try:
                    scrap_loc = self.env.ref('stock.stock_location_scrapped')
                except Exception:
                    scrap_loc = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
            
            if self.scrap_id:
                self.scrap_id.write({
                    'scrap_qty': self.scrap_qty_tam,
                    'scrap_location_id': scrap_loc.id if scrap_loc else False
                })
                self.scrap_id.action_validate()
        else:
            # Nhánh Tái chế: Validate phiếu luân chuyển nội bộ vào Kho đá thừa như cũ
            picking = self.env['stock.picking'].search([('origin', '=', self.name), ('state', '!=', 'done')], limit=1)
            if picking:
                picking.action_assign()
                picking.button_validate()
                
        self.write({
            'state': 'done',
            'scrap_date': fields.Datetime.now()
        })
        if self.sale_order_id:
            msg = "Mảnh đá phế thải" if not self.is_reusable else "Mảnh đá thừa tái chế"
            loc_name = "Kho Phế Phẩm Đá" if not self.is_reusable else "Kho Đá Thừa"
            self.sale_order_id.message_post(body=f"Hệ thống ghi nhận: {msg} của phiếu {self.name} đã được dọn xếp vào {loc_name} thực tế hoàn tất.")