# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class DeliveryWarning(models.TransientModel):
    _name = "delivery.warning"
    _description = "Delivery Warning"

    def continue_carrier(self):
        # method to create an order line with the corresponding shipping rate
        # order_line = self.env['shipping.quote'].add_carrier_to_order(self._context.get('active_id'))
        return {'type':'ir.actions.client', 'tag':'reload'}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
