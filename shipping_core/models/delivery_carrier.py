# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    shipping_carrier_id = fields.Many2one('shipping.carrier', 'Shipping Carrier')
    service_code = fields.Char("Service Code")
    freight = fields.Boolean('Freight')
    weight = fields.Integer("Max/Min Weight")
    height = fields.Integer("Max/Min Height")
    width = fields.Integer("Max/min Width")
    depth = fields.Integer("Max/Min Depth")
    delivery_area = fields.Selection([
        ('domestic', 'Domestic'),
        ('international', 'International'),
        ('both', "Both")
    ], "Delivery Area", default="domestic", required=True)
    shipping_type = fields.Selection([
        ('residential', 'Residential'),
        ('freight', 'Standard Freight'),
        ('shipcollect', 'Third Party Shipping')
    ], string='Shipping Type')
    model_name = fields.Char(related='shipping_carrier_id.model_name', string="Model name")

    def validate_address(self, partner=False):
        self.ensure_one()
        if not partner:
            raise UserError(_('Invalid Partner address for validation'))
        if self.company_id.country_id.code == partner.country_id.code:  # to avoid International address validation
            if hasattr(self, '%s_validate_address' % self.delivery_type):
                return getattr(self, '%s_validate_address' % self.delivery_type)(partner=partner)
        return True

    def validate_residential_address(self, partner=False):
        self.ensure_one()
        if not partner:
            raise UserError(_('Invalid Partner address for validation'))
        if self.company_id.country_id.code == partner.country_id.code:  # to avoid International address validation
            if hasattr(self, '%s_validate_residential_address' % self.delivery_type):
                return getattr(self, '%s_validate_residential_address' % self.delivery_type)(partner=partner)
        return False


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
