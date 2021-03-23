# -*- coding: utf-8 -*-

{
    'name': 'Channel Advisor FTP Configuration',
    'version': '13.0.1.0',
    'sequence': 15,
    'description': "This module will helps to update commissions from ChannelAdvisor",
    'author': 'Confianz Global',
    'website': 'https://confianzit.com',
    'depends': ['channel_advisor'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/ftp_config_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
