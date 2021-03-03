# -*- coding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2020   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "ShipStation Integration",
    'version': '13.0.1.0',
    'category': "Stock Management",
    'description': "Odoo Integration with Shipstation",
    'author': 'Confianz IT',
    'website': 'https://www.confianzit.com',
    'depends':  ['shipping_core', 'channel_advisor'],
    'data': [
        'security/ir.model.access.csv',

        'data/data.xml',

        'wizard/import_export_operation_view.xml',
        'wizard/carrier_add_funds_view.xml',

        'views/menu.xml',
        'views/shipstation_accounts_view.xml',
        'views/shipstation_marketplaces_view.xml',
        'views/shipstation_stores_view.xml',
        'views/shipstation_warehouse_view.xml',
        'views/shipstation_service_view.xml',
        'views/shipstation_carrier_view.xml',
        'views/sale_order_view.xml',
        'views/delivery_carrier_view.xml',
        'views/shipping_carrier_view.xml',
        'views/stock_picking_view.xml',
        'views/shipstation_connector_view.xml',
        'views/shipstation_product_view.xml',
        'views/res_partner_view.xml',
        'views/shipstation_log_view.xml'
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
