# -*- coding: utf-8 -*-
{
    'name': 'Granite Scrap Management',
    'version': '19.0.2.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Xử lý phế phẩm và đá thừa liên kết với Đơn bán hàng (SO)',
    'author': 'Nhóm 9',
    'depends': ['sale', 'stock', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/granite_scrap_data.xml',
        'wizard/granite_scrap_wizard_views.xml',
        'views/granite_scrap_order_views.xml',
        'views/granite_leftover_stone_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}