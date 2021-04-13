# -*- coding: utf-8 -*-

import time
import json
import logging
import requests
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from requests.auth import HTTPBasicAuth
from odoo.exceptions import ValidationError, UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    use_shipstation = fields.Boolean(string='Use Shipstation', copy=False)
    shipstation_order_id = fields.Char('Shipstation Order ID', readonly=True, copy=False, help="The system generated identifier for the order")
    shipstation_account_id = fields.Many2one("shipstation.accounts", "Shipstation Account", ondelete='restrict', copy=False, help="Account in which order exist")
    shipstation_store_id = fields.Many2one('shipstation.store', "Store", ondelete='restrict', copy=False)
    prepared_for_shipstation = fields.Boolean('Prepared for Shipstation', copy=False)
    shipstation_carrier_id = fields.Many2one('shipstation.carrier','Shipstation Carrier', copy=False)
    shipstation_service_id = fields.Many2one('shipstation.service','Shipstation Service', copy=False)
    shipstation_package_id = fields.Many2one('shipstation.packages','Package', copy=False)
    shipped_from_shipstation = fields.Boolean(string='Shipped From Shipstation', copy=False)
    shipstation_order_key = fields.Char(string='Shipstation Order Key', copy=False)
    sscc_id = fields.Char(string='SSCC ID', copy=False)

    @api.onchange('use_shipstation')
    def onchange_use_shipstation(self):
        if self.use_shipstation:
            self.shipping_carrier_id = False
            return {'domain':{'shipping_carrier_id':[('is_shipstation_carrier','=',True)]}}
        else:
            self.shipping_carrier_id = False
            return {'domain':{'shipping_carrier_id':[('is_shipstation_carrier','=',False)]}}

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

    def _generate_shipping_data(self):
        res = super(SaleOrder, self)._generate_shipping_data()
        if self.shipstation_carrier_id and self.use_shipstation:
            res.update({
                'shipstation_carrier_id' : self.shipstation_carrier_id,
                'shipstation_service_id' : self.shipstation_service_id,
                'shipstation_store_id' : self.shipstation_store_id,
                'shipstation_account_id' : self.shipstation_account_id,
                'shipstation_package_id': self.shipstation_package_id,
            })
        return res

    def _update_shipping_data(self, shipping_carrier=None):
        res = super(SaleOrder, self)._update_shipping_data(shipping_carrier)
        if shipping_carrier:
            res.update({
                'shipstation_carrier_id': shipping_carrier.shipstation_carrier_id,
                'shipstation_account_id': shipping_carrier.shipstation_carrier_id.account_id,
            })
        return res

    def import_orders(self, account=False):
        orders = []
        if not account:
            raise UserError("Shipstation Account not defined to import orders")
        request_url = 'orders?pageSize=500&orderStatus=awaiting_shipment'
        if account.order_imported_as_on_date:
            order_date_start = account.order_imported_as_on_date - timedelta(days=3)
            order_date_start = order_date_start.strftime("%Y-%m-%d %H:%M:%S")
            request_url = request_url + '&orderDateStart=%s' % order_date_start
        response = account._send_request(request_url, {}, method='GET')

        if isinstance(response.get('orders'), dict):
            orders = [response.get('orders')]
        orders += response.get('orders')
        total_pages = response.get('pages')
        page = 2
        while total_pages:
            response = account._send_request(request_url + '&page=%s' % page, {}, method='GET')
            order_data = response.get('orders')
            if isinstance(order_data, dict):
                orders += [order_data]
            orders += order_data
            total_pages -= 1
            page += 1

        if orders:
            self.create_shipstation_order(orders, account)
            account.order_imported_as_on_date = datetime.now()
        return orders

    def import_order_from_webhook_notification(self, resource_url, account):
        if not account:
            return True
        account = self.env['shipstation.accounts'].browse(account)
        headers = {
            'Content-Type': 'application/json'
        }
        orders = []
        try:
            req = requests.request('GET', resource_url, auth=HTTPBasicAuth(account.api_key, account.api_secret), headers=headers)
            req.raise_for_status()
            response_text = req.text
        except requests.HTTPError as e:
            response = json.loads(req.text)
            error_msg = ''
            if response.get('ExceptionMessage', False):
                error_msg = response.get('ExceptionMessage', False)
            raise ValidationError(_("Error From ShipStation Webhook: %s" % error_msg or req.text))
        response = json.loads(response_text)
        order_data = response.get('orders')
        if isinstance(order_data, dict):
            orders += [order_data]
        orders += order_data
        if orders:
            self.create_shipstation_order(orders, account)
        return orders

    def update_order_from_shipstation_webhook(self, resource_url, account):
        if not account:
            return True
        account = self.env['shipstation.accounts'].browse(account)
        headers = {
            'Content-Type': 'application/json'
        }
        shipments = []
        try:
            req = requests.request('GET', resource_url, auth=HTTPBasicAuth(account.api_key, account.api_secret), headers=headers)
            req.raise_for_status()
            response_text = req.text
        except requests.HTTPError as e:
            response = json.loads(req.text)
            error_msg = ''
            if response.get('ExceptionMessage', False):
                error_msg = response.get('ExceptionMessage', False)
            raise ValidationError(_("Error From ShipStation Webhook: %s" % error_msg or req.text))
        response = json.loads(response_text)
        logging.error('-------------------- RESPONSE --------------------')
        logging.error(response)
        shipment_data = response.get('shipments')
        if isinstance(shipment_data, dict):
            shipments += [shipment_data]
        shipments += shipment_data
        if shipments:
            self.update_shipstation_order(shipments, account)
        return shipments

    def check_for_product_exist(self, ss_order_lines, account):
        """
        To check the sku is present or not in odoo
        """
        # MerchantSku = self.env['merchant.sku']
        ProductObj = self.env['product.product']
        ss_product_obj = self.env['shipstation.product']
        all_product_exist = True
        for order_line in ss_order_lines:
            name = order_line.get('name', False)
            product_id = order_line.get('productId', False)
            sku = order_line.get('sku', False)
            if not sku:
                all_product_exist = False
                break
            ss_product = ss_product_obj.search(['|', ('shipstation_id', '=', product_id), ('sku', '=', sku), ('account_id', '=', account.id)])
            if ss_product:
                continue
            odoo_product = ProductObj.search([('default_code', '=', sku)], limit=1)
            if odoo_product:
                ss_product_obj.create({
                    'name': name,
                    'product_id': odoo_product.id,
                    'shipstation_id': product_id,
                    'sku': sku,
                    'account_id': account.id
                })
            # product = MerchantSku.search([('sku', '=', sku)], limit=1)
            # if not product:
            #     all_product_exist = False
            #     break
        return all_product_exist

    def prepare_sales_order_vals(self, order, account):
        """
        To prepare sale order vals
        """
        if not order:
            return False

        warehouse = False
        partner_id = False
        shipping_partner_id = False
        advance_option_dict = order.get('advancedOptions', False)
        partner_code = advance_option_dict.get('customField1')
        shipping_address_info = order.get('shipTo')
        ordervals = {
            'name': order.get('orderNumber'),
            'shipstation_order_key' :order.get('orderKey'),
            'shipstation_order_id': order.get('orderId', False),
        }

        # map shipstaion store
        if advance_option_dict.get('storeId'):
            store_id = self.env['shipstation.store'].search([('store_id', '=', advance_option_dict.get('storeId')), ('account_id', '=', account.id)])
        else:
            self.env['shipstation.log'].register_log(
                res_model='sale.order',
                shipstation_id=order.get('orderId', False) or 0,
                operation='import',
                message='Missing Shipstation Store',
                request=order,
            )
            return False

        # map shipstation warehouse
        ShipstationWarehouse = self.env['shipstation.warehouse'].search([
            ('shipstation_warehouse_id', '=', advance_option_dict.get('warehouseId')), ('account_id', '=', account.id)])
        if ShipstationWarehouse and ShipstationWarehouse.warehouse_id:
            warehouse = ShipstationWarehouse.warehouse_id
        else:
            warehouse = account.warehouse_id

        company_id = warehouse and warehouse.company_id or account.company_id

        # map partner
        if partner_code:
            partner_id = self.env['res.partner'].search([('shipstation_partner_code', '=', partner_code),('company_id', '=', company_id.id)], limit=1)

        if not partner_code or not partner_id:
            self.env['shipstation.log'].register_log(
                res_model='sale.order',
                shipstation_id=order.get('orderId', False) or 0,
                operation='import',
                message='Missing Partner Code',
                request=order,
            )
            return False

        if shipping_address_info:
            shipping_address_info.update({'parent_id': partner_id and partner_id.id})
            shipping_partner_id = self.env['res.partner'].ss_find_existing_or_create_partner(shipping_address_info, company=company_id, partner_type='delivery')

        if not shipping_address_info or not shipping_partner_id:
            self.env['shipstation.log'].register_log(
                res_model='sale.order',
                shipstation_id=order.get('orderId', False) or 0,
                operation='import',
                message='Missing Shipping parnter Info',
                request=order,
            )
            return False

        shipstation_service_id = self.env['shipstation.service'].search([('code', '=', order.get('serviceCode', False)), ('company_id', '=', company_id.id)])
        delivery_method = self.env['delivery.carrier'].search([
            ('delivery_type', '=', 'shipstation_ts'),
            ('shipstation_account_id', '=', account.id),
            ('shipstation_store_id', '=', store_id.id),
            ('shipstation_service_id', '=', shipstation_service_id.id),
        ], limit=1)

        shipping_carrier_id = False
        if shipstation_service_id:
            shipping_carrier_id = self.env['shipping.carrier'].search([
                ('shipstation_carrier_id','=',shipstation_service_id.carrier_id.id),('company_id','=',account.company_id.id)], limit=1)

        order_date = order.get('orderDate', False)[:19]
        order_date = time.strptime(order_date, "%Y-%m-%dT%H:%M:%S")
        order_date = time.strftime("%Y-%m-%d %H:%M:%S", order_date)
        ordervals.update({
            'use_shipstation':True,
            'shipstation_account_id': account and account.id or False,
            'shipstation_store_id': store_id and store_id.id,
            'company_id': company_id and company_id.id,
            'partner_id': partner_id and partner_id.id,
            'partner_invoice_id': partner_id and partner_id.id,
            'partner_shipping_id': shipping_partner_id and shipping_partner_id.id,
            'warehouse_id': warehouse and warehouse.id,
            'shipstation_service_id': shipstation_service_id and shipstation_service_id.id,
            'shipstation_carrier_id' : shipstation_service_id and shipstation_service_id.carrier_id and shipstation_service_id.carrier_id.id or False,
            'date_order': order_date,
            'pricelist_id': account.pricelist_id.id,
            'carrier_id': delivery_method and delivery_method.id or False,
        })
        return ordervals

    def prepare_sales_order_line_vals(self, ss_order_lines, account):
        # MerchantSku = self.env['merchant.sku']
        MerchantSku = self.env['shipstation.product']
        order_val_list = []
        for order_line in ss_order_lines:
            sku = order_line.get('sku', False)
            product = MerchantSku.search([('sku', '=', sku)], limit=1)
            order_line_vals = {
                'order_id': self.id,
                'product_id': product and product.product_id.id or False,
                'name': order_line.get('name', False),
                'product_uom_qty': order_line.get('quantity', False),
                'price_unit': order_line.get('unitPrice', False),
                'lineItemKey': order_line.get('lineItemKey', ''),
                'orderItemId': order_line.get('orderItemId', ''),
            }
            order_val_list.append(order_line_vals)
        return order_val_list

    def create_shipstation_order(self, orders, account):
        """
        To create order from shipstation
        """
        res_partner_obj = self.env['res.partner']
        sale_line_obj = self.env['sale.order.line']
        for order in orders:
            ss_order_id = order.get('orderId', False)
            ss_order_lines = order.get('items')
            advance_option_dict = order.get('advancedOptions', False)
            ShipstationStore = False
            if advance_option_dict and advance_option_dict.get('storeId', False):
                ShipstationStore = advance_option_dict.get('storeId')
            if not ss_order_id or not ss_order_lines:
                self.env['shipstation.log'].register_log(
                    res_model='sale.order',
                    shipstation_id=ss_order_id or 0,
                    operation='import',
                    message='Insufficient Order Details',
                    request=order,
                )
                continue
            existing_order = self.search([('shipstation_order_id', '=', ss_order_id)])
            picking = self.env['stock.picking'].search([('shipstation_order_id', '=', ss_order_id)])
            if existing_order or picking:
                continue

            all_product_exist = self.check_for_product_exist(ss_order_lines, account)
            if not all_product_exist:
                self.env['shipstation.log'].register_log(
                    res_model='sale.order',
                    shipstation_id=order.get('orderId', False) or 0,
                    operation='import',
                    message='Order Line Item not found',
                    request=order,
                )
                continue
            order_vals = self.prepare_sales_order_vals(order, account)
            if order_vals:
                try:
                    order_id = self.create(order_vals)
                    order_line_vals = order_id.prepare_sales_order_line_vals(ss_order_lines, account)
                    for line in order_line_vals:
                        sale_line_obj.create(line)
                    # if order.get('shippingAmount') and account.shipping_product_id:
                    #     order_line = {
                    #         'order_id': order_id.id,
                    #         'product_id': account.shipping_product_id.id,
                    #     }
                    #     new_order_line = sale_line_obj.new(order_line)
                    #     new_order_line.product_id_change()
                    #     order_line = sale_line_obj._convert_to_write(
                    #         {name: new_order_line[name] for name in new_order_line._cache})
                    #     order_line.update({
                    #         'sequence': 100,
                    #         'price_unit': order.get('shippingAmount'),
                    #         'is_delivery': True
                    #     })
                    #     sale_line_obj.create(order_line)
                except Exception as e:
                    logging.error(e)
                    self.env['shipstation.log'].register_log(
                        res_model='sale.order',
                        res_id=0,
                        shipstation_id=ss_order_id or 0,
                        operation='import',
                        message=e,
                        request=order,
                    )
        return True

    def update_shipstation_order(self, shipments, account):
        logging.error('------------------- SHIPMENTS -------------------')
        logging.error(shipments)
        shipping_product = self.env.user.company_id.shipping_cost_product_id
        carriers = {carrier.code: carrier.id for carrier in self.env['shipstation.carrier'].search([])}
        services = {service.code: service.id for service in self.env['shipstation.service'].search([])}
        stores = {store.store_id: store.id for store in self.env['shipstation.store'].search([])}
        for shipment in shipments:
            try:
                orderId = shipment.get('orderId')
                if orderId:
                    SaleOrder = self.search([('shipstation_order_id','=', orderId)], limit=1)
                    shipping_line = False
                    if not SaleOrder:
                        order_num = shipment.get('orderNumber', '')
                        SaleOrder = self.search([('chnl_adv_order_id', '=', order_num), ('state', '!=', 'cancel')], limit=1)
                        if shipping_product:
                            shipping_line = SaleOrder.order_line.filtered(lambda r: r.product_id.id == shipping_product.id)
                    if shipment.get('trackingNumber') and SaleOrder:
                        vals = {
                            'tracking_reference': shipment.get('trackingNumber', ''),
                            'shipped_from_shipstation': True,
                        }
                        if not SaleOrder.use_shipstation:
                            vals.update({
                                'shipstation_account_id' : account.id,
                                'shipstation_carrier_id' : carriers.get(shipment.get('carrierCode', 'none'), False),
                                'shipstation_service_id' : services.get(shipment.get('serviceCode', 'none'), False),
                                'shipstation_store_id' : stores.get(shipment.get('advancedOptions', {}).get('storeId', 'none'), False),
                                'shipstation_order_id': shipment.get('orderId', ''),
                                'shipstation_order_key': shipment.get('orderKey', ''),
                            })

                        SaleOrder.write(vals)

                        if shipping_line:
                            shipping_line.write({'purchase_price': shipment.get('shipmentCost', 0.0)})

                        if SaleOrder.picking_ids:
                            for picking in SaleOrder.picking_ids:
                                picking.write({
                                    'carrier_tracking_ref': shipment.get('trackingNumber', ''),
                                    'shipped_from_shipstation': True,
                                })
                                if picking.state == 'assigned':
                                    for move in picking.move_lines:
                                        for move_line in move.move_line_ids:
                                            move_line.qty_done = move_line.product_uom_qty
                                    picking.action_done()
                    else:
                        self.env['shipstation.log'].register_log(
                            res_model='sale.order',
                            res_id=0,
                            shipstation_id=orderId or 0,
                            operation='import',
                            message='Order Update failed',
                            request=shipment,
                        )
                else:
                    self.env['shipstation.log'].register_log(
                        res_model='sale.order',
                        res_id=0,
                        shipstation_id=0,
                        operation='import',
                        message='Missing orderId : Order Update failed',
                        request=shipment,
                    )
            except Exception as e:
                logging.error(e)
                self.env['shipstation.log'].register_log(
                    res_model='sale.order',
                    res_id=0,
                    shipstation_id=shipment.get('orderId') or 0,
                    operation='import',
                    message=e,
                    request=shipment,
                )
        return True


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    lineItemKey = fields.Char(string='lineItemKey')
    orderItemId = fields.Char(string='orderItemId')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

