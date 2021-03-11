# -*- coding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2020   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "Shipping Service Integration",
    'version': '13.0.1.0',
    'category': "Stock Management",
    'description': "Odoo Integration with UPS and Fedex",
    'author': 'Confianz IT',
    'website': 'https://www.confianzit.com',
    'depends':  ['sale', 'stock', 'delivery'],
    'data': [
        'security/shipping_security.xml',
        'security/ir.model.access.csv',

        # 'data/data.xml',

        'wizard/import_label_view.xml',
        # 'wizard/transfer_wizard_view.xml',
        'wizard/reshipment_view.xml',
        'wizard/delivery_warning_view.xml',

        'views/company_view.xml',
        'views/shipping_carrier_view.xml',
        'views/delivery_carrier_view.xml',
        'views/stock_view.xml',
        'views/partner_view.xml',
        'views/product_view.xml',
        'views/sale_view.xml',
        'views/shipping_quote_view.xml',
        'views/shipping_menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
