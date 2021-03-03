# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _

from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare, float_round


_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    regenerate_shiping_label = fields.Boolean('Regenerate Shipping Label')
    is_label_generated = fields.Boolean('Is Label generate')
    shipping_carrier_id = fields.Many2one('shipping.carrier', 'Shipping Carrier')
    is_ship_collect = fields.Boolean('Ship Collect') #Ship Using Customer Account
    carrier_name = fields.Char('Carrier Name')
    carrier_account_id = fields.Char('Carrier Account')
    tracking_number = fields.Char("Tracking Reference")
    dropoff_type_id = fields.Many2one('shipping.dropoff.type', 'Dropoff Type')
    packaging_type_id = fields.Many2one('shipping.packaging.type', 'Packaging Type')
    package_detail_id = fields.Many2one('shipping.package.detail', 'Package Detail')
    physical_packaging_id = fields.Many2one('shipping.physical.packaging', 'Physical Packaging')
    shipping_type = fields.Selection([
        ('residential', 'Residential'),
        ('freight', 'Standard Freight'),
        ('shipcollect','Third Party Shipping'),
        ], string='Shipping Type', related='carrier_id.shipping_type')
    dimension_ids = fields.One2many('picking.dimensions','picking_id', 'Dimensions')   # attrs={'readonly':[('shipping_type','not in', ('shipcollect','freight'))]}
    package_type_count = fields.Integer('Count Package Type', compute='_get_carrier_package_type')
    packagedetail_count = fields.Integer('count Package Detail', compute='_get_carrier_packagedetail')
    physical_packaging_count = fields.Integer('Count Physical Packaging', compute='_get_carrier_physical_packaging')
    dropoff_type_count = fields.Integer('Count Dropof Type', compute='_get_dropoff_type_type')
    tracking_url = fields.Char('Tracking Url', compute='_get_tracking_url')
    no_of_packages = fields.Integer('Number of Packages', compute='_get_number_of_package')
    shipping_quote_lines = fields.One2many('shipping.quote', 'picking_id', 'Shipping Quotes', copy=False)
    carrier_price = fields.Float(string="Shipping Cost", copy=False)
    reshipment = fields.Boolean(string='Reshipment', default=False)

    def action_draft_confirm(self):
        self.ensure_one()
        if self.picking_type_code in ['internal','outgoing']:
            for ops in self.move_line_ids.filtered(lambda x: not x.move_id):
                if not ops.qty_done:
                    raise UserError("You can't confirm a Delivery Order without Done qty")
                # Search move with this product
                moves = self.move_lines.filtered(lambda x: x.product_id == ops.product_id)
                if moves: #could search move that needs it the most (that has some quantities left)
                    ops.move_id = moves[0].id
                else:
                    new_move = self.env['stock.move'].create({
                        'name': _('New Move:') + ops.product_id.display_name,
                        'product_id': ops.product_id.id,
                        'product_uom_qty': ops.qty_done,
                        'product_uom': ops.product_uom_id.id,
                        'location_id': self.location_id.id,
                        'location_dest_id': self.location_dest_id.id,
                        'picking_id': self.id,
                    })
                    ops.move_id = new_move.id
            self.action_confirm()
            return self.action_assign()

    @api.depends('shipping_carrier_id', 'carrier_tracking_ref')
    def _get_tracking_url(self):
        """
            method generates a tracking url based
            on the configuration base url and tracking
            number if present
        """
        for picking in self:
            picking.tracking_url = ''
            if picking.carrier_tracking_ref and picking.shipping_carrier_id:
                try:
                    if picking.carrier_id and picking.carrier_id.freight and picking.shipping_carrier_id.model_name == 'ups.connector':
                        base_url = self.with_context(ups_freight=True).env[picking.shipping_carrier_id.model_name].get_url(company_id = picking.company_id and picking.company_id.id)
                    else:
                        base_url = self.env[picking.shipping_carrier_id.model_name].get_url(company_id=picking.company_id and picking.company_id.id)

                    if base_url:
                        picking.tracking_url = "%s%s" % (base_url, picking.carrier_tracking_ref)
                except Exception:
                    pass

    @api.depends('shipping_carrier_id')
    def _get_dropoff_type_type(self):
        # method to update the dropoff_type
        for picking in self:
            if picking.shipping_carrier_id :
                picking.dropoff_type_count = len(picking.shipping_carrier_id.dropoff_type_ids) or 0
                dropoff_type_id = self.env['shipping.dropoff.type'].search([('carrier_id', '=', picking.shipping_carrier_id.id), ('is_default', '=', True)], limit=1)
                picking.dropoff_type_id = dropoff_type_id and dropoff_type_id.id
            else:
                picking.dropoff_type_id = False
                picking.dropoff_type_count = 0

    @api.depends('shipping_carrier_id')
    def _get_carrier_package_type(self):
        # method to update the package_type
        for picking in self:
            if picking.shipping_carrier_id :
                picking.package_type_count = len(picking.shipping_carrier_id.packaging_type_ids)
                packaging_type_id = self.env['shipping.packaging.type'].search([('carrier_id', '=', picking.shipping_carrier_id.id), ('is_default', '=', True)], limit = 1)
                picking.packaging_type_id = packaging_type_id and packaging_type_id.id
            else:
                picking.packaging_type_id = False
                picking.package_type_count = 0

    @api.depends('shipping_carrier_id')
    def _get_carrier_packagedetail(self):
        # method to update the package_detail
        for picking in self:
            if picking.shipping_carrier_id :
                picking.packagedetail_count = len(picking.shipping_carrier_id.package_detail_ids) or 0
                package_detail_id = self.env['shipping.package.detail'].search([
                    ('carrier_id', '=', picking.shipping_carrier_id.id), ('is_default', '=', True)], limit=1)
                picking.package_detail_id = package_detail_id and package_detail_id.id
            else:
                picking.packagedetail_count = 0
                picking.package_detail_id = False

    @api.depends('dimension_ids')
    def _get_number_of_package(self):
        # method to update nuber of packages
        self.ensure_one()
        for picking in self:
            self.no_of_packages = len(picking.dimension_ids) or 0

    @api.depends('shipping_carrier_id')
    def _get_carrier_physical_packaging(self):
        # method to update the physical_packaging
        for picking in self:
            if picking.shipping_carrier_id :
                picking.physical_packaging_count = len(picking.shipping_carrier_id.physical_packaging_ids) or 0
                physical_packaging_id = self.env['shipping.physical.packaging'].search([
                    ('carrier_id', '=', picking.shipping_carrier_id.id), ('is_default', '=', True)], limit=1)
                picking.physical_packaging_id = physical_packaging_id and physical_packaging_id.id
            else:
                picking.physical_packaging_id = False
                picking.physical_packaging_count = 0

    def _get_shipping_data(self, quote=None):
        """
        The compacted method used to return all details necessary
        to fetch shipping rates or print shipping label.
        @:param quote: manufactrure.quote record set
        """
        self.ensure_one()
        data = {}
        customs_value = False
        sender_id = False
        recipient_id = False
        residential = False
        WarehouseObj = self.env['stock.warehouse']

        if not quote:
            if self.sale_id.warehouse_id and self.sale_id.warehouse_id.partner_id:
                sender_id = self.sale_id.warehouse_id and self.sale_id.warehouse_id.partner_id
            else:
                sender_id = self.company_id and self.company_id.partner_id
            recipient_id = self.partner_id
            order_ref = self.origin
            po_number = self.sale_id and self.sale_id.client_order_ref or ''
            # customs_value =  self.sale_id and self.sale_id.partner_id and self.sale_id.partner_id.duty_payable or ''
            if self.is_ship_collect:
                data.update({'account_number': self.carrier_account_id, 'is_ship_collect': True})
        else:
            sender_id = quote.manufacturer_id and quote.manufacturer_id.partner_id and quote.manufacturer_id.partner_id
            order_ref = quote.order_id and quote.order_id.name
            po_number = quote.order_id and quote.order_id.client_order_ref or ''
            if quote.is_ship_collect:
                data.update({'account_number': quote.carrier_account_id, 'is_ship_collect': True})
            if quote.order_id:
                # customs_value = quote.order_id and quote.order_id.partner_id and quote.order_id.partner_id.duty_payable or ''
                recipient_id = quote.order_id and quote.order_id.partner_shipping_id and quote.order_id.partner_shipping_id
            else:
                if quote.location_id:
                    if quote.location_id.partner_id:
                        recipient_id = quote.location_id.partner_id or False
                        # customs_value = quote.location_id.partner_id.duty_payable or ''
                    else:
                        warehouse = WarehouseObj.search([('lot_stock_id', '=', quote.location_id.id)], limit=1)
                        if warehouse:
                            recipient_id = warehouse.partner_id or quote.company_id and quote.company_id.partner_id or False
                            # customs_value = recipient_id and recipient_id.duty_payable or ''

        if not sender_id or not recipient_id:
            raise UserError(_('Sender / Recipient not defined'))

        if self.carrier_id:
            residential = self.carrier_id.validate_residential_address(partner=recipient_id)

        sender = sender_id and sender_id._get_address() or {}
        recipient = recipient_id and recipient_id._get_address() or {}

        #replace mp name with brand name on labels for incoming shipments
        if quote and quote.company_id and not quote.order_id and sender:
            sender.update({'name':quote.company_id.name})

        #remove company name in label if recipient opted for blind shipment
        # if recipient_id and recipient and recipient_id.blind_shipment:
        #     recipient.update({'company_name':''})

        data.update({
            'sender': sender,
            'recipient': recipient,
            'dropoff_type': self.dropoff_type_id and self.dropoff_type_id.code or False,
            'service_type': self.carrier_id and self.carrier_id.service_code or False,
            'packaging_type': self.packaging_type_id and self.packaging_type_id.code or False,
            'package_detail': self.package_detail_id and self.package_detail_id.code or False,
            'physical_packaging': self.physical_packaging_id and self.physical_packaging_id.code or False,
            'weight': self.weight,
            'currency': self.company_id.currency_id and self.company_id.currency_id.name or False,
            'monetary': 0,  # add product price
            'name': self.name,
            'unit_price': False,  # add unit price
            'origin': self.origin,
            'currency_code': self.company_id.currency_id.name,
            'product_list' : self.move_lines,
            'order_ref': order_ref,
            'po_number': po_number and po_number[:40],
            'customs_value': customs_value,
            'reference': self.sale_id and self.sale_id.client_order_ref or self.sale_id.name,
            'company_id': self.company_id and self.company_id.id or False,
            'is_residential' : residential

        })
        return data

    def onchange_ship_collect(self):
        for picking in self:
            if not picking.is_ship_collect:
                picking.carrier_account_id = ''

    def write(self, vals):
        result = super(StockPicking, self).write(vals)
        # below call is used to update changes in shipping method to correponding sale order
        ship_rate = 0
        for picking in self:
            values = {}
            if vals.get('carrier_id', False):
                picking.message_post(body="Delivery order Carrier Updated to %s"%(picking.carrier_id.name))
            if picking.sale_id:
                SaleOrder = picking.sale_id
                if vals.get('carrier_tracking_ref', False):
                    values.update({'tracking_reference' : vals.get('carrier_tracking_ref', False)})
                if vals.get('carrier_id', False) and SaleOrder.carrier_id and SaleOrder.carrier_id.id != vals.get('carrier_id'):
                    values.update({'carrier_id' : vals.get('carrier_id')})
                if vals.get('is_ship_collect', False) :
                    values.update({'is_ship_collect' : vals.get('is_ship_collect', False)})
                if vals.get('carrier_account_id', '') :
                    values.update({ 'carrier_account_id' : vals.get('carrier_account_id', '')})
                # len(values) and picking.sale_id.write(values)# TODO in version 7 values not updating to SO
        return result

    def _add_delivery_cost_to_so(self):
        self.ensure_one()
        sale_order = self.sale_id
        if not self.reshipment and sale_order and not sale_order.is_ship_collect and not self.is_ship_collect:
            markup = sale_order.company_id and sale_order.company_id.markup_rate or 0.0
            try:
                rate = float(self.carrier_price)
                ship_rate = rate + ((rate / 100) * markup or 1.0)
            except:
                ship_rate = 0.0
                rate = 0.0
            if self.company_id.configuration:
                # if (sale_order.carrier_id and sale_order.carrier_id.service_code != sale_order.shipping_method and sale_order.check_shipping_method()) or (
                #                 sale_order.carrier_id and sale_order.carrier_id.service_code == 'STANDARD_FREIGHT'):
                CarrierLine = sale_order.order_line.filtered(
                    lambda line: (line.is_delivery is True or line.is_shipping is True) and len(line.invoice_lines) == 0)
                update_shipping = False
                if CarrierLine and CarrierLine.shipping_charge_updation:
                    rate = CarrierLine.purchase_price + rate
                if sale_order.update_shipping_charge:
                    update_shipping = True
                    if len(sale_order.picking_ids.filtered(lambda rec: rec.state == 'done')) > 1 and CarrierLine\
                            and CarrierLine.shipping_charge_updation or CarrierLine and CarrierLine.shipping_charge_updation:
                        ship_rate = float(CarrierLine.price_unit) + float(ship_rate)
                elif sale_order.carrier_id != self.carrier_id:
                    update_shipping = True
                    if len(sale_order.picking_ids.filtered(lambda rec: rec.state == 'done')) > 1  and CarrierLine\
                            and CarrierLine.shipping_charge_updation or CarrierLine and CarrierLine.shipping_charge_updation:
                        ship_rate = float(CarrierLine.price_unit) + float(ship_rate)
                elif len(sale_order.picking_ids.filtered(lambda rec: rec.state == 'done')) > 1 :
                    update_shipping = True
                    if CarrierLine and CarrierLine.shipping_charge_updation:
                        ship_rate = float(CarrierLine.price_unit) + float(ship_rate)

                # --------- FOR EDI ORDERS ------------
                if sale_order.is_edi_order:
                    ship_rate = 0
                # -------------------------------------

                if update_shipping and CarrierLine:
                    CarrierLine.write({
                        'price_unit': float(ship_rate),
                        'purchase_price': rate,
                        'product_id': self.carrier_id.product_id and self.carrier_id.product_id.id,
                        'name': self.carrier_id.product_id and self.carrier_id.product_id.name,
                        'shipping_charge_updation': True,
                    })
                elif update_shipping:
                    sale_order.write({
                        'order_line': [(0, 0, {
                            'product_id': self.carrier_id.product_id and self.carrier_id.product_id.id,
                            'product_uom': self.carrier_id.product_id and self.carrier_id.product_id.uom_id.id,
                            'price_unit': float(ship_rate),
                            'purchase_price': rate,
                            'product_uom_qty': 1,
                            'name': self.carrier_id.product_id and self.carrier_id.product_id.name,
                            'is_shipping': True,
                            'is_delivery': True,
                            'shipping_charge_updation': True,
                        })]
                    })
                elif CarrierLine:
                    CarrierLine.write({
                        'purchase_price': rate,
                    })
                elif not CarrierLine:
                    sale_order.write({
                        'order_line': [(0, 0, {
                            'product_id': self.carrier_id.product_id and self.carrier_id.product_id.id,
                            'product_uom': self.carrier_id.product_id and self.carrier_id.product_id.uom_id.id,
                            'price_unit': float(ship_rate),
                            'purchase_price': rate,
                            'product_uom_qty': 1,
                            'name': self.carrier_id.product_id and self.carrier_id.product_id.name,
                            'is_shipping': True,
                            'is_delivery': True,
                            'shipping_charge_updation': True,
                        })]
                    })

                vals = {}
                vals.update({'tracking_url':self.tracking_url})
                if self.carrier_id.id != sale_order.carrier_id.id:
                    vals.update({'carrier_id':self.carrier_id.id})
                if self.shipping_carrier_id.id != sale_order.shipping_carrier_id.id:
                    vals.update({'shipping_carrier_id':self.shipping_carrier_id.id})
                if vals:
                    sale_order.write(vals)

    def print_label(self):
        label_ids = ','.join([str(dim.attachment_id.id) for dim in self.mapped('dimension_ids') if dim.attachment_id])
        if label_ids:
            url = self.env['ir.config_parameter'].get_param('web.base.url')
            constant = 'web_label/print_label/ir.attachment/datas/datas_fname/'
            if url.endswith('/'):
                url = "%s%s%s" % (url, constant, label_ids)
            else:
                url = "%s/%s%s" % (url, constant, label_ids)
            return {
                "type": "ir.actions.act_url",
                "url": url,
                "target": "new",
                'name': "Shipment Tracking Page",
            }

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
        for picking in self:
            vals = {}
            if picking.shipping_quote_lines:
                picking.shipping_quote_lines.unlink()
            delivery_area = ('domestic', 'both')
            if (picking.partner_id.country_id and picking.partner_id.country_id.code or '') != (picking.company_id.country_id and picking.company_id.country_id.code or ''):
                delivery_area = ('international', 'both')
            data = picking._get_shipping_data()
            while isinstance(data, list):
                data = data[0]
            height = depth = width = 0
            weight = picking.weight
            for line in picking.move_lines: #row.pack_operation_product_ids
                if line.product_id and line.product_id.type == 'service':
                    continue
                if not(line.product_id.weight and line.product_id.depth and line.product_id.height and line.product_id.width):
                    raise UserError(_('Warning!\n The product %s does not have proper dimension or weight values.\nPlease consider adding them.' % line.product_id.name))
                if line.product_id and line.product_id.depth > depth:
                    depth = line.product_id.depth
                if line.product_id and line.product_id.height > height:
                    height = line.product_id.height
                if line.product_id and line.product_id.width > width:
                    width = line.product_id.width
            if picking.carrier_id and picking.carrier_id.service_code == 'STANDARD_FREIGHT':
                return True

            if picking.carrier_id:
                residential = picking.carrier_id.validate_residential_address(partner=picking.partner_id) or False
                data.update({'is_residential' : residential})
                if not picking.shipping_carrier_id:
                    picking.shipping_carrier_id = picking.carrier_id.shipping_carrier_id and picking.carrier_id.shipping_carrier_id.id
                res = self.env[picking.shipping_carrier_id.model_name].get_rate(data)
                res = len(res) and res[0]
                if picking.company_id and picking.company_id.markup_rate :
                    carrier_charge = float(res.get('rate', 0.0))
                    rate = carrier_charge + carrier_charge * (picking.company_id.markup_rate/100)
                    res.update({'rate': carrier_charge, 'markup_rate': rate})
                ShippingQuote.create({'picking_id':picking.id, 'weight':weight, 'shipping_carrier_id':picking.shipping_carrier_id.id, 'carrier_id':picking.carrier_id.id, 'rate':res.get('rate'), 'markup_rate': res.get('markup_rate')})

            else:
                try:
                    AvailableCarriers = picking.shipping_carrier_id or self.env['shipping.carrier'].search([('company_id','=', picking.company_id.id),('active','=',True)])
                    services = []
                    carrier_response = []
                    for ShippingCarrier in AvailableCarriers:
                        available_services = []
                        checked_residential = False
                        residential = False
                        for method in self.env['delivery.carrier'].search([('shipping_carrier_id', '=', ShippingCarrier.id), ('delivery_area', 'in', delivery_area),('company_id','=', picking.company_id.id)]):
                            if (method.weight > 0 and method.weight >= weight or method.weight < 0 and abs(method.weight) <= weight) or \
                            ( method.height > 0 and method.height >= height or method.height < 0 and abs(method.height) <= height) or \
                            (method.width > 0 and method.width >= width or method.width < 0 and abs(method.width) <= width) or \
                            (method.depth > 0 and method.depth >= depth or method.depth < 0 and abs(method.depth) <= depth):
                                if not checked_residential:
                                    residential = method.validate_residential_address(partner=picking.partner_id)
                                    checked_residential = True
                                available_services.append(method.service_code)
                        services.extend(available_services)
                        data.update({'available_services':available_services, 'is_residential' : residential})
                        response = self.env[ShippingCarrier.model_name].get_all_rates(data)
                        carrier_response.extend(response)
                    if not carrier_response:
                        raise UserError("Rate request error")
                    for carrier in carrier_response:
                        if carrier.get('service_type','') and carrier.get('service_type','') in services:
                            DeliveryCarrier = self.env['delivery.carrier'].search([('service_code','=',carrier.get('service_type','')),('company_id','=', picking.company_id.id)], limit=1)
                            if picking.company_id and picking.company_id.markup_rate :
                                charge = float(carrier.get('rate',0.0))
                                rate = charge + charge*(picking.company_id.markup_rate/100)
                                carrier.update({'rate': charge, 'markup_rate': rate})
                            ShippingQuote.create({'picking_id':picking.id, 'shipping_carrier_id':DeliveryCarrier.shipping_carrier_id.id, 'weight':weight, 'carrier_id':DeliveryCarrier.id, 'rate':carrier.get('rate'), 'markup_rate': carrier.get('markup_rate')})
                except Exception as e:
                    _logger.error(e)

            if weight:
                for quote in self.env['shipping.quote'].search([('weight', '!=', weight), ('picking_id', '=', picking.id)]):
                    quote.unlink()
            return vals

    # TODO check dependency and add ups
    @api.model
    def generate_shipping_for_presta(self, store=False, cust_id=False, carrier=False, ship_data=None):
        ship_data = ship_data or {}
        res = []
        weight = ship_data.get('weight', False)
        if not weight:
            return {'error_code': 'weight not specified'}
        elif not store:
            return {'error_code': 'Shop not specified'}
        elif not carrier:
            return {'error_code': 'ShippingCarrier not specified'}

        customer = self.env['res.partner'].browse(cust_id) if cust_id else False

        # receiver info
        customer_postal_code = (customer and customer.zip) or ship_data.get('customer_postal_code', False)
        customer_country_code = (customer and customer.country_id.code) or ship_data.get('customer_country_code', False)
        # cust_name = ship_data.get('customer_name', '')
        # cust_street = ship_data.get('cust_street', '')
        # cust_city = ship_data.get('cust_city', '')
        # cust_state_code = ship_data.get('cust_state_code', '')
        # cust_street2 = ship_data.get('cust_street2', '')
        # cust_phone = ship_data.get('cust_phone', '')
        # cust_email = ship_data.get('cust_email', '')

        # sender info
        zip_code = self.env['partner.zip.code'].search(
            [('zip', '=', customer_postal_code), ('company_id', '=', store.company_id.id)], limit=1)
        print(zip_code)
        if zip_code:
            ship_address = zip_code.warehouse_id and zip_code.warehouse_id.partner_id or False
        else:
            ship_address = store.cust_address
        print(ship_address)
        shipper = ship_address._get_address()
        ### Recipient
        recipient = {'zip': customer_postal_code, 'country_code': customer_country_code}

        # receipient = Address(cust_name, cust_street, cust_city, cust_state_code, customer_postal_code, customer_country_code,
        #         cust_street2, cust_phone, cust_email, cust_name)
        #
        # if carrier == 'usps':
        #     usps_info = self.pool.get('shipping.usps').get_usps_info(cr, uid, context=context)
        #     service_type_usps = vals.get('service_type_usps', False)
        #     first_class_mail_type_usps = vals.get('first_class_mail_type_usps') or ''
        #     container_usps = stockpicking.container_usps or ''
        #     size_usps = vals.get('size_usps', False)
        #     width_usps = vals.get('width_usps', False)
        #     length_usps = vals.get('length_usps', False)
        #     height_usps = vals.get('height_usps', False)
        #     girth_usps = vals.get('girth_usps', False)
        #
        #     usps = shippingservice.USPSRateRequest(usps_info, service_type_usps, first_class_mail_type_usps,
        #                                            container_usps, size_usps, str(width_usps), str(length_usps),
        #                                            str(height_usps), girth_usps, weight, shipper, receipient,
        #                                            cust_default, sys_default)
        #     usps_response = usps.send()
        #
        #     res = {'USPS': {'error_code': 'error', 'success': False}}  # usps still not tested

        if carrier and carrier.lower() == 'ups':
            data = {
                'sender': shipper,
                'recipient': recipient,
                'dropoff_type': ship_data.get('dropoff_type', False) or '03',
                'service_type': ship_data.get('service_type_ups', False) or '03',
                'packaging_type': ship_data.get('packaging_type', False) or '02',
                'weight': weight,
                'company_id': store.company_id.id
            }

            try:
                res = self.env['ups.connector'].get_rate(data)
            except Exception as e:
                return {'error_code': str(e), 'success': False}

        elif carrier and carrier.lower() == 'fedex':
            data = {
                'sender': shipper,
                'recipient': recipient,
                'dropoff_type': ship_data.get('dropoff_type', False) or 'REGULAR_PICKUP',
                'service_type': ship_data.get('service_type_fedex', False) or 'FEDEX_GROUND',
                'packaging_type': ship_data.get('packaging_type', False) or 'YOUR_PACKAGING',
                'package_detail': ship_data.get('package_detail', False) or 'INDIVIDUAL_PACKAGES',
                'physical_packaging': ship_data.get('physical_packaging', False) or 'BAG',
                'weight': weight,
                'company_id': store.company_id.id
            }

            try:
                res = self.env['fedex.connector'].get_rate(data)
            except Exception as e:
                return {'error_code': 'Rate Request Error\n%s' % e, 'success': False}

        if len(res) and res[0].get('rate', False):
            rate = res[0].get('rate', 0.0)
            markup = store and store.company_id.markup_rate or 1
            ship_rate = rate + ((rate / 100) * markup)
            res[0].update({'rate': ship_rate, 'success': True})
            return res[0]
        return res

    def action_done(self):
        # TDE FIXME: should work in batch
        self.ensure_one()
        res = super(StockPicking, self).action_done()
        if self.shipping_type == 'shipcollect':
            trackingnumber = 0
            for dimension in self.dimension_ids:
                dimension.attachment_id.write({'res_model':self._name, 'res_id':self.id})
                trackingnumber = dimension.tracking_number
            self.carrier_tracking_ref = trackingnumber
        if (not self.shipping_carrier_id or not self.carrier_id) and self.is_ship_collect:
            if self.carrier_name.lower() in ('fedex', 'ups') :
                raise UserError(_('Please select a valid Shipping type'))
            else:
                if not self.dimension_ids:
                    raise UserError(_('Warning\nPlease upload a valid Shipping label'))
                else:
                    flag = True
                    for dim in  self.dimension_ids:
                        if dim.is_used is False and dim.attachment_id:
                            flag=False
                            break
                    if flag:
                        raise UserError(_('Warning\nPlease upload a valid Shipping labels'))
        # updates the weight field with shipped weight
        delivered_weight = 0
        for line in  self.dimension_ids:
            delivered_weight += line.package_weight
        self.weight = delivered_weight
        # self.send_tracking_mail()
        if self.sale_id and not self.reshipment:
            self.sale_id.update_tracking_number(self.carrier_tracking_ref)
        # call to webservice for printing the label after fetching them
        base_url = self.env['ir.config_parameter'].get_param(key='web.base.url')
        labe_link = "/web_label/print_label/ir_attachment/store_fname/datas_fname/"
        url = ''
        atta_ids = ''
        for dimension in self.dimension_ids:
            atta_ids='%s%s,' %(atta_ids,dimension.attachment_id.id)
        url="%s%s%s" %(base_url,labe_link,atta_ids)
        if url.endswith(','):
            url = url[:-1]
        if url and atta_ids:
            return {
                'type': 'ir.actions.act_url',
                'res_model': 'ir.actions.act_url',
                'url': url ,
                'target': 'new_tab',
                'before_action':'close',
                'tag': 'reload',
            }

        return res

    def open_website_url(self):
        self.ensure_one()
        if not self.tracking_url:
            raise UserError(_("Your delivery method has no redirect on courier provider's website to track this order."))

        client_action = {
            'type': 'ir.actions.act_url',
            'name': "Shipment Tracking Page",
            'target': 'new',
            'url': self.tracking_url,
        }
        return client_action

    @api.model
    def get_dimension_data(self, dimensions):
        """
            @ dimensions List of browse recods contains dimension of a perticular picking
            {'weight':self_brw.package_weight, 'length':self_brw.length, 'breadth':self_brw.breadth, 'height':self_brw.height, 'dimension_unit':self_brw.dimension_unit}
        """
        data=[]
        for dimension in dimensions :
            vals = {}
            if isinstance(dimension, dict):
                if dimension.get('weight',0) <= 0 or dimension.get('breadth',0) <= 0 or dimension.get('length',0) <= 0 or dimension.get('height',0) <= 0:
                    raise UserError(_('Invalid Data \n Please Update Dimensions'))
                vals = {'package_weight':dimension.get('weight'), 'package_depth':dimension.get('length'), 'package_width':dimension.get('breadth'), 'package_height':dimension.get('height'), 'unit':dimension.get('dimension_unit')}
            else:
                if dimension.weight <= 0 or dimension.depth <= 0 or dimension.width <= 0 or dimension.height <= 0:
                    raise UserError(_('Invalid Data \n Please Update Dimensions'))
                vals = {'package_weight':dimension.weight, 'package_depth':dimension.depth, 'package_width':dimension.width, 'package_height':dimension.height, 'unit':dimension.dimension_unit}
            data.append(vals)
        return data

    def update_shipping_dimension(self, dimensions=[]):
        for picking in self:
            data = []
            if not self._context.get('skip_freight_check', False) and picking.carrier_id and picking.carrier_id.service_code == 'STANDARD_FREIGHT':
                if len(dimensions) == 1:
                    unused_dimension = picking.dimension_ids.filtered(lambda rec : rec.is_used==False)
                    if len(unused_dimension):
                        dimension_vals = picking.get_dimension_data(dimensions)
                        dimension_vals and unused_dimension[0].write({'is_used':True , 'unit':dimension_vals[0].get('unit'),
                                                   'package_depth':dimension_vals[0].get('package_depth'), 'package_width':dimension_vals[0].get('package_width'),
                                                   'package_height':dimension_vals[0].get('package_height'), 'package_weight':dimension_vals[0].get('package_weight')})
                        picking.write({'carrier_tracking_ref':unused_dimension[0].tracking_number, 'carrier_price':unused_dimension[0].rate})
                        picking.sale_id.update_tracking_number(unused_dimension[0].tracking_number)
                    else :
                        raise UserError(_('Label Not Found\nNo Label found for Shipping freight Shipment '))
                else:
                    raise UserError(_('Standard Freight only supports one package!\nYou can only process a single package shipment using Standard Freight BOL.'))
            else:
                if picking.carrier_id and picking.shipping_carrier_id:
                    picking.dimension_ids and picking.dimension_ids.unlink()
                    for dimension in picking.get_dimension_data(dimensions):
                        data.append((0,0,dimension))
                    if data:
                        picking.write({'dimension_ids':data})
        return True

    def button_validate(self):
        """
            overrided to prevent overprocessing of stock move and to pop up immediate transfer wizard
            if quantity_done and product_uom_qty are same for all moves to enter the picking dimensions
        """
        self.ensure_one()
        picking_type = self.picking_type_id
        no_quantities_done = all(line.qty_done == 0.0 for line in self.move_line_ids)
        no_initial_demand = all(move.product_uom_qty == 0.0 for move in self.move_lines)
        if no_initial_demand and no_quantities_done:
            raise UserError(_('You cannot validate a transfer if you have not processed any quantity.'))

        if self._get_overprocessed_stock_moves():
            raise UserError(_('Quantity to be delivered cannot be greater than quantity ordered'))

        if self.picking_type_code == 'outgoing':
            if self.move_lines and all(line.quantity_done == line.product_uom_qty for line in self.move_lines):
                if picking_type.use_create_lots or picking_type.use_existing_lots:
                    lines_to_check = self.move_line_ids
                    if not no_quantities_done:
                        lines_to_check = lines_to_check.filtered(lambda line: float_compare(line.qty_done, 0, precision_rounding=line.product_uom_id.rounding))

                    for line in lines_to_check:
                        product = line.product_id
                        if product and product.tracking != 'none':
                            if not line.lot_name and not line.lot_id:
                                raise UserError(_('You need to supply a lot/serial number for %s.') % product.display_name)
                            elif line.qty_done == 0:
                                raise UserError(_('You cannot validate a transfer if you have not processed any quantity for %s.') % product.display_name)

                view = self.env.ref('stock.view_immediate_transfer')
                wiz = self.env['stock.immediate.transfer'].create({'pick_ids': [(4, self.id)]})
                return {
                    'name': _('Immediate Transfer?'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.immediate.transfer',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'res_id': wiz.id,
                    'context': self.env.context,
                }
            else:
                if no_quantities_done:
                    quantity_todo = {}
                    quantity_done = {}
                    for move in self.mapped('move_lines'):
                        quantity_todo.setdefault(move.product_id.id, 0)
                        quantity_done.setdefault(move.product_id.id, 0)
                        quantity_todo[move.product_id.id] += move.product_uom_qty
                        quantity_done[move.product_id.id] += sum(move.move_line_ids.mapped('product_uom_qty'))
                    if any(quantity_done[x] < quantity_todo.get(x, 0) for x in quantity_done):
                        for move in self.move_lines:
                            if move.move_line_ids:
                                for move_line in move.move_line_ids:
                                    move_line.qty_done = move_line.product_uom_qty
                            else:
                                move.quantity_done = move.reserved_availability
        return super(StockPicking, self).button_validate()

    def action_assign(self):
        self.ensure_one()
        res = super(StockPicking, self).action_assign()
        if self._context.get('raise_warning', False) and self.state == 'confirmed':
            raise UserError('No stock available in %s warehouse' % self.picking_type_id.warehouse_id.name)
        return res

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        res = super(StockPicking, self).copy(default)
        if res and res.picking_type_code == 'incoming':
            res.write({'is_ship_collect':False, 'carrier_account_id':'', 'carrier_name':''})
        return res


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _get_new_picking_values(self):
        """
        Overrided to update is shipping information
        """
        #todo weight_package not included
        res = super(StockMove, self)._get_new_picking_values()
        if self.group_id and self.group_id.sale_id:
            sale_order = self.group_id.sale_id
            res.update({
                'shipping_carrier_id':sale_order.shipping_carrier_id and sale_order.shipping_carrier_id.id,
                'is_ship_collect': sale_order.is_ship_collect,
                'dropoff_type_id': sale_order.dropoff_type_id and sale_order.dropoff_type_id.id,
                'packaging_type_id': sale_order.packaging_type_id and sale_order.packaging_type_id.id,
                'package_detail_id': sale_order.package_detail_id and sale_order.package_detail_id.id,
                'physical_packaging_id': sale_order.physical_packaging_id and sale_order.physical_packaging_id.id,
            })
            if sale_order.is_ship_collect :
                res.update({'is_ship_collect':True, 'carrier_account_id':sale_order.carrier_account_id, 'carrier_name':sale_order.carrier_name})
        return res


class PickingDimensions(models.Model):
    _name = "picking.dimensions"
    _description = "Store the data of dimension"

    @api.model
    def default_get(self,fields):
        data = []
        res = super(PickingDimensions, self).default_get(fields)
        if self._context.get('picking_id', False):
            picking = False
            if isinstance(self._context.get('picking_id'), (list, int)):
                picking = self.env['stock.picking'].browse(self._context.get('picking_id'))
            else:
                picking = self._context.get('picking_id')
            if len(picking):
                for move in picking.move_lines:
                    if move.sale_line_id and (not move.sale_line_id.is_delivery or not move.sale_line_id.is_shipping):
                        data.append((0,False,{
                            'move_id':move.id,
                            'qty':move.product_qty,
                            'product_id':move.product_id.id,
                        }))
                res.update({'package_operation_ids':data})
        return res


    is_used = fields.Boolean('Used')
    package_depth = fields.Integer('Package Length')  #package_length
    package_width = fields.Integer('Package Width')  #package_breadth
    package_height = fields.Integer('Package Height')
    package_weight = fields.Float('Package Weight')
    unit = fields.Selection([('CM','CM'), ('IN','Inch')],'Dimension Unit', default='IN')
    tracking_number = fields.Char('Tracking Number')
    rate = fields.Float('Shipping Charge')
    picking_id = fields.Many2one('stock.picking','Picking_id')
    package_operation_ids = fields.One2many('stock.package.operation', 'pack_id', 'Package lines',)
    # carrier_id = fields.Many2one('delivery.carrier', string='Delivery Carrier', related='picking_id.carrier_id')
    # shipping_type = fields.Selection([('residential', 'Residential'), ('frieght', 'Standard Frieght')], string='Shipping Type', related='carrier_id.shipping_type')
    attachment_id = fields.Many2one('ir.attachment',"Attachments")
    # state = fields.Selection([('new', 'New'), ('used', 'Used')])
    #Freight fields
    freight = fields.Boolean(related='picking_id.carrier_id.freight', string="Freight")
    freight_package = fields.Many2one('shipping.physical.packaging', string='Package')
    freight_class = fields.Many2one('freight.class', string = 'Freight Class')
    freight_description = fields.Char('Description')
    no_of_packages = fields.Integer('Package Pieces')
    shipping_carrier_model = fields.Char(related='picking_id.shipping_carrier_id.model_name', string="Shipping Carrier Model")


class stock_package_operation(models.Model):
    _name = "stock.package.operation"
    _description = "Package Operation"

    move_id = fields.Many2one('stock.move', 'Product', required=True)
    product_id = fields.Many2one("product.product","Products")
    qty = fields.Float("Quantity")
    qty_to_be_packaged= fields.Float("Quantity Packaged")
    pack_id = fields.Many2one('picking.dimensions', 'Dimensions')
    freight = fields.Boolean(related='pack_id.freight', string="Freight")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
