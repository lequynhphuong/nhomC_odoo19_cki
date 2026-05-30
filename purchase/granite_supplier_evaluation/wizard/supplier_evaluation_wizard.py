from odoo import models, fields, api
from odoo.exceptions import UserError


class SupplierEvaluationWizard(models.TransientModel):
    _name = 'supplier.evaluation.wizard'
    _description = 'Wizard Đánh Giá Nhà Cung Cấp'

    # ─── Thông tin hiển thị (readonly) ──────────────────────────────
    stock_picking_id = fields.Many2one(
        'stock.picking',
        string='Phiếu Nhập',
        readonly=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Nhà Cung Cấp',
        readonly=True,
    )
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Đơn PO',
        readonly=True,
    )
    scheduled_date = fields.Datetime(
        string='Ngày Dự Kiến',
        related='stock_picking_id.scheduled_date',
        readonly=True,
    )
    date_done = fields.Datetime(
        string='Ngày Thực Nhận',
        related='stock_picking_id.date_done',
        readonly=True,
    )
    delivery_delay_days = fields.Integer(
        string='Số Ngày Trễ',
        compute='_compute_preview',
    )
    score_delivery_preview = fields.Float(
        string='Điểm Giao Hàng (Preview)',
        compute='_compute_preview',
        digits=(4, 2),
    )

    # ─── Input từ người dùng ────────────────────────────────────────
    score_quality = fields.Selection(
        selection=[
            ('1', '1 ★ - Rất Kém'),
            ('2', '2 ★ - Kém'),
            ('3', '3 ★ - Trung Bình'),
            ('4', '4 ★ - Tốt'),
            ('5', '5 ★ - Xuất Sắc'),
        ],
        string='Điểm Chất Lượng & Số Lượng',
        required=True,
    )
    note = fields.Text(string='Ghi Chú')
    tag_ids = fields.Many2many(
        'granite.supplier.tag',
        string='Nhãn',
    )

    # ─── Compute preview ────────────────────────────────────────────
    @api.depends('scheduled_date', 'date_done')
    def _compute_preview(self):
        for rec in self:
            if rec.scheduled_date and rec.date_done:
                delta = rec.date_done - rec.scheduled_date
                delay = delta.days
                rec.delivery_delay_days = max(delay, 0)
                if delay <= 0:
                    rec.score_delivery_preview = 5.0
                elif delay <= 2:
                    rec.score_delivery_preview = 4.0
                elif delay <= 5:
                    rec.score_delivery_preview = 3.0
                elif delay <= 10:
                    rec.score_delivery_preview = 2.0
                else:
                    rec.score_delivery_preview = 1.0
            else:
                rec.delivery_delay_days = 0
                rec.score_delivery_preview = 0.0

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        picking_id = self.env.context.get('default_stock_picking_id')
        if picking_id:
            picking = self.env['stock.picking'].browse(picking_id)
            res['stock_picking_id'] = picking.id
            res['partner_id'] = picking.partner_id.id
            # Lấy PO từ picking
            if picking.purchase_id:
                res['purchase_order_id'] = picking.purchase_id.id
        return res

    def action_save_evaluation(self):
        """Lưu đánh giá và đóng popup."""
        self.ensure_one()
        if not self.purchase_order_id:
            raise UserError(
                "Phiếu nhập này không liên kết với đơn PO. "
                "Không thể tạo đánh giá."
            )

        # Kiểm tra đã có đánh giá cho picking này chưa
        existing = self.env['granite.supplier.evaluation'].search([
            ('stock_picking_id', '=', self.stock_picking_id.id)
        ], limit=1)
        if existing:
            raise UserError(
                f"Phiếu nhập '{self.stock_picking_id.name}' đã có đánh giá "
                f"'{existing.name}'. Không thể tạo đánh giá trùng."
            )

        eval_record = self.env['granite.supplier.evaluation'].create({
            'partner_id': self.partner_id.id,
            'purchase_order_id': self.purchase_order_id.id,
            'stock_picking_id': self.stock_picking_id.id,
            'score_quality': self.score_quality,
            'note': self.note,
            'tag_ids': [(6, 0, self.tag_ids.ids)],
        })

        # Mở form record vừa tạo
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'granite.supplier.evaluation',
            'res_id': eval_record.id,
            'view_mode': 'form',
            'target': 'current',
        }