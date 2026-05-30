# Stone Slab Inventory

Module quản lý tồn kho đá tự nhiên theo Lô hàng (Lot) và chi tiết tấm đá (Slab Lines) cho Odoo 19 Community.

## Chức năng chính

- Đánh dấu sản phẩm là **đá tự nhiên** (is_slab_product).
- Mỗi Lô hàng chứa nhiều **tấm đá** với kích thước khác nhau.
- Diện tích m² tự động tính: `length_cm × width_cm × slab_count / 10000`.
- Phân loại chất lượng từng tấm: **Đạt / Chờ Xử Lý / Lỗi**.
- Chỉ tấm **Đạt** mới được đồng bộ vào tồn kho.
- Nút **Sync Slab Quantity** trên phiếu nhập kho.
- Chặn xác nhận phiếu nhập nếu còn tấm **Chờ Xử Lý**.

## Cài đặt

1. Copy thư mục `stone_slab_inventory` vào `custom-addons/`.
2. Cập nhật danh sách module: **Settings > Update App List**.
3. Tìm và cài đặt **Stone Slab Inventory**.

## Quy trình sử dụng

1. **Cấu hình sản phẩm**: Mở sản phẩm đá → tab *Cấu Hình Đá* → bật *Là Sản Phẩm Đá* → tracking tự chuyển sang Lot.
2. **Tạo phiếu nhập kho** (Receipts): chọn sản phẩm đá.
3. **Nhập chi tiết tấm đá**: tab *Chi Tiết Tấm Đá* → thêm slab lines với kích thước và chất lượng.
4. **Sync**: bấm **Sync Slab Quantity** → m² của tấm Đạt được đẩy vào move lines.
5. **Validate**: xác nhận phiếu nhập → tồn kho tăng đúng số m² đạt chất lượng.

## Công thức

```
area_m2 = length_cm × width_cm × slab_count / 10000
```

## Phụ thuộc

- `stock`
- `product`
