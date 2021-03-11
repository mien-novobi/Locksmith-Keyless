# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def _freight_note(self):
        return """<h6 style="color:blue"><b>Freight get rate is calculated on assumption that the shipment is of single package, so price may vary during shipment</b></h6>"""

    # Which carrier used to ship
    shipping_carrier_id = fields.Many2one('shipping.carrier', 'Shipping Carrier', copy=False)
    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", copy=False)
    is_ship_collect = fields.Boolean('Ship Collect', copy=False)  # Is ship collect
    carrier_name = fields.Char('Carrier Name', copy=False)
    carrier_account_id = fields.Char('Carrier Account', copy=False)
    tracking_reference = fields.Char("Tracking Reference", copy=False)
    dropoff_type_id = fields.Many2one('shipping.dropoff.type', 'Dropoff Type')
    packaging_type_id = fields.Many2one('shipping.packaging.type', 'Packaging Type')
    package_detail_id = fields.Many2one('shipping.package.detail', 'Package Detail')
    physical_packaging_id = fields.Many2one('shipping.physical.packaging', 'Physical Packaging')
    package_type_count = fields.Integer('Count Package Type', compute='_get_carrier_package_type')
    packagedetail_count = fields.Integer('count Package Detail', compute='_get_carrier_packagedetail')
    physical_packaging_count = fields.Integer('Count Physical Packaging', compute='_get_carrier_physical_packaging')
    dropoff_type_count = fields.Integer('Count Dropof Type', compute='_get_dropoff_type_type')
    shipping_quote_lines = fields.One2many('shipping.quote', 'sale_id', 'Shipping Quotes')
    weight = fields.Float(compute='get_weight', string='Weight')
    tracking_url = fields.Char('Tracking Url', compute='_get_tracking_url', copy=False)
    freight_note = fields.Html('Note', default=_freight_note)
    freight = fields.Boolean(related='carrier_id.freight', string="Freight")
    home_delivery = fields.Boolean("Home Delivery")
    is_test = fields.Boolean('Is Test?', help='Is address verified')
    update_shipping_charge = fields.Boolean('Update shipping cost')
    is_edi_order = fields.Boolean(string="EDI Order?", default=False)

    @api.onchange('carrier_id')
    def onchange_carrier(self):
        if self.state in ('sale', 'progress', 'partially_shipped','shipped'):
            self.update_shipping_charge = True

    @api.depends('tracking_reference', 'shipping_carrier_id')
    def _get_tracking_url(self):
        """
            method generates a tracking url based
            on the configuration base url and tracking
            number if present
        """
        self.tracking_url = ''
        if self.tracking_reference and self.shipping_carrier_id:
            try:
                base_url = self.env[self.shipping_carrier_id.model_name].get_url(company_id=self.company_id and self.company_id.id)
                if base_url:
                    self.tracking_url = "%s%s" % (base_url, self.tracking_reference)
            except Exception:
                pass

    def open_website_url(self):
        self.ensure_one()
        if not self.tracking_url:
            raise UserError(
                _("Your delivery method has no redirect on courier provider's website to track this order."))

        return {
            'type': 'ir.actions.act_url',
            'name': "Shipment Tracking Page",
            'target': 'new',
            'url': self.tracking_url,
        }

    @api.onchange('shipping_carrier_id')
    def onchange_shipping_carrier_id(self):
        # if not self.is_ship_collect:
        if self.carrier_id.shipping_carrier_id != self.shipping_carrier_id:
            self.carrier_id = False

    @api.onchange('partner_id')
    def onchange_partner_id_carrier_id(self):
        if self.partner_id and self.partner_id.property_delivery_carrier_id:
            self.carrier_id  = self.partner_id.property_delivery_carrier_id.id

    @api.depends('order_line')
    def get_weight(self):
        # calculate total weight of products
        for order in self:
            weight = 0.0
            for line in order.order_line:
                if line.product_id and line.product_id.type != 'service':
                    weight = weight + (line.product_id.weight * line.product_uom_qty)
            order.weight = weight

    @api.depends('shipping_carrier_id')
    def _get_carrier_package_type(self):
        # method to update the package_type
        if self.shipping_carrier_id:
            self.package_type_count = len(self.shipping_carrier_id.packaging_type_ids)
            packaging_type_id = self.env['shipping.packaging.type'].search([('carrier_id', '=', self.shipping_carrier_id.id), ('is_default', '=', True)], limit=1)
            if packaging_type_id:
                self.packaging_type_id = packaging_type_id.id
        else:
            self.packaging_type_id = None
            self.package_type_count = 0

    @api.depends('shipping_carrier_id')
    def _get_carrier_packagedetail(self):
        # method to update the package_detail
        if self.shipping_carrier_id:
            self.packagedetail_count = len(self.shipping_carrier_id.package_detail_ids) or 0
            package_detail_id = self.env['shipping.package.detail'].search([('carrier_id', '=', self.shipping_carrier_id.id), ('is_default', '=', True)], limit=1)
            if package_detail_id:
                self.package_detail_id = package_detail_id.id
        else:
            self.package_detail_id = None
            self.packagedetail_count = 0

    @api.depends('shipping_carrier_id')
    def _get_carrier_physical_packaging(self):
        # method to update the physical_packaging
        if self.shipping_carrier_id:
            self.physical_packaging_count = len(self.shipping_carrier_id.physical_packaging_ids) or 0
            physical_packaging_id = self.env['shipping.physical.packaging'].search([('carrier_id', '=', self.shipping_carrier_id.id), ('is_default', '=', True)], limit=1)
            if physical_packaging_id:
                self.physical_packaging_id = physical_packaging_id and physical_packaging_id.id
        else:
            self.physical_packaging_id = None
            self.physical_packaging_count = 0

    @api.depends('shipping_carrier_id')
    def _get_dropoff_type_type(self):
        # method to update the dropoff_type
        if self.shipping_carrier_id:
            self.dropoff_type_count = len(self.shipping_carrier_id.dropoff_type_ids) or 0
            dropoff_type_id = self.env['shipping.dropoff.type'].search([('carrier_id', '=', self.shipping_carrier_id.id), ('is_default', '=', True)], limit=1)
            if dropoff_type_id:
                self.dropoff_type_id = dropoff_type_id.id
        else:
            self.dropoff_type_id = None
            self.dropoff_type_count = 0

    #todo client dont need to change the carrier account_id
    # @api.onchange('is_ship_collect')
    def _get_carrier_info(self):
        """ fetches the shipping account name and account id from res.partner
            if the partner opts for ship collect type shipping in sale order.
            Method also responsible for the toggling of visibility of ship collect
            account name and account id fields in order.
        """
        self.carrier_account_id = ''
        # carrier_id =False
        if self.is_ship_collect and self.partner_id:
            self.carrier_account_id = self.partner_shipping_id.carrier_account_id or self.partner_id.carrier_account_id
            # carrier_id = self.partner_shipping_id.property_delivery_carrier_id or self.partner_id.property_delivery_carrier_id
            # self.carrier_account_id = carrier_account_id
            # self.carrier_id = bool(carrier_id) and carrier_id.id or False
            # self.shipping_carrier_id = bool(carrier_id) and carrier_id.shipping_carrier_id and carrier_id.shipping_carrier_id.id or False

    @api.model
    def get_default_shipping_configuration(self, shipping_carrier_id):
        dropoff_type = self.env['shipping.dropoff.type'].search(
            [('carrier_id', '=', shipping_carrier_id), ('is_default', '=', True)], limit=1)
        physical_packaging = self.env['shipping.physical.packaging'].search(
            [('carrier_id', '=', shipping_carrier_id), ('is_default', '=', True)], limit=1)
        package_detail = self.env['shipping.package.detail'].search(
            [('carrier_id', '=', shipping_carrier_id), ('is_default', '=', True)], limit=1)
        packaging_type = self.env['shipping.packaging.type'].search(
            [('carrier_id', '=', shipping_carrier_id), ('is_default', '=', True)], limit=1)
        return {
            'dropoff_type_id': dropoff_type and dropoff_type.id or False,
            'physical_packaging_id': physical_packaging and physical_packaging.id or False,
            'package_detail_id' : package_detail and package_detail.id or False,
            'packaging_type_id': packaging_type and packaging_type.id or False,
        }

    def _generate_shipping_data(self):
        """
        The compacted method used to return all details necessary
        to fetch shipping rates or print shipping label.
        """
        data = {
            'dropoff_type': self.dropoff_type_id and self.dropoff_type_id.code or False,
            'service_type': self.carrier_id and self.carrier_id.service_code or False,
            'packaging_type': self.packaging_type_id and self.packaging_type_id.code or False,
            'package_detail': self.package_detail_id and self.package_detail_id.code or False,
            'physical_packaging': self.physical_packaging_id and self.physical_packaging_id.code or False,
            'package_count': 1,  # add mps value to it
            'weight': self.weight,
            'currency': self.company_id.currency_id and self.company_id.currency_id.name or False,
            'monetary': 0,  # add product price
            'pieces': 1,  # add no of package
            'origin': self.name,
            'unit_price': False,  # add unit price
            'company_id': self.company_id and self.company_id.id
        }
        sender = self.company_id.partner_id._get_address()
        recipient = self.partner_shipping_id._get_address()
        while isinstance(sender, list):
            sender = sender[0]
        while isinstance(recipient, list):
            recipient = recipient[0]
        data.update({'sender': sender, 'recipient': recipient})
        return data

    def _update_shipping_data(self, shipping_carrier=None):
            return {}

    def get_rate(self):
        """
        The generalised method used to fetch the rates
        of shipping method given based on the given package data
        trigerred by the get rate button in sale order.
        if no carrier or carrier method is specified,
        tries to get rate of all shipping methods.
        if carrier and shipping method are specified,
        fetches only the rates of given shipping method.
        """
        ShippingQuote = self.env['shipping.quote']
        for order in self:
            # order.check_address_validate()
            vals = {}
            res = []
            delivery_area = ('domestic', 'both')
            if (order.partner_shipping_id.country_id and order.partner_shipping_id.country_id.code or '') != (
                    order.company_id.country_id and order.company_id.country_id.code or ''):
                delivery_area = ('international', 'both')
            data = order._generate_shipping_data()
            while isinstance(data, list):
                data = data[0]
            height = depth = width = 0
            weight = order.weight
            for line in order.order_line:
                if line.product_id and line.product_id.type == 'service':
                    continue
                if not line.product_id.weight:
                    raise UserError(_('The product %s does not have weight values' % line.product_id.name))
                if line.product_id and line.product_id.depth > depth:
                    depth = line.product_id.depth
                if line.product_id and line.product_id.height > height:
                    height = line.product_id.height
                if line.product_id and line.product_id.width > width:
                    width = line.product_id.width
            if order.carrier_id and order.carrier_id.service_code == 'STANDARD_FREIGHT':
                return True
            if order.shipping_quote_lines:
                order.shipping_quote_lines.unlink()
            # shipping carrier selected then get rates of all types which supports this package
            if order.carrier_id:
                residential = order.carrier_id.validate_residential_address(partner=order.partner_shipping_id) or False
                data.update({'is_residential' : residential})
                if not order.shipping_carrier_id:
                    order.shipping_carrier_id = order.carrier_id.shipping_carrier_id and order.carrier_id.shipping_carrier_id.id
                res = self.env[order.shipping_carrier_id.model_name].get_rate(data)
                for vals in res:
                    if order.company_id and order.company_id.markup_rate:
                        carrier_charge = float(vals.get('rate', 0.0))
                        rate = carrier_charge + carrier_charge * (order.company_id.markup_rate / 100)
                        vals.update({'rate': carrier_charge, 'markup_rate': rate})

                    ShippingQuote.create({
                        'name': vals.get('service_name'),
                        'sale_id': order.id,
                        'weight': weight,
                        'shipping_carrier_id': order.shipping_carrier_id.id,
                        'carrier_id': order.carrier_id.id,
                        'rate': vals.get('rate'),
                        'markup_rate': vals.get('markup_rate'),
                    })
            else:
                try:
                    AvailableCarriers = order.shipping_carrier_id or self.env['shipping.carrier'].search([
                        ('company_id', '=', order.company_id.id), ('active', '=', True)])
                    carrier_response = []
                    available_services = {}
                    for ShippingCarrier in AvailableCarriers:
                        checked_residential = False
                        residential = False
                        delivery_carriers = self.env['delivery.carrier'].search([
                            ('shipping_carrier_id', '=', ShippingCarrier.id),
                            ('delivery_area', 'in', delivery_area),
                        ])
                        for method in delivery_carriers:
                            if (method.weight > 0 and method.weight >= weight) or (method.weight < 0 and abs(method.weight) <= weight):
                                if not checked_residential:
                                    residential = method.validate_residential_address(partner=order.partner_shipping_id)
                                    checked_residential = True
                                available_services[method.service_code] = method

                        data.update({'is_residential': residential})
                        data.update(order._update_shipping_data(ShippingCarrier))

                        response = self.env[ShippingCarrier.model_name].get_rate(data)
                        carrier_response.extend(response)

                    for carrier in carrier_response:
                        delivery_carrier = available_services.get(carrier.get('service_type', ''))
                        if delivery_carrier:
                            if order.company_id and order.company_id.markup_rate:
                                charge = float(carrier.get('rate', 0.0))
                                rate = charge + charge * (order.company_id.markup_rate / 100)
                                carrier.update({'rate': charge, 'markup_rate': rate})
                            ShippingQuote.create({
                                'name': carrier.get('service_name'),
                                'sale_id': order.id,
                                'shipping_carrier_id': delivery_carrier.shipping_carrier_id.id,
                                'weight': weight,
                                'carrier_id': delivery_carrier.id,
                                'rate': carrier.get('rate'),
                                'markup_rate': carrier.get('markup_rate'),
                            })
                except Exception as e:
                    pass

            if weight:
                for quote in ShippingQuote.search([('weight', '!=', weight), ('sale_id', '=', order.id)]):
                    quote.unlink()
            return vals

    @api.model
    def update_weight(self, order):
        weight = 0.0
        for line in order.order_line:
            if line.product_id and line.product_id != 'service':
                pdt_weight = line.product_id.weight or 0.0
                weight += (pdt_weight * line.product_uom_qty)
        return weight

    def action_confirm(self):
        for order in self:
            if order.partner_shipping_id.country_id and order.partner_shipping_id.zip:
                if order.carrier_id:
                    if (order.home_delivery or order.carrier_id.validate_residential_address(partner=order.partner_shipping_id))\
                        and order.carrier_id.service_code == 'FEDEX_GROUND':
                        address = "%s; %s; %s; %s"%(order.partner_shipping_id.street, order.partner_shipping_id.street2, order.partner_shipping_id.city,order.partner_shipping_id.zip)
                        logging.error("Forcing Home Delivery for %s partner %s - %s - %s"%(order.name,order.partner_shipping_id.name,order.partner_shipping_id,address))
                        raise UserError(_('The Shipment supports Home Delivery '))
                    if order.carrier_id.name == 'TBD':
                        raise UserError(_("Invalid Data\nPlease Select a valid shipping type"))
            elif not order.is_edi_order and order.shipping_carrier_id:
                raise UserError('Country or Zip Code missing in Delivery address')
        return super(SaleOrder, self).action_confirm()

    @api.model
    def get_shipping_values(self, sale):
        '''
        This function is used to correct shiping values to update manufacture quote and picking
        @ param self : Self of the object
        @ param sale : SaleOrder Record

        @ return : dict
        '''

        data = {}
        if sale:
            data.update({
                'shipping_carrier_id': sale.shipping_carrier_id and sale.shipping_carrier_id.id or False,
                'dropoff_type_id': sale.dropoff_type_id and sale.dropoff_type_id.id or False,
                'packaging_type_id': sale.packaging_type_id and sale.packaging_type_id.id or False,
                'package_detail_id': sale.package_detail_id and sale.package_detail_id.id or False,
                'physical_packaging_id': sale.physical_packaging_id and sale.physical_packaging_id.id or False,
                'is_ship_collect': sale.is_ship_collect,
                'carrier_id': sale.carrier_id and sale.carrier_id.id or False,
            })
            if sale.is_ship_collect:
                data.update({'carrier_name': sale.carrier_name, 'carrier_account_id': sale.carrier_account_id})
        return data

    def write(self, vals):
        if vals.get('shipping_carrier_id'):
            shipping_conf = self.get_default_shipping_configuration(vals.get('shipping_carrier_id'))
            for key, val in shipping_conf.items():
                if not key in vals:
                    vals.update({key: val})
        res = super(SaleOrder, self).write(vals)
        for sale in self:
            data = {}
            home_delivery = False
            FedexGround = self.env['delivery.carrier'].search(
                [('service_code', '=', 'FEDEX_GROUND'), ('company_id', '=', sale.company_id.id)], limit=1)
            GroundHomeDelivery = self.env['delivery.carrier'].search(
                [('service_code', '=', 'GROUND_HOME_DELIVERY'), ('company_id', '=', sale.company_id.id)], limit=1)
            do_validation = False
            carrier = False
            if vals.get('carrier_id'):
                carrier = self.env['delivery.carrier'].browse(vals.get('carrier_id'))
                sale.message_post(body="Carrier Updated to %s"%(carrier.name))
            else:
                carrier = sale.carrier_id
            if vals.get('partner_shipping_id'):
                sale.message_post(body="Delivery Address updated to %s"%(sale.partner_shipping_id.name))
            if vals.get('carrier_id', False) or vals.get('partner_shipping_id', False):

                if carrier and carrier.id in (FedexGround.id, GroundHomeDelivery.id):
                    if vals.get('partner_shipping_id'):
                        do_validation = True
                        home_delivery = False
                    elif FedexGround and vals.get('carrier_id', '') == FedexGround.id:
                        do_validation = True
                    elif GroundHomeDelivery and vals.get('carrier_id', '') == GroundHomeDelivery.id:
                        do_validation = True
                        home_delivery = False
                    if do_validation:
                        result = carrier and carrier.validate_residential_address(partner=sale.partner_shipping_id)
                        if result:
                            home_delivery = True
                        elif carrier and carrier.id == GroundHomeDelivery.id:
                            raise UserError(_('The Shipment does not supports Home Delivery ! Please change the carrier !'))
                    else:
                        home_delivery = False
                if sale.home_delivery != home_delivery:
                    sale.home_delivery = home_delivery

            if vals.get('carrier_account_id') or vals.get('carrier_name') or \
                    (carrier and carrier.service_code != 'Fedex_TBD' or 'carrier_id' in vals and not carrier):
                # checking updations in the specific field
                data.update(sale.get_shipping_values(sale))
            if vals.get('is_ship_collect'):
                data.update({'is_ship_collect': vals.get('is_ship_collect')})

            if data:
                # updates shipping info to ManufacturingQuotes
                # ManufacturingQuotes = self.env['manufacture.quote'].search([('order_id', '=', sale.id),
                #                                                     ('state', 'in', (
                #                                                     'draft', 'submitted', 'approved', 'confirmed',
                #                                                     'production_started', 'production_completed',
                #                                                     'on_hold'))])
                # if len(ManufacturingQuotes):
                #     if vals.get('carrier_id', False):
                #         ManufacturingQuotes.write({'carrier_id': vals.get('carrier_id', False)})
                #     if sale.shipping_carrier_id:
                #         ManufacturingQuotes.write(data)

                # updates shipping info to Pickings
                picking_ids = self.env['stock.picking'].search(
                    [('sale_id', '=', sale.id), ('state', 'in', ('draft', 'waiting', 'assigned', 'confirmed'))])
                if len(picking_ids):
                    if vals.get('carrier_id', False):
                        picking_ids.write({'carrier_id': vals.get('carrier_id', False)})
                    if sale.shipping_carrier_id:
                        picking_ids.write(data)
        return res

    @api.model
    def create(self, vals):
        if vals.get('shipping_carrier_id'):
            shipping_conf = self.get_default_shipping_configuration(vals.get('shipping_carrier_id'))
            for key, val in shipping_conf.items():
                if not key in vals:
                    vals.update({key: val})
        Order = super(SaleOrder, self).create(vals)
        DeliveryCarrier = self.env['delivery.carrier']
        dimension_vals = []
        weight = 0.0
        if Order:
            if not Order.carrier_id and not Order.is_ship_collect:
                for line in Order.order_line:
                    if not line.product_id or line.product_id.type == 'service':
                        continue
                    dimension_vals.extend([line.product_id.depth or 0, line.product_id.width or 0, line.product_id.height or 0])
                    weight = weight + (line.product_id.weight * line.product_uom_qty)
                if dimension_vals:
                    carrier = False
                    if weight > 150 or max(dimension_vals) > 36:
                        carrier = DeliveryCarrier.search(
                            [('service_code', '=', 'STANDARD_FREIGHT'), ('company_id', '=', Order.company_id.id)],
                            limit=1)
                    else:
                        carrier = DeliveryCarrier.search(
                            [('service_code', '=', 'FEDEX_GROUND'), ('company_id', '=', Order.company_id.id)], limit=1)
                    if carrier:
                        Order.carrier_id = carrier.id
                        Order.shipping_carrier_id = carrier.shipping_carrier_id.id
            if vals.get('carrier_id') or vals.get('partner_shipping_id'):
                if vals.get('partner_shipping_id'):
                    Order.message_post(body="Delivery Address :  %s"%(Order.partner_shipping_id.name))
                if vals.get('carrier_id'):
                    Order.message_post(body="Carrier :  %s"%(Order.carrier_id.name))
                if Order.carrier_id:
                    Order.shipping_carrier_id = Order.carrier_id.shipping_carrier_id and Order.carrier_id.shipping_carrier_id.id
                    if Order.carrier_id.service_code == 'FEDEX_GROUND':
                        result = Order.carrier_id.validate_residential_address(partner=Order.partner_shipping_id)
                        if result:
                            Order.home_delivery = True
                        else:
                            Order.home_delivery = False
                else:
                    if Order.partner_shipping_id.picking_warn_msg:
                        Order.home_delivery = False
        return Order

    def update_tracking_number(self, tracking_no):
        return self.write({'tracking_reference': tracking_no})

    def check_shipping_method(self):
        result = True
        # TODO shipping_method char field from prestaerp check dependency
        for order in self:
            if (order.shipping_method and order.shipping_method == 'FEDEX_GROUND') and (
                order.carrier_id and order.carrier_id.service_code == 'GROUND_HOME_DELIVERY'):
                result = False
        return result

    def update_shiping_cost(self, rate=0, carrier_id=False):
        '''Method to update shipping cost from either manufacturing portal or stock picking
        @ return True
        '''

        ship_rate = 0.0
        for order in self:
            data = {}  # Values to write in sale order
            if not order.free_shipping and not order.is_ship_collect:
                if not carrier_id:
                    raise UserError(_('Shipping service output settings not defined'))
                if not carrier_id.free_over:
                    markup = order.company_id and order.company_id.markup_rate or 0.0
                    try:
                        rate = float(rate)
                        ship_rate = rate + ((rate / 100) * markup or 1.0)
                    except:
                        ship_rate = 0.0
                        rate = 0.0
                    shipping_line = order.order_line.filtered(lambda rec: (rec.is_delivery == True or rec.is_shipping == True and len(rec.invoice_lines) == 0))
                    # if shipping line update that line   #TODO shipping_method char field from prestaerp check dependency
                    if len(shipping_line):
                        if (order.carrier_id and order.carrier_id.service_code != order.shipping_method and order.check_shipping_method()) or (
                                    order.carrier_id and order.carrier_id.service_code == 'STANDARD_FREIGHT'):
                            if shipping_line.shipping_charge_updation:
                                data.update({'price_unit': float(shipping_line.price_unit) + float(ship_rate),
                                             'purchase_price': shipping_line.purchase_price + rate})
                            else:
                                data.update({
                                    'price_unit': float(ship_rate),
                                    'purchase_price': rate,
                                    'shipping_charge_updation': True
                                })
                            shipping_line.write(data)
                    else:  # Create new line
                        if not order.is_ship_collect and order.check_shipping_method():
                            # todo type is not used in new version
                            # line_type = False
                            # if order.web_store_id and order.web_store_id.product_id and order.web_store_id.product_id.route_ids:
                            #     if self.env.ref(
                            #             "stock.route_warehouse0_mto").id in order.web_store_id.product_id.route_ids.ids:
                            #         line_type = 'make_to_order'
                            #     else:
                            #         line_type = 'make_to_stock'
                            order.write({
                                'carrier_id': carrier_id.id,
                                'order_line': [(0, 0, {
                                    'product_id': carrier_id.product_id and carrier_id.product_id.id,
                                    'product_uom': carrier_id.product_id and carrier_id.product_id.product_tmpl_id.uom_id.id,
                                    'price_unit': float(ship_rate),
                                    'purchase_price': float(rate),
                                    'product_uom_qty': 1,
                                    'name': order.web_store_id and order.web_store_id.product_id.name,
                                    # 'type': line_type,
                                    'is_shipping': True,
                                    'is_delivery': True,
                                    'shipping_charge_updation': True,
                                })]
                            })
        return True

    def check_address_validate(self):
        """
        Method to check address is valid
        :return: Boolean
        """
        invalid_field = []
        # messages = []
        # exp_msg = 'The following fields are not found in address: '
        self.ensure_one()
        if self.partner_shipping_id.country_id and self.partner_shipping_id.country_id.code != 'US':
            self.is_test = True
            return True
        if not (self.partner_shipping_id.street or self.partner_shipping_id.street2):
            invalid_field.append("Street")
        if not self.partner_shipping_id.city:
            invalid_field.append("City")
        if not self.partner_shipping_id.country_id:
            invalid_field.append("Country")
        if self.partner_shipping_id.country_id and self.partner_shipping_id.country_id.code == 'US' and not self.partner_shipping_id.state_id:
            invalid_field.append("State")
        if not self.partner_shipping_id.mobile and not self.partner_shipping_id.phone:
            invalid_field.append("Phone Number")
        if not self.partner_shipping_id.zip:
            invalid_field.append("Zipcode")
        if not invalid_field and self.partner_shipping_id.country_id.code == 'US':
            result = self.carrier_id and self.carrier_id.validate_address(partner=self.partner_shipping_id)
            if (not self.carrier_id and self.is_ship_collect) or result:
                self.is_test = True
                return True
            else:
                raise UserError(_('Address not verified'))
        elif invalid_field:
            error_msg = "The following fields are not found in address: "
            error_msg += ", ".join(invalid_field)
            raise UserError(_(error_msg))
        return False


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    is_shipping = fields.Boolean('Is Shipping')
    is_carrier = fields.Boolean('Is Carrier')
    shipping_charge_updation = fields.Boolean("Shipping Charge Updation")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
