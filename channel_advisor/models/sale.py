# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
# from ftplib import FTP
# from StringIO import StringIO
from xml.etree.ElementTree import Element, SubElement
from xml.etree import ElementTree
from xml.dom import minidom
import datetime


class SaleOrder(models.Model):
    _inherit = "sale.order"

    chnl_adv_order_id = fields.Char('CA OrderID')
    is_edi_order = fields.Boolean(string='CA Order', copy=False)
    is_fba = fields.Boolean(string='FBA Order', copy=False)
    is_review = fields.Boolean(string='Review', copy=False)
    margin_percent = fields.Float(string='Margin%', compute='_product_margin_percent', store=True)
    special_instruction = fields.Html(string='SpecialInstructions')
    private_note = fields.Html(string='Private Notes')
    total_price = fields.Float(string='CA Total')
    total_fees = fields.Float(string='Total Fees', default=0.0)

    @api.depends('order_line.margin','total_fees','margin','amount_untaxed')
    def _product_margin(self):
        margin =  super(SaleOrder, self)._product_margin()
        for order in self:
            if order.total_fees :
                order.margin = order.margin - order.total_fees



    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if res and res.partner_id.commission:
            res.total_fees = res.amount_untaxed * res.partner_id.commission / 100
        return res


    @api.depends('margin', 'amount_untaxed')
    def _product_margin_percent(self):
        for order in self:
            if order.margin and order.amount_untaxed:
                order.margin_percent = order.margin / order.amount_untaxed * 100


SaleOrder()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    margin = fields.Float(compute='_product_margin', digits='Product Price', store=True)
    margin_percent = fields.Float('Margin%', compute='_product_margin_percent', store=True)
    promotion_code = fields.Char("Promotion Code")
    promotion_amt =  fields.Float("Promotion%")

    @api.depends('product_id', 'purchase_price', 'product_uom_qty', 'price_unit', 'price_subtotal')
    def _product_margin(self):
        for line in self:
            currency = line.order_id.pricelist_id.currency_id
            price = line.purchase_price
            margin = line.price_subtotal - (price * line.product_uom_qty)
            line.margin = currency.round(margin) if currency else margin

    @api.depends('product_id', 'purchase_price', 'product_uom_qty', 'price_unit', 'price_subtotal')
    def _product_margin_percent(self):
        for line in self:
            price = line.purchase_price
            margin = line.price_subtotal - (price * line.product_uom_qty)
            if line.price_subtotal:
                line.margin_percent = margin / line.price_subtotal * 100



SaleOrderLine()




