# -*- coding: utf-8 -*-

import logging

from odoo import http
from odoo.http import request


class Shipstation(http.Controller):
    @http.route("/shipstation/get_dashboard_data", type="json", auth="user")
    def fetch_shipstation_data(self):
        results = {}
        dashboard_data = dict(carrier_count=0)
        carrier = request.env['shipstation.carrier'].search([])
        dashboard_data['carrier_count'] = len(carrier)
        return dashboard_data

    @http.route("/shipstation/webhook/notification/<int:account>", type="json", auth="public")
    def shipstation_webhook_notification(self, account=None, **kwargs):
        data = request.jsonrequest and request.jsonrequest or {}
        logging.error(data)
        order_obj = request.env['sale.order'].sudo()
        ShipstationOrder = request.env['shipstation.order'].sudo()
        if data.get('resource_type') == 'SHIP_NOTIFY':
            logging.error('Ship Notify')
            order_obj.update_order_from_shipstation_webhook(data.get('resource_url'), account)
            return 'SUCCESS'
        if data.get('resource_type') == 'ORDER_NOTIFY':
            logging.error('ORDER_NOTIFY')
            ShipstationOrder.import_order_from_webhook_notification(data.get('resource_url'), account)
            return 'SUCCESS'
        return 'FAILURE'


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:


#http://167.71.224.12:10050/shipstation/webhook/notification/

#{"shipments":[{"shipmentId":84423296,"orderId":147109884,"orderKey":"ec4d05f7bbcf45a1b7ec993d94afd5a5","userId":"c284f626-4d3f-4f9e-963a-429c6125bd86","customerEmail":"testnoemail5@store.lowes.comtest","orderNumber":"SO40322","createDate":"2020-10-28T00:11:27.0270000","shipDate":"2020-10-28","shipmentCost":3.33,"insuranceCost":0.0,"trackingNumber":"9449011899564934265374","isReturnLabel":false,"batchNumber":null,"carrierCode":"stamps_com","serviceCode":"usps_media_mail","packageCode":"package","confirmation":null,"warehouseId":511799,"voided":true,"voidDate":"2020-10-28T00:11:56.6470000","marketplaceNotified":false,"notifyErrorMessage":null,"shipTo":{"name":"American Designs, Inc","company":null,"street1":"4147 W OGDEN AVE","street2":"NULL","street3":null,"city":"CHICAGO","state":"IL","postalCode":"60623-2877","country":"US","phone":"773-592-1291","residential":null,"addressVerified":null},"weight":{"value":32.00,"units":"ounces","WeightUnits":1},"dimensions":{"units":"inches","length":3.00,"width":2.00,"height":4.00},"insuranceOptions":{"provider":null,"insureShipment":false,"insuredValue":0.0},"advancedOptions":{"billToParty":"4","billToAccount":null,"billToPostalCode":null,"billToCountryCode":null,"storeId":357369},"shipmentItems":null,"labelData":null,"formData":null}],"total":1,"page":1,"pages":0}
