# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ShippingQuote(models.Model):
    _name = "shipping.quote"
    _description = "Shipping Quotes"

    name = fields.Char(string="Service Name")
    shipping_carrier_id = fields.Many2one('shipping.carrier', 'Shipping Carrier', required=1)
    carrier_id = fields.Many2one('delivery.carrier', 'Service Type', required=1)
    rate = fields.Float('Cost')
    markup_rate = fields.Float('Shipping Rate')
    weight = fields.Float('weight')
    sale_id = fields.Many2one('sale.order', 'Sale Order')
    picking_id = fields.Many2one('stock.picking', 'Stock Picking')
    state = fields.Selection([('cancel', 'Cancel'), ('new', 'New'), ('used', "Used")], "Status", default='new')
    order_state = fields.Selection('Order Status', related='sale_id.state')

    def add_carrier_to_order(self, quote_id=False):
        # method to create an order line with the corresponding shipping rate
        if not self:
            self = self.browse(quote_id)
        self.ensure_one()
        # for row in self.env['shipping.quote'].browse(quote_id):
        if self.sale_id:
            vals = {
                'order_id': self.sale_id.id,
                'product_id': self.carrier_id.product_id.id,
                'name': self.carrier_id.name,
                'product_uom': self.carrier_id.product_id.product_tmpl_id.uom_id.id,
                'price_unit': self.markup_rate,
                'purchase_price': self.rate,
                'product_uom_qty': 1,
                'is_delivery': True,
                'is_shipping': True,
            }
            # Avoid mapping of wrong invoice_ids before Confirm Sale (set condition based on order_id)
            line = self.env['sale.order.line'].search([
                '|', ('is_delivery', '=', True),
                ('is_shipping', '=', True),
                ('order_id', '=', self.sale_id.id)
            ], limit=1)
            self.sale_id.write({
                'shipping_carrier_id': self.shipping_carrier_id.id,
                'carrier_id': self.carrier_id.id,
            })
            if line:
                line.write(vals)
            else:
                line.create(vals)
            self.sale_id.shipping_quote_lines.filtered(lambda rec: rec.state == 'used').write({'state': 'new'})
            self.write({'state': 'used'})
        return True

    def add_to_order(self):
        self.ensure_one()
        result = self.carrier_id and self.carrier_id.validate_residential_address(\
                    partner=self.sale_id and self.sale_id.partner_shipping_id) or False
        partner_address = self.sale_id.partner_shipping_id._get_address()
        company_address = self.sale_id.company_id.partner_id._get_address()
        if company_address.get('country_code', '') == partner_address.get('country_code', ''):
            if self.sale_id and self.carrier_id and self.carrier_id.shipping_type == 'residential':
                if not result:
                    raise UserError('Residential Address Validation Failed !')

        self.add_carrier_to_order()
        return {'type': 'ir.actions.client', 'tag': 'reload'}


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
