from odoo import models, fields, api
from odoo.exceptions import ValidationError


class GraniteSupplierEvaluation(models.Model):
    _name = 'granite.supplier.evaluation'
    _description = 'Granite Supplier Evaluation'
    _order = 'evaluation_date desc, id desc'
    _rec_name = 'name'

    name = fields.Char(
        string='Evaluation Code',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code(
            'granite.supplier.evaluation'
        ) or 'EVAL/NEW',
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Supplier',
        required=True,
        ondelete='restrict',
    )
    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order (PO)',
        required=True,
        ondelete='restrict',
    )
    stock_picking_id = fields.Many2one(
        'stock.picking',
        string='Receipt (Picking)',
        required=True,
        ondelete='restrict',
    )
    evaluation_date = fields.Date(
        string='Evaluation Date',
        default=fields.Date.today,
        required=True,
    )
    note = fields.Text(string='Notes')
    tag_ids = fields.Many2many(
        'granite.supplier.tag',
        'evaluation_tag_rel',
        'evaluation_id',
        'tag_id',
        string='Tags',
    )

    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        related='stock_picking_id.scheduled_date',
        store=True,
    )
    date_done = fields.Datetime(
        string='Effective Date',
        related='stock_picking_id.date_done',
        store=True,
    )
    delivery_delay_days = fields.Integer(
        string='Delay Days',
        compute='_compute_delivery_score',
        store=True,
    )
    score_delivery = fields.Float(
        string='Delivery Score',
        compute='_compute_delivery_score',
        store=True,
        digits=(4, 2),
    )

    score_quality = fields.Selection(
        selection=[
            ('1', '1 ★ - Very Poor'),
            ('2', '2 ★ - Poor'),
            ('3', '3 ★ - Average'),
            ('4', '4 ★ - Good'),
            ('5', '5 ★ - Excellent'),
        ],
        string='Quality Score (Selection)',
        required=True,
    )
    score_quality_float = fields.Float(
        string='Quality Score',
        compute='_compute_quality_score_float',
        store=True,
    )

    po_unit_price = fields.Float(
        string='PO Unit Price (VND)',
        compute='_compute_price_score',
        store=True,
        digits=(16, 0),
    )
    avg_price_market = fields.Float(
        string='Avg Market Price (VND)',
        compute='_compute_price_score',
        store=True,
        digits=(16, 0),
    )
    price_diff_percent = fields.Float(
        string='Price Difference (%)',
        compute='_compute_price_score',
        store=True,
        digits=(4, 1),
    )
    score_price = fields.Float(
        string='Price Score',
        compute='_compute_price_score',
        store=True,
        digits=(4, 2),
    )

    total_score = fields.Float(
        string='Total Score',
        compute='_compute_total_score',
        store=True,
        digits=(4, 2),
    )

    @api.depends('scheduled_date', 'date_done')
    def _compute_delivery_score(self):
        for rec in self:
            if rec.scheduled_date and rec.date_done:
                delta = rec.date_done - rec.scheduled_date
                delay = delta.days  # negative means early delivery
                rec.delivery_delay_days = max(delay, 0)

                if delay <= 0:
                    rec.score_delivery = 5.0
                elif delay <= 2:
                    rec.score_delivery = 4.0
                elif delay <= 5:
                    rec.score_delivery = 3.0
                elif delay <= 10:
                    rec.score_delivery = 2.0
                else:
                    rec.score_delivery = 1.0
            else:
                rec.delivery_delay_days = 0
                rec.score_delivery = 0.0

    @api.depends('score_quality')
    def _compute_quality_score_float(self):
        for rec in self:
            rec.score_quality_float = float(rec.score_quality) if rec.score_quality else 0.0

    @api.depends('purchase_order_id', 'purchase_order_id.order_line', 'partner_id')
    def _compute_price_score(self):
        for rec in self:
            if not rec.purchase_order_id:
                rec.po_unit_price = 0.0
                rec.avg_price_market = 0.0
                rec.price_diff_percent = 0.0
                rec.score_price = 3.0  # default average
                continue

            po_lines = rec.purchase_order_id.order_line
            if not po_lines:
                rec.po_unit_price = 0.0
                rec.avg_price_market = 0.0
                rec.price_diff_percent = 0.0
                rec.score_price = 3.0
                continue

            # Compute weighted average price of current PO
            total_qty = sum(l.product_qty for l in po_lines if l.product_qty)
            if total_qty:
                current_price = sum(
                    l.price_unit * l.product_qty for l in po_lines
                ) / total_qty
            else:
                current_price = po_lines[0].price_unit

            rec.po_unit_price = current_price

            # Market price benchmark: Avg price from other confirmed POs 
            # for the same products, from other suppliers
            product_ids = po_lines.mapped('product_id').ids
            if product_ids:
                other_lines = self.env['purchase.order.line'].search([
                    ('product_id', 'in', product_ids),
                    ('order_id', '!=', rec.purchase_order_id.id),
                    ('order_id.state', 'in', ['purchase', 'done']),
                    ('order_id.partner_id', '!=', rec.partner_id.id),
                ])
                if other_lines:
                    avg_market = sum(l.price_unit for l in other_lines) / len(other_lines)
                    rec.avg_price_market = avg_market

                    # Difference percentage: positive means more expensive than market
                    diff_pct = ((current_price - avg_market) / avg_market) * 100
                    rec.price_diff_percent = diff_pct

                    # Scoring logic based on market difference
                    if diff_pct <= -10:
                        rec.score_price = 5.0   # Cheaper than market ≥10% → Excellent
                    elif diff_pct <= -5:
                        rec.score_price = 4.0   # Cheaper by 5-10%
                    elif diff_pct <= 5:
                        rec.score_price = 3.0   # Within ±5% range
                    elif diff_pct <= 15:
                        rec.score_price = 2.0   # More expensive by 5-15%
                    else:
                        rec.score_price = 1.0   # More expensive >15%
                else:
                    # No other suppliers to compare → default to 3.0
                    rec.avg_price_market = 0.0
                    rec.price_diff_percent = 0.0
                    rec.score_price = 3.0
            else:
                rec.avg_price_market = 0.0
                rec.price_diff_percent = 0.0
                rec.score_price = 3.0

    @api.depends('score_delivery', 'score_quality_float', 'score_price')
    def _compute_total_score(self):
        for rec in self:
            scores = []
            if rec.score_delivery:
                scores.append(rec.score_delivery)
            if rec.score_quality_float:
                scores.append(rec.score_quality_float)
            if rec.score_price:
                scores.append(rec.score_price)

            rec.total_score = sum(scores) / len(scores) if scores else 0.0

    @api.constrains('stock_picking_id')
    def _check_unique_picking(self):
        """BR4: 1 Done Receipt = 1 Evaluation Record."""
        for rec in self:
            duplicate = self.search([
                ('stock_picking_id', '=', rec.stock_picking_id.id),
                ('id', '!=', rec.id),
            ])
            if duplicate:
                raise ValidationError(
                    f"The receipt '{rec.stock_picking_id.name}' already has an evaluation. "
                    f"Each receipt can only be evaluated once."
                )

    def unlink(self):
        """BR: Purchase User cannot delete — only Purchase Manager can."""
        if not self.env.user.has_group('purchase.group_purchase_manager'):
            raise ValidationError(
                "You do not have permission to delete supplier evaluation records."
            )
        return super().unlink()