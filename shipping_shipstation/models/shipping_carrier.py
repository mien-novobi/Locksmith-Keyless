# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ShippingCarrier(models.Model):
    _inherit = "shipping.carrier"

    is_shipstation_carrier = fields.Boolean(string="Shipstation Carrier")
    shipstation_carrier_id = fields.Many2one('shipstation.carrier', string='ShipStation Carrier')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
