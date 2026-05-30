from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ─── Evaluation Fields ──────────────────────────────────────────
    evaluation_ids = fields.One2many(
        'granite.supplier.evaluation',
        'partner_id',
        string='Lịch Sử Đánh Giá',
    )
    evaluation_count = fields.Integer(
        string='Số Lần Đánh Giá',
        compute='_compute_evaluation_stats',
        store=True,
    )
    avg_score = fields.Float(
        string='Điểm TB',
        compute='_compute_evaluation_stats',
        store=True,
        digits=(4, 2),
    )
    supplier_tag_ids = fields.Many2many(
        'granite.supplier.tag',
        'partner_tag_rel',
        'partner_id',
        'tag_id',
        string='Nhãn Nhà Cung Cấp',
    )

    @api.depends('evaluation_ids', 'evaluation_ids.total_score')
    def _compute_evaluation_stats(self):
        for partner in self:
            evals = partner.evaluation_ids.filtered(lambda e: e.total_score > 0)
            partner.evaluation_count = len(partner.evaluation_ids)
            partner.avg_score = (
                sum(evals.mapped('total_score')) / len(evals) if evals else 0.0
            )