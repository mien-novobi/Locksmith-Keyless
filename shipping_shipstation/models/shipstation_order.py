# -*- coding: utf-8 -*-

import logging
import requests
from requests.auth import HTTPBasicAuth
from dateutil import parser

from odoo import api, fields, models


class ShipstaionOrder(models.Model):
    _name = "shipstation.order"
    _description = "Shipstaion Order"
    _rec_name = "order_number"

    order_id = fields.Char(string="Order ID")
    order_key = fields.Char(string="Order Key")
    order_date = fields.Datetime(string="Order Date")
    order_number = fields.Char(string="Order Number")
    account_id = fields.Many2one('shipstation.accounts', string="ShipStation Account")

    def update_status(self):
        self.ensure_one()
        sale_order = self.env['sale.order'].search([('chnl_adv_order_id', '=', self.order_number)], limit=1)
        if sale_order and not sale_order.shipstation_order_id:
            if sale_order.picking_ids.filtered(lambda r: r.state == 'done' and r.picking_type_id.code == 'outgoing'):
                data = {'orderId': self.order_id}
                res = self.account_id._send_request('orders/restorefromhold', data, method="POST")
        return True

    @api.model
    def import_order_from_webhook_notification(self, resource_url, account_id):
        if not account_id:
            return False

        try:
            account = self.env['shipstation.accounts'].browse(account_id)
            headers = {'Content-Type': 'application/json'}
            res = requests.get(resource_url, auth=HTTPBasicAuth(account.api_key, account.api_secret), headers=headers)
            if res.ok:
                order_data = res.json().get('orders', [])
                for vals in order_data:
                    if not self.search([('order_id', '=', vals.get('orderId'))]):
                        shipping_order = self.create({
                            'order_id': vals.get('orderId'),
                            'order_key': vals.get('orderKey'),
                            'order_date': parser.parse(vals.get('orderDate')).strftime("%Y-%m-%d %H:%M:%S"),
                            'order_number': vals.get('orderNumber'),
                            'account_id': account.id,
                        })
                        self.env.cr.commit()
                        if shipping_order:
                            shipping_order.update_status()

        except Exception as e:
            self.env.cr.rollback()
            logging.error(str(e))

        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
