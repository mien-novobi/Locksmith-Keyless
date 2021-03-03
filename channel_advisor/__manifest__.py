# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Channel Advisor Integration',
    'version': '1.0',
    'category': 'Sales',
    'author'  : "Confianz Global",
    'sequence': 1500,
    'summary': 'The module that manages the Channel Advisor ',
    'description': """
The module that manages the order generated via Channel Advisor
    """,
    'website': 'https://www.confianzit.com',
    'depends': ['sale','purchase','account','sale_margin'],
    'data': [
        'security/ir.model.access.csv',

        'data/order_import_cron.xml',
        'data/inventory_update_cron.xml',

        'views/menu.xml',
        'views/edi_config_view.xml',
        'views/sale_order_view.xml',
        'views/partner_view.xml',
        'views/edi_log_view.xml',
        'views/product_view.xml',
        'views/connector_views.xml',
        'views/ca_account_views.xml',
        'views/res_company_view.xml',
        'views/purchase_view.xml',
        'views/distribution_center_views.xml',
        'report/report_saleorder.xml',
        'report/purchase_order_templates.xml',
'report/report_invoice.xml',
    ],
    'demo': [

    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
