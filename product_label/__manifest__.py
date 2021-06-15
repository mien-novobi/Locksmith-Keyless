# -*- coding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2021   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "Product Label",
    'version': '13.0.1.0',
    'category': "Barcode",
    'description': """
        This module will helps to print customized product label.
    """,
    'author': 'Confianz IT',
    'website': 'https://www.confianzit.com',
    'depends':  ['product', 'channel_advisor'],
    'data': [
        'report/product_label.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
