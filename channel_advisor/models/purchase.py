# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp



class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    vendor_sku = fields.Char(compute="get_vendor_sku", string='Vendor SKU')


    @api.depends('product_id')
    def get_vendor_sku(self):
        for line in self:
            line.vendor_sku = ''
            if line.product_id:
                for seller in line.product_id.seller_ids:
                    if line.order_id.partner_id == seller.name:
                        line.vendor_sku = seller.product_code
                    else:
                        line.vendor_sku = ''








PurchaseOrderLine()
