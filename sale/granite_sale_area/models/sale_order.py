from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends(
        "order_line",
        "order_line.length",
        "order_line.width",
        "order_line.product_uom_qty",
        "order_line.discount",
        "order_line.price_unit",
        "order_line.tax_ids",
        "order_line.price_subtotal",
        "order_line.price_tax",
        "order_line.price_total",
        "currency_id",
        "company_id",
        "payment_term_id",
    )
    def _compute_amounts(self):
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)

            order.amount_untaxed = sum(order_lines.mapped("price_subtotal"))
            order.amount_tax = sum(order_lines.mapped("price_tax"))
            order.amount_total = sum(order_lines.mapped("price_total"))
