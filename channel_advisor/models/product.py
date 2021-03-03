# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp
from odoo.exceptions import ValidationError
from odoo.tools import float_is_zero
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from xml.dom import minidom
import xml.etree.ElementTree as ET
import datetime


class CustomerProduct(models.Model):
    _name ='customer.product.values'
    _description = 'Saves the customer Info of the product'

    product_id = fields.Many2one('product.template', string= 'Product')
    name       = fields.Char(string= 'Name')
    customer_sku = fields.Char(string= 'SKU')
    partner_id  = fields.Many2one('res.partner', string= 'Partner')
    agreed_price = fields.Float(string='Agreed Price')

    _sql_constraints = [
        ('partner_product_uniq', 'unique (partner_id,product_id)', 'The product must be unique per partner !')
    ]


    @api.model
    def get_vendor_sku(self, partner=False, product=False):
        product_record= self.search([('product_id', '=', product.id), ('partner_id', '=', partner.id)], limit=1)
        return product_record and product_record.customer_sku or ''


class ProductTemplate(models.Model):
    _inherit = "product.template"

    customer_product_value_ids = fields.One2many('customer.product.values', 'product_id', string= 'Customer Reference')
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

    @api.depends('ca_parent_product_id')
    def _compute_ca_parent_id(self):
        for product in self:
            if product.ca_parent_product_id:
                parent = self.search([('ca_profile_id', '=', product.ca_profile_id), ('ca_product_id', '=', product.ca_parent_product_id)], limit=1)
                product.ca_parent_id = parent.id
            else:
                product.ca_parent_id = False

    def action_update_components(self):
        self.ensure_one()
        Product = self.env['product.product']
        connector = self.env['ca.connector'].sudo().search([('ca_account_ids.account_id', '=', self.ca_profile_id)], limit=1)
        if connector:
            res = connector.call('retrieve_bundle_components', bundle_id=self.ca_product_id)
            components = [(5, 0, 0)]
            for vals in res.get('value', []):
                product = Product.search([('ca_product_id', '=', vals.get('ComponentID')), ('ca_profile_id', '=', vals.get('ProfileID'))], limit=1)
                if product:
                    components.append((0, 0, {
                        'product_id': product.id,
                        'quantity': vals.get('Quantity', 0),
                    }))
            self.write({'ca_bundle_product_ids': components})
        return True


class ProductProduct(models.Model):
    _inherit ='product.product'

    def inventory_update(self):

        xml_string = self.get_pdt_xml()
        date_today  = datetime.datetime.strptime(str(fields.Datetime.now()) , '%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
        # save_path_file = "Inventory_%s.xml" % date_today
        save_path_file = "/home/locksmith_keyless_13/odoo13/inventory_updates/" +"Inventory_%s.xml" % date_today
        with open(save_path_file, "w") as f:
            f.write(xml_string)
        return True

    def get_pdt_xml(self):

        xmlns_uris = {'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
                      'web': 'http://api.channeladvisor.com/webservices/'}
        try :
            products = self.search([('type', '=', 'product')])
            root_node = ET.Element("soapenv:Envelope")
            soap_header = SubElement(root_node, 'soapenv:Header')
            api_cred= SubElement(soap_header, 'web:APICredentials')
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


    def add_XMLNS_attributes(self,tree, xmlns_uris_dict):
        if not ET.iselement(tree):
            tree = tree.getroot()
        for prefix, uri in xmlns_uris_dict.items():
            tree.attrib['xmlns:' + prefix] = uri


class ProductBundle(models.Model):
    _name = "ca.product.bundle"
    _description = "Channel Advisor Product Bundle"

    product_id = fields.Many2one('product.product', string="Component")
    product_tmpl_id = fields.Many2one(related="product_id.product_tmpl_id", store=True)
    product_type = fields.Selection(related="product_id.ca_product_type", string="Product type", readonly=True, store=False)
    quantity = fields.Float(string="Quantity", default=1)
    bundle_id = fields.Many2one('product.template', string="Bundle")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
