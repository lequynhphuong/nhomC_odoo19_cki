{
    'name': 'Granite Stock Area',
    'version': '19.0.1.0.0',
    'summary': 'Granite stock area and lot dimension tracking',
    'author': 'Quynh Phuong',
    'category': 'Inventory',
    'license': 'LGPL-3',
    'depends': ['purchase', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_lot_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'application': False,
}
