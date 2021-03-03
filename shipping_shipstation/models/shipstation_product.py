# -*- coding: utf-8 -*-

import json
from datetime import datetime, timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError


class ShipstationProduct(models.Model):
    _name = "shipstation.product"
    _description = "Shipstation Product"

    name = fields.Char(string="Name", required=True)
    sku = fields.Char(string="SKU", required=True)
    product_id = fields.Many2one('product.product', string="Product", ondelete="restrict")
    shipstation_id = fields.Integer(string="Shipstation Product")
    account_id = fields.Many2one("shipstation.accounts", "Accounts", required=True, ondelete="restrict", help="Account in which carrier is configured")
    company_id = fields.Many2one('res.company', string="Company")
    height = fields.Float(string="Height")
    width = fields.Float(string="Width")
    length = fields.Float(string="Length")
    weight = fields.Float(string="Weight")

    def import_products(self, account=False):
        products = []
        if not account:
            raise UserError("Shipstation Account not defined to import orders")
        response = account._send_request('products?pageSize=500', {})
        if isinstance(response.get('products'), dict):
            products = [response.get('products')]
        products += response.get('products')
        total_pages = response.get('pages')
        page = 2
        while total_pages:
            response = account._send_request('products?pageSize=500&page=%s' % page, {}, method='GET')
            product_data = response.get('products')
            if isinstance(product_data, dict):
                products += [product_data]
            products += product_data
            total_pages -= 1
            page += 1
        if products:
            self.create_ss_product(products, account)
        return products

    @api.model
    def convert_product_weight(self, weight, op='oz_to_lb'):
        qty = 0
        uom_oz = self.env.ref('product.product_uom_oz', raise_if_not_found=False)
        uom_lb = self.env.ref('product.product_uom_lb', raise_if_not_found=False)
        if uom_oz and uom_lb:
            if op == 'oz_to_lb':
                qty = uom_oz._compute_quantity(weight, uom_lb)
            else:
                qty = uom_lb._compute_quantity(weight, uom_oz)
        return qty

    def create_ss_product(self, products, account):
        product_obj = self.env['product.product']
        for product in products:
            ss_product_id = product.get('productId', False)
            sku = product.get('sku', False)
            name = product.get('name', False)
            height = product.get('height', False)
            width = product.get('width', False)
            length = product.get('length', False)
            weight = product.get('weightOz', False)
            if weight:
                weight = self.convert_product_weight(weight, op='oz_to_lb')
            if not ss_product_id or not sku:
                continue
            ss_product = self.search([('shipstation_id', '=', ss_product_id), ('sku', '=', sku)])
            if ss_product:
                continue
            odoo_product = product_obj.search([('default_code', '=', sku)], limit=1)
            if odoo_product:
                self.create({
                    'name': name,
                    'product_id': odoo_product.id,
                    'shipstation_id': ss_product_id,
                    'sku': sku,
                    'height': height,
                    'width': width,
                    'length': length,
                    'weight': weight or odoo_product.weight or False,
                    'account_id': account.id,
                })
                if weight:
                    odoo_product.update({'weight': weight})
            elif account.automatic_product_creation:
                product = product_obj.create({
                    'name': name,
                    'type': 'product',
                    'weight': weight or False,
                    'default_code': sku,
                })
                self.create({
                    'name': name,
                    'product_id': product.id,
                    'shipstation_id': ss_product_id,
                    'sku': sku,
                    'height': height,
                    'width': width,
                    'length': length,
                    'weight': weight or product.weight or False,
                    'account_id': account.id,
                })
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
