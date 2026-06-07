from odoo import api, models
from odoo.tools import formatLang


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.depends("order_line.price_subtotal", "company_id", "currency_id")
    def _amount_all(self):
        AccountTax = self.env["account.tax"]
        for order in self:
            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            base_lines = []

            for line in order_lines:
                company = order.company_id or self.env.company
                area_m2 = line.area_m2 or getattr(line, "area", 0.0)
                quantity_for_amount = (area_m2 or 0.0) * (line.product_qty or 0.0)
                if quantity_for_amount <= 0:
                    quantity_for_amount = line.product_qty or 0.0

                base_line = AccountTax._prepare_base_line_for_taxes_computation(
                    line,
                    tax_ids=line.tax_ids,
                    quantity=quantity_for_amount,
                    partner_id=line.order_id.partner_id,
                    currency_id=line.order_id.currency_id or company.currency_id,
                    rate=line.order_id.currency_rate,
                    name=line.name,
                )
                AccountTax._add_tax_details_in_base_line(base_line, company)
                base_lines.append(base_line)

            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )

            order.amount_untaxed = tax_totals["base_amount_currency"]
            order.amount_tax = tax_totals["tax_amount_currency"]
            order.amount_total = tax_totals["total_amount_currency"]
            order.amount_total_cc = tax_totals["total_amount"]

    @api.depends("order_line.price_subtotal", "currency_id", "company_id")
    def _compute_tax_totals(self):
        AccountTax = self.env["account.tax"]
        for order in self:
            if not order.company_id:
                order.tax_totals = False
                continue

            order_lines = order.order_line.filtered(lambda x: not x.display_type)
            base_lines = []

            for line in order_lines:
                company = order.company_id or self.env.company
                area_m2 = line.area_m2 or getattr(line, "area", 0.0)
                quantity_for_amount = (area_m2 or 0.0) * (line.product_qty or 0.0)
                if quantity_for_amount <= 0:
                    quantity_for_amount = line.product_qty or 0.0

                base_line = AccountTax._prepare_base_line_for_taxes_computation(
                    line,
                    tax_ids=line.tax_ids,
                    quantity=quantity_for_amount,
                    partner_id=line.order_id.partner_id,
                    currency_id=line.order_id.currency_id or company.currency_id,
                    rate=line.order_id.currency_rate,
                    name=line.name,
                )
                AccountTax._add_tax_details_in_base_line(base_line, company)
                base_lines.append(base_line)

            AccountTax._round_base_lines_tax_details(base_lines, order.company_id)
            order.tax_totals = AccountTax._get_tax_totals_summary(
                base_lines=base_lines,
                currency=order.currency_id or order.company_id.currency_id,
                company=order.company_id,
            )
            if order.currency_id != order.company_currency_id:
                order.tax_totals['amount_total_cc'] = f"({formatLang(self.env, order.amount_total_cc, currency_obj=order.company_currency_id)})"
