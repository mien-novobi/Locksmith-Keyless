# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import base64
import os
import xmltodict
import re
from dateutil.relativedelta import relativedelta
from xml.dom.minidom import parseString
from datetime import datetime
import logging
import json
import requests


class TransactionLogger(models.Model):
    _name = "transaction.log"
    _description = "Transaction Log Details"
    _order = 'id desc'

    name = fields.Char(string='Name')
    # ftp_id = fields.Many2one('ftp.configuration', 'FTP ID')
    message = fields.Text(string='Error Message')
    attachment_id = fields.Many2one('ir.attachment', 'File')
    sale_id = fields.Many2one('sale.order', 'Sale Order')


    def _get_values(self, elements):

        # def extract_xml(xml_elements, vals_dict):
        #     for element in xml_elements:
        #         # input()
        #         if not element.childNodes and element.nodeType == element.TEXT_NODE and element.parentNode:
        #             vals_dict.update({element.parentNode.nodeName: element.nodeValue})
        #         if element.childNodes:
        #             if len(element.childNodes) > 1:
        #
        #                 ch_dict = {}
        #                 extract_xml(element.childNodes, ch_dict)
        #                 if element.nodeName in vals_dict:
        #                     vals_dict[element.nodeName].append(ch_dict)
        #                 else:
        #                     vals_dict.update({element.nodeName: [ch_dict]})
        #             else:
        #                 vals_dict.update({element.nodeName: {}})
        #                 extract_xml(element.childNodes, vals_dict[element.nodeName])
        #     # input(vals_dict)
        #     return vals_dict

        order_no = False
        mkt_order_no = False
        date_order = ''
        del_addr = False
        res = {}
        ship_info = {}
        bill_info = {}

        for el in elements:
            # print (el.childNodes)
            # node = {}
            # extract_xml(el.childNodes, node)
            # res.update({'lines': {}})
            if node.get('q1:OrderID') and not order_no:
                res.update({'order_no': node.get('q1:OrderID').get('q1:OrderID')})
            if  not res.get('lines'):
                res.update({'lines': {}})
            if node.get('q1:ClientOrderIdentifier'):
                res.update({'mkt_order_no': node.get('q1:ClientOrderIdentifier').get('q1:ClientOrderIdentifier')})
            if node.get('q1:OrderTimeGMT'):
                res.update({'date_order ': datetime.strptime(node.get('q1:OrderTimeGMT').get('q1:OrderTimeGMT'), "%Y-%m-%dT%H:%M:%S").strftime('%m/%d/%Y %H:%M:%S')})

            if node.get('q1:ShippingInfo') :
                Ship = node.get('q1:ShippingInfo')
                for ShippingInfo in Ship :
                    if ShippingInfo.get('q1:AddressLine1'):
                        ship_info.update({
                            'address1':ShippingInfo.get('q1:AddressLine1').get('q1:AddressLine1'),
                        })
                    if ShippingInfo.get('q1:AddressLine2'):
                        ship_info.update({
                            'address2': ShippingInfo.get('q1:AddressLine2').get('q1:AddressLine2'),
                        })
                    if ShippingInfo.get('q1:City'):
                        ship_info.update({
                            'City': ShippingInfo.get('q1:City').get('q1:City'),
                        })
                    if ShippingInfo.get('q1:RegionDescription'):
                        ship_info.update({
                            'RegionDescription': ShippingInfo.get('q1:RegionDescription').get('q1:RegionDescription'),
                        })
                    if ShippingInfo.get('q1:PostalCode'):
                        ship_info.update({
                            'PostalCode': ShippingInfo.get('q1:PostalCode').get('q1:PostalCode'),
                        })
                    if ShippingInfo.get('q1:CountryCode'):
                        ship_info.update({
                            'CountryCode': ShippingInfo.get('q1:CountryCode').get('q1:CountryCode'),
                        })
                    if ShippingInfo.get('q1:FirstName'):
                        ship_info.update({
                            'FirstName': ShippingInfo.get('q1:FirstName').get('q1:FirstName'),
                        })
                    if ShippingInfo.get('q1:LastName'):
                        ship_info.update({
                            'LastName': ShippingInfo.get('q1:LastName').get('q1:LastName'),
                        })
                    if ShippingInfo.get('q1:PhoneNumberDay'):
                        ship_info.update({
                            'PhoneNumberDay': ShippingInfo.get('q1:PhoneNumberDay').get('q1:PhoneNumberDay'),
                        })
                    res.update({'ship_info': ship_info})
            if node.get('q1:BillingInfo'):
                bill = node.get('q1:BillingInfo')
                for BillingInfo in bill:
                    if BillingInfo.get('q1:AddressLine1'):
                        bill_info.update({
                            'address1': BillingInfo.get('q1:AddressLine1').get('q1:AddressLine1'),
                        })
                    if BillingInfo.get('q1:AddressLine2'):
                        bill_info.update({
                            'address2': BillingInfo.get('q1:AddressLine2').get('q1:AddressLine2'),
                        })
                    if BillingInfo.get('q1:City'):
                        bill_info.update({
                            'City': BillingInfo.get('q1:City').get('q1:City'),
                        })
                    if BillingInfo.get('q1:RegionDescription'):
                        bill_info.update({
                            'RegionDescription': BillingInfo.get('q1:RegionDescription').get('q1:RegionDescription'),
                        })
                    if BillingInfo.get('q1:PostalCode'):
                        bill_info.update({
                            'PostalCode': BillingInfo.get('q1:PostalCode').get('q1:PostalCode'),
                        })
                    if BillingInfo.get('q1:CountryCode'):
                        bill_info.update({
                            'CountryCode': BillingInfo.get('q1:CountryCode').get('q1:CountryCode'),
                        })
                    if BillingInfo.get('q1:FirstName'):
                        bill_info.update({
                            'FirstName': BillingInfo.get('q1:FirstName').get('q1:FirstName'),
                        })
                    if BillingInfo.get('q1:LastName'):
                        bill_info.update({
                            'LastName': BillingInfo.get('q1:LastName').get('q1:LastName'),
                        })
                    if BillingInfo.get('q1:PhoneNumberDay'):
                        bill_info.update({
                            'PhoneNumberDay': BillingInfo.get('q1:PhoneNumberDay').get('q1:PhoneNumberDay'),
                        })
                    res.update({'bill_info':bill_info})

            if node.get('q1:ShoppingCart'):
                for shopping in node.get('q1:ShoppingCart'):
                    for LineItemSKU in shopping.get('q1:LineItemSKUList'):
                        for line_item in LineItemSKU.get('q1:OrderLineItemItem'):
                            if line_item.get('q1:LineItemID'):
                                LineItemID = line_item.get('q1:LineItemID').get('q1:LineItemID')
                                res['lines'].update({LineItemID: {}})
                                if line_item.get('q1:UnitPrice'):
                                    res['lines'][LineItemID].update({'UnitPrice': float(line_item.get('q1:UnitPrice').get('q1:UnitPrice'))})
                                if line_item.get('q1:Quantity'):
                                    res['lines'][LineItemID].update({'Quantity': float(line_item.get('q1:Quantity').get('q1:Quantity'))})
                                if line_item.get('q1:ItemSaleSource'):
                                    res.update({'ItemSaleSource': line_item.get('q1:ItemSaleSource').get('q1:ItemSaleSource')})
                                if line_item.get('q1:SKU'):
                                    res['lines'][LineItemID].update({'SKU': line_item.get('q1:SKU').get('q1:SKU')})
                                if line_item.get('q1:Title'):
                                    res['lines'][LineItemID].update({'Title': line_item.get('q1:Title').get('q1:Title')})
        print ("res",res)
        return res

    def find_or_create_address(self, customer, address, address_type='delivery'):
        """
        FInd or create partner address
        :param address: dict, dictionary containg addres information
        :param address_type: string 'delivery' or 'invoice'
        :return: Partner Address recordset
        """

        street  = address.get('address1', '')
        street1  = address.get('address2', '')
        state = address.get('RegionDescription', '')
        city = address.get('City', '')
        zip_code = address.get('PostalCode', '')
        domain = [('type', '=', address_type), ('parent_id', '=', customer.id), ('active', '=', True), ('city', '=ilike', city),
                  ('zip', '=', zip_code), ]
        # if 'Contacts' in address:
        #     domain.append(('name', '=', address.get('Contacts', {}).get('ContactName', '')))
        # else:
        #     domain.append(('name', '=', address.get('AddressName', {})))
        # contact = customer.search(domain)
        # if not contact:

        if street:
            domain.append(('street', '=ilike', street))
        if street1:
            domain.append(('street2', '=ilike', street1))
        if state:
            domain.append(('state_id.name', '=', state))
        del_addr = self.env['res.partner'].search(domain, limit=1)
        if not del_addr:
            if  address.get('CountryCode', ''):
                Country = self.env['res.country'].search([('code', '=', address.get('CountryCode', ''))])
                State = False
                if Country:
                    State = self.env['res.country.state'].search(
                        [('name', '=', address.get('RegionDescription', '')), ('country_id', '=', Country.id)])

            vals = {
                    'name':  address.get('FirstName', '') +  '' + address.get('LastName', '') or '',
                    'phone': address.get('PhoneNumberDay', '') or '',
                    'street': street or '',
                    'street2': street1 or '',
                    'zip': address.get('PostalCode', '') or '',
                    'city': address.get('City', '') or '',
                    'state_id': State and State.id or False,
                    'country_id': Country and Country.id or False,
                    'type': address_type,
                    'parent_id': customer.id
                }

            del_addr = customer.create(vals)
        return del_addr
    def process_line_item(self, line, customer):
        """
        Process line item and return dict of values to create sale line
        :param line: dict
        :return: dict
        """
        print("line",line)
        Product = self.env['customer.product.values'].search([
            ('product_id.active', '=', True),
            ('partner_id', '=', customer.id),
            ('customer_sku', '=', line.get('SKU')),
        ], limit=1).product_id
        product = self.env['product.product'].search([('product_tmpl_id', '=', Product.id)])
        if not product:
            raise UserError('Product %s not in Product Master' % line.get('Title'))
        print("Product.standard_price",product,product.standard_price,line.get('UnitPrice', ''))
        vals = {

            'product_id': product.id,
            'product_uom_qty': line.get('Quantity', 0),
            'name': line.get('Title', 0) or Product.name,
            # 'tax_id': [[6, 0, taxes]],
            'price_unit': line.get('UnitPrice', ''),
            'purchase_price':product.standard_price

        }
        return vals


    def create_order(self, data):
        """
        Create SaleOrder from EDI data
        :param data: dict
        :return: Order recordset
        """
        delivery_address = False
        invoice_address = False
        Customer = self.env['res.partner'].search(
                    [('name', '=ilike', 'ChannelAdvisor')])
        print ("data",data)
        if data.get('bill_info', '') :
            address = data.get('bill_info', '')
            invoice_address = self.find_or_create_address(Customer, address, 'invoice')
            print("invoice_address",invoice_address)
        if data.get('ship_info', '') :
            address = data.get('ship_info', '')
            delivery_address = self.find_or_create_address(Customer, address, 'delivery')
            print("delivery_address",delivery_address)
        vals = {
            'partner_id':Customer.id,
            'is_edi_order': True,
            'client_order_ref':  data.get('mkt_order_no'),
            'item_sale_source': data.get('ItemSaleSource'),
            'partner_shipping_id': delivery_address and delivery_address.id or Customer.id,  # 59,#
            'partner_invoice_id': invoice_address and invoice_address.id or Customer.id,  # 60,#
        #     # 'carrier_id': carrier and carrier.id or False,
        #     # 'note': notes,
        #     # 'ftp_id': self.ftp_id and self.ftp_id.id or False,
        #     'sps_order_ids': [[0, 0, values]]
        }
        #
        line_vals = []
        print("data.get('lines')", data.get('lines'))
        for line in data.get('lines'):
            print("line$$$$$$$$$$$$$$$$$$$$$$$$4", )
            line_vals.append([0, 0, self.process_line_item(data.get('lines').get(line), Customer)])
            print(line_vals)
           # line_vals = [[0, 0, self.process_line_item(line_item, Customer)]]
        vals.update({'order_line': line_vals})
        SaleOrder = self.env['sale.order'].create(vals)
        return SaleOrder


    def xml_processing(self):
        # try:
            # headers = {
            #     'Content-Type': 'text/xml',
            # }
            # url = "https://shop.vs-moebel.de/ODGW/get_full_object(%s)" % (self.obj_id.replace('-', ''))
            # response = requests.post(url, headers=headers)
            # message_by_code = {
            #     204: 'No content',
            #     302: 'Bad URL',
            #     400: 'Bad Request',
            #     401: 'Unauthorized',
            #     404: 'Not Found',
            #     405: 'Method Not Allowed',
            #     500: 'Internal Server Error'
            # }
            # if response.status_code in message_by_code.keys():
            #     raise UserError("AAs order import failed and returned an HTTP status of %s\n%s" % (
            #     response.status_code, message_by_code.get(response.status_code)))
        # response = open('/home/locksmith_keyless_13/odoo13/channel_adv_order.xml').read()
        # response = open('/home /devika /Projects /13.0 /odoo13 /server/channel_adv_order.xml').read()
        response = requests.get("https://api.channeladvisor.com/v1/Orders?access_token=9hHksWZyA9P4sRH2RvIlPcgyS8Vhfp6lu-r73AN8WjU-38851")
        vals = json.loads(response.text)
        # vals= json.loads(response.content)
        print("todos",todos,type(todos))
        # print("vals",vals,type(vals))


        try:
            print("als",vals)
            values = self._get_values(vals)
            TransactionLog = self.create({
                'name': "create order",
            })
            # os.remove(tempfile)
            error_message = ''
            try:
                SaleOrder = TransactionLog.create_order(values)
            except Exception as e:
                error_message = e
                SaleOrder = False
            if SaleOrder:
                # Attachment.write({'res_id': SaleOrder.id})
                TransactionLog.write(
                    {'message': 'Order created succesfully', 'sale_id': SaleOrder.id, 'name': SaleOrder.name})
            else:
                if error_message:
                    TransactionLog.write({'message': error_message})
        except Exception as e:
            print (e)
            pass
        return True




