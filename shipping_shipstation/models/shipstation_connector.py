# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class shipstation_connector(models.Model):
    _name = "shipstation.connector"
    _description = "Shipstation Connector"

    name = fields.Char(string='Name')
    company_id = fields.Many2one('res.company', 'Company')
    environment = fields.Selection([('test', 'Test Environment'), ('live', 'Live Environment')], 'Environment', default="test")
    shipstation_account_id = fields.Many2one('shipstation.accounts', string="ShipStation Account", required=True)
    shipstation_store_id = fields.Many2one('shipstation.store', string="ShipStation Store", required=True)

    def check_required_value_shipping_for_shipstation_request(self, orders, warehouse_address, shipping_address):
        if not warehouse_address:
            return _("Configure warehouse from Shipstation warehouse menu.")
        for order in orders:
            if not order.order_line:
                return _("You don't have any item to ship.")
            else:
                order_lines_without_weight = order.order_line.filtered(
                    lambda line_item: not line_item.product_id.type in ['service', 'digital'] and not line_item.product_id.weight and not line_item.is_delivery)
                for order_line in order_lines_without_weight:
                    return _("Please define weight in product : \n %s") % order_line.product_id.name

            if warehouse_address and not warehouse_address.zip:
                return (_("There are some missing the values of the Warehouse address. \n Missing field(s) : Zip / Postal Code"))

            missing_value = self.check_required_value_in_shipstation_address(shipping_address)
            if missing_value:
                fields = ", ".join(missing_value)
                return (_("There are some missing the values of the Customer address. \n Missing field(s) : %s  ") % fields)

        if not self.shipstation_store_id:
            return _("Shipstation Store isn't defined delivery method.")
        return False

    def get_rate(self, data):
        sender = data.get('sender', {})
        recipient = data.get('recipient', {})
        try:
            rate_data = {
                "carrierCode": data.get('shipstation_carrier_id') and data.get('shipstation_carrier_id').code,
                "serviceCode": data.get('shipstation_service_id') and data.get('shipstation_service_id').code or None,
                "fromPostalCode": sender.get('zip', ''),
                "toState": recipient.get('state_code', ''),
                "toCountry": recipient.get('country_code', ''),
                "toPostalCode": recipient.get('zip', ''),
                "toCity": recipient.get('city', ''),
                "weight": {
                    "value": data.get('weight', 0.0),
                    "units": 'pounds',
                },
                "residential": data.get('is_residential', False)
            }
            response = data.get('shipstation_account_id')._send_request('shipments/getrates', rate_data, method="POST")
        except Exception as e:
            return [{
                'success': False,
                'price': 0.0,
                'error_message': e,
                'warning_message': False,
            }]
        if not response:
            return [{
                'success': False,
                'price': 0.0,
                'error_message': "Rate Not Found!",
                'warning_message': False,
            }]
        res = []
        for resp in response:
            shipping_charge = resp.get('shipmentCost', 0.0) + resp.get('otherCost', 0.0)
            res.append({
                'rate' : float(shipping_charge),
                'service_type': resp.get('serviceCode'),
                'service_name': resp.get('serviceName'),
            })
        return res

    @api.model
    def get_connector(self, company_id=None, domain=[]):
        domain = []
        if company_id:
            domain.append(('company_id', '=', company_id))
        res = self.search(domain, limit=1)
        if not res:
            raise UserError(_("Error \n There is no Active Shipstaion configuration"))
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
