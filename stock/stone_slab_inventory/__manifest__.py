{
    'name': 'Stone Slab Inventory',
    'version': '19.0.1.0.0',
    'summary': 'Quản lý tồn kho đá tự nhiên theo Lot và Slab Lines',
    'author': 'Duong Ngoc Linh',
    'category': 'Inventory',
    'depends': ['stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/stone_slab_line_views.xml',
        'views/stock_lot_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
