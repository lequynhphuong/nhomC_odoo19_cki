{
    'name': 'Phiếu Sản Xuất Đơn Giản',
    'version': '19.0.1.0.0',
    'summary': 'Tạo phiếu sản xuất nội bộ từ Sale Order, không cần MRP',
    'author': 'Duong Ngoc Linh',
    'category': 'Sales',
    'depends': ['sale', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'views/simple_production_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
