# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    @api.model
    def run(self, procurements):
        new_procurements = []
        for procurement in procurements:
            product = procurement.product_id
            if product and product.ca_bundle_product_ids:
                for component in product.ca_bundle_product_ids:
                    product_qty = component.quantity * procurement.product_qty
                    new_procurements.append(self.Procurement(
                        component.product_id,
                        product_qty,
                        component.product_id.uom_id,
                        procurement.location_id,
                        procurement.name,
                        procurement.origin,
                        procurement.company_id,
                        procurement.values,
                    ))
            else:
                new_procurements.append(procurement)

        return super(ProcurementGroup, self).run(new_procurements)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
