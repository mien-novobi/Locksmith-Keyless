# -*- coding: utf-8 -*-
##############################################################################
#
#    Confianz IT
#    Copyright (C) 2021   (https://www.confianzit.com)
#
##############################################################################


{
    'name': "Default Analytic Account",
    'version': '13.0.1.0',
    'category': "Accounting",
    'description': "Default Analytic Account",
    'author': 'Confianz IT',
    'website': 'https://www.confianzit.com',
    'depends':  ['sale', 'account', 'point_of_sale'],
    'data': [
        'views/res_config_settings.xml',
        'views/partner_view.xml',
        'views/pos_config_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
