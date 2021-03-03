# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ShippingQuote(models.Model):
    _inherit = "shipping.quote"

    def add_carrier_to_order(self, quote_id=False):
        res = super(ShippingQuote, self).add_carrier_to_order(quote_id)

        if not self:
            self = self.browse(quote_id)
        self.ensure_one()

        if self.sale_id:
            self.sale_id.onchange_shipping_carrier_id_ss()
            self.sale_id.onchange_carrier_id_ss()

        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
