# -*- coding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2021   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "POS Extension",
    'version': '13.0.1.0',
    'category': "POS",
    'description': """
        This module will add following features:
            - Auto Invoicing.
            - SMS Notification.
    """,
    'author': 'Confianz IT',
    'website': 'https://www.confianzit.com',
    'depends':  ['point_of_sale'],
    'data': [
        'security/sms_security.xml',

        'data/sms_data.xml',

        'views/assets.xml',
        'views/pos_config_view.xml',
        'views/product_views.xml',
    ],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
