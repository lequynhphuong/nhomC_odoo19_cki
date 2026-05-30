{
    'name': 'Granite Supplier Evaluation',
    'version': '1.0',
    'summary': 'Tự động đánh giá nhà cung cấp đá sau mỗi lần nhận hàng',
    'author': 'Quynh Phuong',
    'category': 'Supply Chain',
    'license': 'LGPL-3',
    'depends': ['purchase', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'data/granite_supplier_tag_data.xml',
        'wizard/supplier_evaluation_wizard_views.xml',
        'views/granite_supplier_evaluation_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'application': True,
}