# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models, _


class Partner(models.Model):
    _inherit = 'res.partner'

    edi_partner = fields.Boolean(string= "CA Customer")
    ca_site_id = fields.Integer(string='CA Site ID')
    commission = fields.Float(string='Commission %', default=0.0)
    ca_journal_id = fields.Many2one('account.journal', string="Payment Journal")

    # edi_order  = fields.Boolean(string="Enable 850")
    # edi_ack = fields.Boolean(string="Enable 855 ")
    # edi_inv = fields.Boolean(string="Enable 810")
    # edi_ship = fields.Boolean(string="Enable 856")
    # edi_partner_id = fields.Integer(string= 'EDI PartnerId')
    # trading_partner_code = fields.Char('Trading Partner Id', copy=False)
    # receiver_unique_code = fields.Char('Reciever Unique Id', copy=False)
    # reciever_company_name = fields.Char(string='Reciever Company Name')
    # vendor_number = fields.Char('Vendor')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
