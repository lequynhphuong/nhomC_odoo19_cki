from odoo import api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    length = fields.Float(string="Length (m)", digits=(16, 2))
    width = fields.Float(string="Width (m)", digits=(16, 2))
    area_m2 = fields.Float(
        string="Area (m²)",
        compute="_compute_area_m2",
        store=True,
        readonly=True,
        digits=(16, 4),
    )

    @api.depends("length", "width")
    def _compute_area_m2(self):
        for line in self:
            if line.length > 0 and line.width > 0:
                line.area_m2 = round(line.length * line.width, 4)
            else:
                line.area_m2 = 0.0

    @api.depends("length", "width", "area_m2", "product_qty", "price_unit", "tax_ids")
    def _compute_amount(self):
        for line in self:
            company = line.company_id or self.env.company
            quantity_for_amount = (line.area_m2 or 0.0) * (line.product_qty or 0.0)

            base_line = self.env['account.tax']._prepare_base_line_for_taxes_computation(
                line,
                tax_ids=line.tax_ids,
                quantity=quantity_for_amount,
                partner_id=line.order_id.partner_id,
                currency_id=line.order_id.currency_id or company.currency_id,
                rate=line.order_id.currency_rate,
                name=line.name,
            )
            self.env['account.tax']._add_tax_details_in_base_line(base_line, company)
            self.env['account.tax']._round_base_lines_tax_details([base_line], company)

            line.price_subtotal = base_line['tax_details']['total_excluded_currency']
            line.price_total = base_line['tax_details']['total_included_currency']
            line.price_tax = line.price_total - line.price_subtotal

    @api.constrains("length", "width")
    def _check_dimension_values(self):
        for line in self:
            if line.length < 0:
                raise ValidationError("Length cannot be less than 0.")
            if line.width < 0:
                raise ValidationError("Width cannot be less than 0.")