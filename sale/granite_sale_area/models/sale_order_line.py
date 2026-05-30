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

    @api.constrains("length", "width")
    def _check_dimension_values(self):
        for line in self:
            if line.length < 0:
                raise ValidationError("Length cannot be less than 0.")
            if line.width < 0:
                raise ValidationError("Width cannot be less than 0.")