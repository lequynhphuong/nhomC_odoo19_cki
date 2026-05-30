from odoo import models, fields, api
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order' # Khai báo kế thừa module Bán hàng (Sales)

    # 1. Các trường dữ liệu
    nt_deposit_amount = fields.Monetary(string="Deposit Amount", tracking=True)
    nt_is_accepted = fields.Boolean(string="Is Accepted", tracking=True)
    nt_remaining_amount = fields.Monetary(
        string="Remaining Amount",
        compute="_compute_nt_remaining_amount",
        store=True,
        tracking=True
    )
    nt_is_fully_paid = fields.Boolean(string="Is Fully Paid", tracking=True)

    # 2. Logic tự động tính tiền & Tự động tick
    @api.depends('nt_deposit_amount', 'amount_total')
    def _compute_nt_remaining_amount(self):
        for order in self:
            remaining = order.amount_total - order.nt_deposit_amount
            order.nt_remaining_amount = remaining if remaining > 0 else 0
            
            # Nếu tiền cọc >= Tổng tiền -> Tự động tick đã thanh toán đủ
            if order.amount_total > 0 and order.nt_deposit_amount >= order.amount_total:
                order.nt_is_fully_paid = True
            else:
                order.nt_is_fully_paid = False

    # 3. Ngoại lệ 2a: Tiền cọc lớn hơn tổng đơn hàng
    @api.constrains('nt_deposit_amount', 'amount_total')
    def _check_deposit_amount(self):
        for order in self:
            if order.nt_deposit_amount > order.amount_total:
                raise ValidationError("Error: Deposit amount cannot exceed the total order value! Please enter a valid amount.")

    # 4. Ngoại lệ 5a: Tick thanh toán đủ nhưng chưa nghiệm thu
    @api.constrains('nt_is_fully_paid', 'nt_is_accepted')
    def _check_acceptance_before_payment(self):
        for order in self:
            if order.nt_is_fully_paid and not order.nt_is_accepted:
                raise ValidationError("Error: Order cannot be fully paid before acceptance.")