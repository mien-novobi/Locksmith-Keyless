# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class ShippingQuote(models.Model):
    _inherit = "shipping.quote"

    def add_carrier_to_order(self, quote_id=False):
        res = super(ShippingQuote, self).add_carrier_to_order(quote_id)

        if not self:
            self = self.browse(quote_id)
        self.ensure_one()

        sale_order = self.sale_id
        if sale_order:
            package_id = sale_order.shipstation_package_id.id or False
            sale_order.onchange_shipping_carrier_id_ss()
            sale_order.onchange_carrier_id_ss()

            service_name = (self.name or '').split('-')
            if not package_id and len(service_name) > 1:
                packages = {package.name: package.id for package in self.sale_id.shipstation_carrier_id.package_ids}
                package_id = packages.get(service_name[1].strip(), False)
            sale_order.shipstation_package_id = package_id

        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
