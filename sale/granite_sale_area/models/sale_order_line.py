from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    length = fields.Float(
        string="Length",
        digits=(16, 2),
    )

    width = fields.Float(
        string="Width",
        digits=(16, 2),
    )

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
            area_m2 = line.area or getattr(line, "area_m2", 0.0)
            quantity_for_amount = (area_m2 or 0.0) * (line.product_uom_qty or 0.0)
            if quantity_for_amount <= 0:
                quantity_for_amount = line.product_uom_qty or 0.0

            price = (
                quantity_for_amount
                * line.price_unit
                * (1 - (line.discount or 0.0) / 100.0)
            )

            taxes = line.tax_ids.compute_all(
                price,
                line.currency_id,
                1.0,
                product=line.product_id,
                partner=line.order_id.partner_shipping_id,
            )

            line.update({
                "price_tax": sum(
                    tax.get("amount", 0.0)
                    for tax in taxes.get("taxes", [])
                ),
                "price_total": taxes["total_included"],
                "price_subtotal": taxes["total_excluded"],
            })

    @api.constrains("length", "width")
    def _check_dimension_values(self):
        for line in self:
            if line.length < 0:
                raise ValidationError("Length cannot be less than 0.")
            if line.width < 0:
                raise ValidationError("Width cannot be less than 0.")