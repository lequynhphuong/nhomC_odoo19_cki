from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    length = fields.Float(string="Length", digits=(16, 2))
    width = fields.Float(string="Width", digits=(16, 2))

    area = fields.Float(
        string="Area m²",
        compute="_compute_area",
        store=True,
        readonly=True,
        digits=(16, 2),
    )

    @api.depends("length", "width")
    def _compute_area(self):
        for line in self:
            if line.length > 0 and line.width > 0:
                line.area = round(line.length * line.width, 2)
            else:
                line.area = 0.0

    def _prepare_base_line_for_taxes_computation(self, **kwargs):
        self.ensure_one()
        base_line = super()._prepare_base_line_for_taxes_computation(**kwargs)

        if self.area > 0:
            base_line["price_unit"] = self.price_unit * self.area

        return base_line

    @api.depends(
        "product_uom_qty",
        "discount",
        "price_unit",
        "tax_ids",
        "area",
    )
    def _compute_amount(self):
        super()._compute_amount()

        for line in self:
            if line.area > 0:
                effective_price_unit = line.price_unit * line.area

                taxes = line.tax_ids.compute_all(
                    effective_price_unit,
                    line.currency_id,
                    line.product_uom_qty,
                    product=line.product_id,
                    partner=line.order_id.partner_shipping_id,
                )

                line.price_subtotal = taxes["total_excluded"]
                line.price_tax = sum(
                    tax.get("amount", 0.0)
                    for tax in taxes.get("taxes", [])
                )
                line.price_total = taxes["total_included"]

    @api.constrains("length", "width")
    def _check_dimension_values(self):
        for line in self:
            if line.length < 0:
                raise ValidationError("Length cannot be less than 0.")
            if line.width < 0:
                raise ValidationError("Width cannot be less than 0.")


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.depends(
        "order_line.price_subtotal",
        "order_line.price_tax",
        "order_line.price_total",
    )
    def _compute_amounts(self):
        for order in self:
            lines = order.order_line.filtered(lambda line: not line.display_type)

            amount_untaxed = sum(lines.mapped("price_subtotal"))
            amount_tax = sum(lines.mapped("price_tax"))

            order.amount_untaxed = amount_untaxed
            order.amount_tax = amount_tax
            order.amount_total = amount_untaxed + amount_tax