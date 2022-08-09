# -*- coding: utf-8 -*-

import json
import threading

from odoo import api, fields, models, registry, _
import logging


class StockPicking(models.Model):
    _inherit = "stock.picking"

    shipstation_order_id = fields.Char('Shipstation Order ID', copy=False)
    is_shipstation_order = fields.Boolean(string="Is ShipStation Order")
    use_shipstation = fields.Boolean(string="Use Shipstation")
    shipstation_exported = fields.Boolean(string="Exported to Shipstation", copy=False)
    shipstation_carrier_id = fields.Many2one('shipstation.carrier', string="ShipStation Carrier")
    shipstation_service_id = fields.Many2one('shipstation.service', string="ShipStation Service")
    shipstation_package_id = fields.Many2one('shipstation.packages','Package', copy=False)
    shipstation_store_id = fields.Many2one('shipstation.store', string="ShipStation Store")
    shipstation_shipment_id = fields.Char(string="ShipStation Shipment ID", copy=False)
    shipped_from_shipstation = fields.Boolean(string="Shipped From Shipstation", copy=False)
    shipstation_order_key = fields.Char(string="Shipstation Order Key", copy=False)
    sscc_id = fields.Char(string="SSCC ID", copy=False)

    @api.onchange('shipping_carrier_id')
    def onchange_shipping_carrier_id_ss(self):
        for order in self:
            if order.shipping_carrier_id and order.shipping_carrier_id.shipstation_carrier_id:
                order.shipstation_carrier_id = order.shipping_carrier_id.shipstation_carrier_id.id
            else:
                order.shipstation_carrier_id = False

    @api.onchange('carrier_id')
    def onchange_carrier_id_ss(self):
        if self.carrier_id:
            self.shipstation_store_id = self.carrier_id.shipstation_store_id.id
            self.shipstation_package_id = self.carrier_id.shipstation_package_id.id
            if self.carrier_id.shipstation_service_id:
                self.shipstation_service_id = self.carrier_id.shipstation_service_id.id
            if self.carrier_id.shipstation_carrier_id:
                self.shipstation_account_id = self.carrier_id.shipstation_carrier_id.account_id.id
        else:
            self.shipstation_store_id = False
            self.shipstation_service_id = False
            self.shipstation_account_id = False
            self.shipstation_package_id = False

    def visit_shipstation(self):
        """
        method generates a tracking url for shipstation
        https://ship12.shipstation.com/orders/awaiting-shipment/order/6f047013-9216-59d8-af8f-5ab7eca27895/active/177849058
        https://ship12.shipstation.com/orders/shipped/order/f2ebb6e4-6663-58dd-87e4-e423ac0d6d9e/active/155400748
        https://ship12.shipstation.com/orders/awaiting-shipment/store/deeb6a77-26a9-4efa-bea4-48bf3cec2ecb/order/aba9a18d-afb6-5835-87b1-471ef7d5d9d6/active/14533445
        """
        self.ensure_one()
        orders = []
        order_status = ''
        link = ''
        if self.shipstation_order_key and self.shipstation_order_id:
            try:
                if self.shipstation_store_id and self.shipstation_store_id.account_id:
                    base_url = self.shipstation_store_id.account_id.endpoint_url or "https://ship12.shipstation.com/orders/"
                    request_url = "orders/%s" %(self.shipstation_order_id)
                    response = self.shipstation_store_id.account_id._send_request(request_url, {}, method='GET')
                    order_status = response.get('orderStatus')
                    if order_status:
                        link = "%s%s/order/%s/active/%s" %(base_url, order_status, self.shipstation_order_key, self.shipstation_order_id )
            except Exception:
                pass

        if len(link):
            return {
                'type': 'ir.actions.act_url',
                'name': "Shipstation Tracking Page",
                'target': 'new_tab',
                'url': link,
            }
        return True

    def _get_shipping_data(self, quote=None):
        res = super(StockPicking, self)._get_shipping_data(quote=quote)
        if self.shipstation_carrier_id and self.use_shipstation:
            res.update({
                'picking' : self,
                'shipstation_carrier_id': self.shipstation_carrier_id,
                'shipstation_service_id': self.shipstation_service_id,
                'shipstation_store_id': self.shipstation_store_id,
                'shipstation_package_id': self.shipstation_package_id,
                'shipstation_account_id' : self.shipstation_carrier_id.account_id,
            })
        return res

    def prepare_shipstation_data(self, operation='create'):
        logging.info("^^^^^^^^^^^inside prepare_shipstation_data^^^^^^^^^")

        values = {}
        for picking in self:
            item_list = []
            for move in picking.move_line_ids:
                qty = int(move.product_uom_qty)
                if operation == 'update':
                    qty = int(move.qty_done)
                item_list.append({
                    "sku": move.product_id and move.product_id.default_code or '',
                    "name": move.product_id and move.product_id.name or '',
                    "quantity": qty ,
                    "unitPrice": move.move_id.sale_line_id.price_unit,
                    "taxAmount": 0.0,
                })

            sale_order = picking.sale_id
            if item_list:
                items_json = json.dumps(item_list)
                values = {
                    "orderNumber": sale_order.name,
                    "orderDate": sale_order.date_order.strftime("%Y-%m-%d %H:%M:%S"),
                    "orderStatus": "awaiting_shipment",
                    "customerUsername": picking.partner_id.name,
                    "customerEmail": picking.partner_id.email,
                    "carrierCode": picking.shipstation_carrier_id.code,
                    "serviceCode": picking.shipstation_service_id.code,
                    'packageCode': picking.shipstation_package_id.code or None,
                    "weight": {
                        "value": picking.weight,
                        "units": "pounds",
                    },
                    "billTo": {
                        "name": picking.partner_id.name,
                        "street1": picking.partner_id.street,
                        "street2": picking.partner_id.street2 or "null",
                        "city": picking.partner_id.city,
                        "state": picking.partner_id.state_id.code,
                        "postalCode": picking.partner_id.zip,
                        "country": picking.partner_id.country_id.code,
                        "phone": picking.partner_id.phone,
                    },
                    "shipTo": {
                        "name": picking.partner_id.name,
                        "street1": picking.partner_id.street,
                        "street2": picking.partner_id.street2 or "null",
                        "city": picking.partner_id.city,
                        "state": picking.partner_id.state_id.code,
                        "postalCode": picking.partner_id.zip,
                        "country": picking.partner_id.country_id.code,
                        "phone": picking.partner_id.phone,
                    },
                    "items": item_list,
                    "advancedOptions" : {
                        "storeId": picking.shipstation_store_id.store_id,
                        'source': 'Odoo Sales',
                    },
                }

                if picking.backorder_id and picking.backorder_id.shipstation_order_id:
                    values.update({"advancedOptions" : {
                        'mergedOrSplit': True,
                        'storeId' : picking.shipstation_store_id.store_id,
                        'parentId': int(picking.backorder_id.shipstation_order_id),
                    }})

                if operation == 'update':
                    if picking.shipstation_order_key:
                        values.update({'orderKey': picking.shipstation_order_key})
        logging.info("^^^^^^^^^^^inside prepare_shipstation_data before return^^^^^^^^^")
        return values

    # def write(self, vals):
    #     res = super(StockPicking, self).write(vals)
    #     for picking in self:
    #         if vals.get('state') == 'assigned' and picking.sale_id and not picking.quote_id:
    #             if picking.shipstation_carrier_id and not picking.shipstation_order_id:
    #                 shipment_values = picking.prepare_shipstation_data(operation='create')
    #                 data = {
    #                     'shipstation_carrier_id':self.shipstation_carrier_id,
    #                     'shipstation_service_id':self.shipstation_service_id,
    #                     'shipstation_store_id':self.shipstation_store_id,
    #                 }
    #                 response = picking.shipstation_store_id.shipstation_account_id._send_request('orders/createorder', shipment_values, method="POST")

    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        for picking in self:
            # if picking.sale_id and picking.sale_id.use_shipstation and not picking.quote_id:
            if picking.sale_id and picking.sale_id.use_shipstation:
                if picking.state == 'assigned' and picking.shipstation_carrier_id and not picking.shipstation_order_id:
                    shipment_values = picking.prepare_shipstation_data(operation='create')
                    data = {
                        'shipstation_carrier_id': self.shipstation_carrier_id,
                        'shipstation_service_id': self.shipstation_service_id,
                        'shipstation_store_id': self.shipstation_store_id,
                    }
                    response = picking.shipstation_store_id.account_id._send_request('orders/createorder', shipment_values, method="POST")
                    if response.get('orderId'):
                        picking.write({
                            'shipstation_order_id': response.get('orderId'),
                            'shipstation_exported': True,
                            'shipstation_order_key': response.get('orderKey'),
                        })
                        picking.sale_id.write({
                            'shipstation_order_id': response.get('orderId'),
                            'shipstation_order_key': response.get('orderKey'),
                        })
                    else:
                        msg = 'Export Failed for sale order %s (%s), picking %s (%s)' %(picking.sale_id.name, picking.sale_id.id, picking.name, picking.id)
                        self.env['shipstation.log'].register_log(
                            res_model='sale.order',
                            res_id=picking.sale_id.id,
                            shipstation_id=0,
                            operation='export',
                            message=msg,
                            request=shipment_values,
                        )
        return res

    def mark_as_shipped(self):
        for picking in self:
            data = {
                'orderId': picking.shipstation_order_id,
                'carrierCode': picking.shipstation_carrier_id.code,
                'trackingNumber': picking.carrier_tracking_ref,
            }
            req = picking.shipstation_store_id.account_id._send_request('orders/markasshipped', data, method="POST")
        return True

    def send_to_shipper(self):
        self.ensure_one()
        if self.shipped_from_shipstation or self.is_shipstation_order or self.carrier_id.delivery_type == 'shipstation_ts':
            return True
        else:
            return super(StockPicking, self).send_to_shipper()

    def restore_from_hold(self):
        ShipstationOrder = self.env['shipstation.order'].sudo()
        for picking in self:
            data = {}
            shipstation_account = False
            sale_order = picking.sale_id
            if sale_order.shipstation_order_id:
                data['orderId'] = sale_order.shipstation_order_id
                shipstation_account = sale_order.shipstation_account_id
            elif sale_order.chnl_adv_order_id:
                shipping_order = ShipstationOrder.search([('order_number', '=', sale_order.chnl_adv_order_id)], limit=1)
                if shipping_order:
                    data['orderId'] = shipping_order.order_id
                    shipstation_account = shipping_order.account_id
            if shipstation_account and data:
                logging.info("#################before new cr################3")
                # res = shipstation_account._send_request('orders/restorefromhold', data, method="POST")
                new_cr = registry(self.env.cr.dbname).cursor()
                logging.info("#################after new cr################3")

                with api.Environment.manage():
                    new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                    shipstation_account = shipstation_account.with_env(new_env)
                    thread = threading.Thread(target=shipstation_account._send_request, args=('orders/restorefromhold', data, 'POST'))
                    thread.daemon = True
                    logging.info("#################before thread################3")

                    thread.start()
                    logging.info("#################after thread################3")

        return True

    def action_done(self):
        self.ensure_one()
        logging.info("^^^^^^^^^^^action_done start^^^^^^^^^^")
        res = super(StockPicking, self).action_done()
        logging.info("^^^^^^^^^^^action_done after super^^^^^^^^^")
        if self.state == 'done' and self.picking_type_id.code == 'outgoing':
            if (self.shipstation_order_id and self.is_shipstation_order) or (self.use_shipstation and self.is_shipstation_order):
                shipment_values = self.prepare_shipstation_data(operation='update')
                logging.info("^^^^^^^^^^^action_done after shipment_values^^^^^^^^^")

                response = self.shipstation_store_id.account_id._send_request('orders/createorder', shipment_values, method="POST")
                logging.info("^^^^^^^^^^^action_done after response^^^^^^^^^")

                if response.get('orderId'):
                    self.write({
                        'shipstation_order_id': response.get('orderId'),
                        'shipstation_exported': True,
                        'shipstation_order_key': response.get('orderKey'),
                    })
                    self.sale_id.write({
                        'shipstation_order_id': response.get('orderId'),
                        'shipstation_order_key': response.get('orderKey'),
                    })
            logging.info("^^^^^^^^^^^action_done before restore_from_hold^^^^^^^^^")
            self.restore_from_hold()
            logging.info("^^^^^^^^^^^action_done after restore_from_hold^^^^^^^^^")

        return res


class StockMove(models.Model):
    _inherit = "stock.move"

    def _get_new_picking_values(self):
        """
        Overrided to update is shipstation information
        """
        #TODO: weight_package not included
        res = super(StockMove, self)._get_new_picking_values()
        if self.group_id and self.group_id.sale_id:
            sale_order = self.group_id.sale_id
            if self.group_id.sale_id.use_shipstation:
                res.update({
                    'sscc_id' : sale_order.sscc_id,
                    'is_shipstation_order' : True,
                    'shipstation_order_id' : sale_order.shipstation_order_id,
                    'shipstation_store_id' : sale_order.shipstation_store_id.id,
                    'shipstation_order_key' : sale_order.shipstation_order_key,
                    'shipstation_carrier_id' : sale_order.shipstation_carrier_id.id,
                    'shipstation_service_id' : sale_order.shipstation_service_id.id,
                    'shipstation_package_id' : sale_order.shipstation_package_id.id,
                })
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
