# -*- coding: utf-8 -*-

import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from xml.dom import minidom
import xml.etree.ElementTree as ET
import logging



class CustomerProduct(models.Model):
    _name = 'customer.product.values'
    _description = 'Saves the customer Info of the product'

    product_id = fields.Many2one('product.template', string='Product')
    name = fields.Char(string='Name')
    customer_sku = fields.Char(string='SKU')
    partner_id = fields.Many2one('res.partner', string='Partner')
    agreed_price = fields.Float(string='Agreed Price')

    _sql_constraints = [
        ('partner_product_uniq', 'unique (partner_id,product_id)', 'The product must be unique per partner !')
    ]

    @api.model
    def get_vendor_sku(self, partner=False, product=False):
        product_record = self.search([('product_id', '=', product.id), ('partner_id', '=', partner.id)], limit=1)
        return product_record and product_record.customer_sku or ''


class ProductTemplate(models.Model):
    _inherit = "product.template"

    customer_product_value_ids = fields.One2many('customer.product.values', 'product_id', string='Customer Reference')
    product_customer_sku = fields.Char(related='customer_product_value_ids.customer_sku', string='Customer SKU')
    ca_product_id = fields.Char("Channel Advisor Product ID")
    ca_profile_id = fields.Char("Channel Advisor Account ID")
    ca_qty_updated_date = fields.Datetime(string="Qty Last Updated Date")
    ca_brand = fields.Char(string="Brand")
    ca_mpn = fields.Char(string="MPN")
    ca_product_type = fields.Selection([
        ('Item', 'Standard'),
        ('Child', 'Child'),
        ('Parent', 'Parent'),
        ('Bundle', 'Bundle'),
    ], string="Product Type")
    ca_parent_product_id = fields.Char(string="Parent Product ID")
    ca_parent_id = fields.Many2one('product.template', string="Parent", compute="_compute_ca_parent_id")
    ca_bundle_ids = fields.One2many('ca.product.bundle', 'product_tmpl_id', string="Bundles")
    ca_bundle_product_ids = fields.One2many('ca.product.bundle', 'bundle_id', string="Components")
    kit_available = fields.Float(compute="_compute_kit_available", digits="Product Unit of Measure")
    kit_free_qty = fields.Float(compute="_compute_kit_available", string="Free To Use Kits",
                                digits="Product Unit of Measure", compute_sudo=False)
    free_qty = fields.Float(compute="_compute_free_qty", string="Free To Use Quantity",
                            digits="Product Unit of Measure", compute_sudo=False)
    is_kit = fields.Boolean(string="Kit?", default=False)
    ca_condition = fields.Selection([
        ('NEW', 'New'),
        ('USED', 'Used'),
        ('REFURBISHED', 'Refurbished'),
        ('RECONDITIONED', 'Reconditioned'),
        ('LIKE NEW', 'Lke New'),
    ], string="Condition")
    ca_manufacturer = fields.Char(string="Manufacturer")
    flag = fields.Boolean(string="flag?", default=False)

    @api.depends()
    def _compute_free_qty(self):
        variants_available = self.mapped('product_variant_ids')._product_available()
        for template in self:
            free_qty = sum(
                [variants_available[product.id]['free_qty'] or 0 for product in template.product_variant_ids])
            template.free_qty = free_qty

    @api.depends()
    def _compute_kit_available(self):
        for template in self:
            if template.is_kit:
                kit_available_qtys = []
                kit_free_qtys = []
                for item in template.ca_bundle_product_ids:
                    kit_available_qtys += [item.product_id.qty_available // item.quantity]
                    kit_free_qtys += [item.product_id.free_qty // item.quantity]
                template.kit_available = min(kit_available_qtys, default=0)
                template.kit_free_qty = min(kit_free_qtys, default=0)
            else:
                template.kit_available = 0
                template.kit_free_qty = 0

    @api.depends('ca_parent_product_id')
    def _compute_ca_parent_id(self):
        for product in self:
            if product.ca_parent_product_id:
                parent = self.search([('ca_profile_id', '=', product.ca_profile_id),
                                      ('ca_product_id', '=', product.ca_parent_product_id)], limit=1)
                product.ca_parent_id = parent.id
            else:
                product.ca_parent_id = False

    def action_update_components(self):
        Product = self.env['product.product']
        connector = False
        profile_ids = []
        logging.info("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logging.info(self)

        for rec in self.filtered(lambda r: r.ca_product_type == 'Bundle'):
            logging.info(rec)

            if rec.ca_profile_id not in profile_ids or not connector:
                connector = self.env['ca.connector'].sudo().search(
                    [('ca_account_ids.account_id', '=', rec.ca_profile_id)], limit=1)
                profile_ids = connector.ca_account_ids.mapped('account_id')

            if connector:
                res = connector.call('retrieve_bundle_components', bundle_id=rec.ca_product_id)
                components = [(5, 0, 0)]
                for vals in res.get('value', []):
                    product = Product.search([('ca_product_id', '=', vals.get('ComponentID')),
                                              ('ca_profile_id', '=', vals.get('ProfileID'))], limit=1)
                    if product:
                        components.append((0, 0, {
                            'product_id': product.id,
                            'quantity': vals.get('Quantity', 0),
                        }))
                rec.write({'ca_bundle_product_ids': components})
        return True

    def update_components_cron(self):
        while self.env['product.product'].search_count(
                [('flag', '=', False), ('ca_product_type', '=', 'Bundle')]) > 0:
            Product = self.env['product.product']
            connector = False
            profile_ids = []
            pdt = self.env['product.product'].search(
                [('flag', '=', False), ('ca_product_type', '=', 'Bundle')], limit=200)
            for rec in pdt:
                if rec.ca_profile_id not in profile_ids or not connector:
                    connector = self.env['ca.connector'].sudo().search(
                        [('ca_account_ids.account_id', '=', rec.ca_profile_id)], limit=1)
                    profile_ids = connector.ca_account_ids.mapped('account_id')

                if connector:
                    logging.info("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                    logging.info(rec.ca_product_id)
                    res = connector.call('retrieve_bundle_components', bundle_id=rec.ca_product_id)
                    components = [(5, 0, 0)]
                    for vals in res.get('value', []):
                        product = Product.search([('ca_product_id', '=', vals.get('ComponentID')),
                                                  ('ca_profile_id', '=', vals.get('ProfileID'))], limit=1)
                        if product:
                            components.append((0, 0, {
                                'product_id': product.id,
                                'quantity': vals.get('Quantity', 0),
                            }))
                            logging.info("componentscomponentscomponentscomponents")
                            logging.info(components)

                    rec.write({'ca_bundle_product_ids': components})
                    rec.write({'flag': True})
                    logging.info(rec.ca_bundle_product_ids)

            self._cr.commit()
        Products = self.env['product.product'].search(
            [('ca_product_type', '=', 'Bundle'), ('flag', '=', True)])
        logging.info("Products")
        logging.info(Products)
        for prod in Products:
            prod.write({'flag': False})
        return True

    def ca_update_quantity(self):
        self.mapped('product_variant_id').ca_update_quantity()

    def update_bundle_price(self):
        for product in self:
            if product.is_kit:
                # component_price = sum([item.product_id.lst_price * item.quantity for item in product.ca_bundle_product_ids])
                component_cost = sum(
                    [item.product_id.standard_price * item.quantity for item in product.ca_bundle_product_ids])
                product.write({
                    # 'list_price': component_price,
                    'standard_price': component_cost,
                })

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)

        if 'list_price' in vals or 'ca_bundle_ids' in vals:
            for product in self:
                if not product.is_kit:
                    product.ca_bundle_ids.mapped('bundle_id').update_bundle_price()

        if 'ca_bundle_product_ids' in vals:
            for product in self:
                if product.is_kit:
                    product.update_bundle_price()

        if 'list_price' in vals and not self._context.get('ca_import', False):
            apps = self.env['ca.connector'].sudo().search([('state', '=', 'active'), ('auto_update_price', '=', True)])
            for app in apps:
                for product in self.filtered(lambda r: r.ca_profile_id in app.ca_account_ids.mapped('account_id')):
                    vals = {'RetailPrice': product.list_price}
                    app.call('update_price', product_id=product.ca_product_id, vals=vals)

        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_product_multiline_description_sale(self):
        # name = super(ProductProduct, self).get_product_multiline_description_sale()
        name = self.display_name
        return name

    def action_update_components(self):
        self.ensure_one()
        return self.product_tmpl_id.action_update_components()

    def inventory_update(self):

        xml_string = self.get_pdt_xml()
        date_today = datetime.datetime.strptime(str(fields.Datetime.now()), '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        # save_path_file = "Inventory_%s.xml" % date_today
        save_path_file = "/home/locksmith_keyless_13/odoo13/inventory_updates/" + "Inventory_%s.xml" % date_today
        with open(save_path_file, "w") as f:
            f.write(xml_string)
        return True

    def get_pdt_xml(self):

        xmlns_uris = {'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
                      'web': 'http://api.channeladvisor.com/webservices/'}
        try:
            products = self.search([('type', '=', 'product')])
            root_node = ET.Element("soapenv:Envelope")
            soap_header = SubElement(root_node, 'soapenv:Header')
            api_cred = SubElement(soap_header, 'web:APICredentials')
            SubElement(api_cred, 'web:DeveloperKey').text = 'test'
            SubElement(api_cred, 'web:Password').text = 'test'
            soap_body = SubElement(root_node, 'soapenv:Body')
            item_qty_price = SubElement(soap_body, 'web:UpdateInventoryItemQuantityAndPriceList')
            for product in products:
                qty = product.qty_available - product.outgoing_qty
                update_item_qty_price = SubElement(item_qty_price, 'web:InventoryItemQuantityAndPrice')
                SubElement(update_item_qty_price, 'web:Sku').text = str(product.default_code)
                SubElement(update_item_qty_price, 'web:Quantity').text = str(qty)
                # SubElement(update_item_qty_price, 'web:DistributionCenterCode').text = product.location_id.name
                SubElement(update_item_qty_price, 'web:UpdateType').text = 'UNSHIPPED'
                price_info = SubElement(item_qty_price, 'web:PriceInfo')
                SubElement(price_info, 'web:Cost').text = str(product.standard_price)
                SubElement(price_info, 'web:RetailPrice').text = str(product.lst_price)
                SubElement(price_info, 'web:StorePrice').text = str(product.lst_price)

            self.add_XMLNS_attributes(root_node, xmlns_uris)
            rough_string = ET.tostring(root_node, encoding='UTF-8', method='xml')
            reparsed = minidom.parseString(rough_string)
            return reparsed.toprettyxml(indent="  ")
        except Exception as e:
            raise UserError("Exception in Inventory processing\n %s " % e)

    def add_XMLNS_attributes(self, tree, xmlns_uris_dict):
        if not ET.iselement(tree):
            tree = tree.getroot()
        for prefix, uri in xmlns_uris_dict.items():
            tree.attrib['xmlns:' + prefix] = uri

    def ca_update_quantity(self):
        dist_centers = self.env['ca.distribution.center'].search(
            [('type', '=', 'Warehouse'), ('warehouse_id', '!=', False)])
        if not dist_centers:
            return

        Connector = self.env['ca.connector'].sudo()
        for product in self.filtered(lambda r: r.ca_product_type in ['Item', 'Child']):
            connector = Connector.search([
                ('state', '=', 'active'),
                ('ca_account_ids.account_id', '=', product.ca_profile_id)
            ], limit=1)

            vals = {'Value': {'UpdateType': 'Absolute', 'Updates': []}}
            for dist_center in dist_centers:
                if product.is_kit:
                    qty_available = product.with_context(warehouse=dist_center.warehouse_id.id).kit_free_qty
                else:
                    qty_available = product.with_context(warehouse=dist_center.warehouse_id.id).free_qty

                vals['Value']['Updates'].append({
                    'DistributionCenterID': int(dist_center.res_id),
                    'Quantity': int(qty_available),
                })
            connector.call('update_quantity', product_id=product.ca_product_id, vals=vals)

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)

        if 'standard_price' in vals:
            for product in self:
                if not product.is_kit:
                    product.ca_bundle_ids.mapped('bundle_id').update_bundle_price()

            if not self._context.get('ca_import', False):
                apps = self.env['ca.connector'].sudo().search(
                    [('state', '=', 'active'), ('auto_update_cost', '=', True)])
                for app in apps:
                    for product in self.filtered(lambda r: r.ca_profile_id in app.ca_account_ids.mapped('account_id')):
                        vals = {'Cost': product.standard_price}
                        app.call('update_price', product_id=product.ca_product_id, vals=vals)
        return res


class ProductBundle(models.Model):
    _name = "ca.product.bundle"
    _description = "Channel Advisor Product Bundle"
    _rec_name = "bundle_id"

    product_id = fields.Many2one('product.product', string="Component", ondelete="cascade")
    product_tmpl_id = fields.Many2one(related="product_id.product_tmpl_id", store=True)
    product_type = fields.Selection(related="product_id.ca_product_type", string="Product type", readonly=True,
                                    store=False)
    quantity = fields.Float(string="Quantity", default=1)
    bundle_id = fields.Many2one('product.template', string="Bundle", ondelete="cascade")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
