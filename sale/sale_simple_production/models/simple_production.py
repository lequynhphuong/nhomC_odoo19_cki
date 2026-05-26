from odoo import models, fields, api


class SimpleProduction(models.Model):
    _name = 'simple.production'
    _description = 'Phiếu Sản Xuất Đơn Giản'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        'Mã Phiếu', required=True, readonly=True,
        default='New', copy=False, tracking=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order', 'Đơn Hàng', readonly=True, ondelete='restrict',
    )
    partner_id = fields.Many2one(
        'res.partner', 'Khách Hàng',
        related='sale_order_id.partner_id', store=True,
    )
    date_planned = fields.Date('Ngày Sản Xuất Dự Kiến')
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã Xác Nhận'),
        ('done', 'Hoàn Thành'),
        ('cancel', 'Đã Hủy'),
    ], string='Trạng Thái', default='draft', tracking=True)
    line_ids = fields.One2many(
        'simple.production.line', 'production_id', 'Sản Phẩm Cần Sản Xuất',
    )
    note = fields.Text('Ghi Chú')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('simple.production') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})
