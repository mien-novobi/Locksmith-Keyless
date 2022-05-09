# -*- coding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2022   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "Purchase Report",
    'version': '13.0.1.0',
    'category': "Reports",
    'description': """
        This module will helps to print customised purchase report.
    """,
    'author': 'Confianz IT',
    'website': 'https://www.confianzit.com',
    'depends':  ['purchase', 'channel_advisor'],
    'data': [
        'wizard/purchasing_report_view.xml',
        'views/purchase_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
