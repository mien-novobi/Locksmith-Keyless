# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
import json
import requests
from dateutil import parser


class TransactionLogger(models.Model):
    _name = "transaction.log"
    _description = "Transaction Log Details"
    _order = 'id desc'

    name = fields.Char(string='Name')
    message = fields.Text(string='Error Message')
    attachment_id = fields.Many2one('ir.attachment', 'File')
    sale_id = fields.Many2one('sale.order', 'Sale Order')
    def convert_date_time(self, date_str):
        try:
            date_str1 = parser.parse(date_str).strftime("%Y-%m-%d %H:%M:%S")
            res= datetime.strptime(date_str1,"%Y-%m-%d %H:%M:%S")
            return res

        except:
            raise UserError("Date format is invalid %s" % date_str)


    def _get_values(self, node):

        res = {}
        ship_info = {}
        if node.get('ShippingAddressLine1', ''):
            ship_info.update({
                'address1': node.get('ShippingAddressLine1', ''),
            })
        if node.get('ShippingAddressLine2', ''):
            ship_info.update({
                'address2': node.get('ShippingAddressLine2', ''),
            })
        if node.get('ShippingCity'):
            ship_info.update({
                'City': node.get('ShippingCity'),
            })
        if node.get('ShippingStateOrProvinceName', ''):
            ship_info.update({
                'RegionDescription': node.get('ShippingStateOrProvinceName', ''),
            })
        if node.get('ShippingPostalCode', ''):
            ship_info.update({
                'PostalCode': node.get('ShippingPostalCode', ''),
            })
        if (node.get('ShippingCountry') or '').strip():
            ship_info.update({
                'CountryCode': (node.get('ShippingCountry') or '').strip(),
            })
        if node.get('ShippingFirstName', '',):
            ship_info.update({
                'FirstName': node.get('ShippingFirstName', '',),
            })
        if node.get('ShippingLastName', '',):
            ship_info.update({
                'LastName': node.get('ShippingLastName', '',),
            })
        if node.get('ShippingDaytimePhone', '',):
            ship_info.update({
                'PhoneNumberDay': node.get('ShippingDaytimePhone', '',),
            })
        res.update({'order_no': node.get('ID', ''),
                    'ProfileID': node.get('ProfileID', ''),
                    'SiteName': node.get('SiteName', ''),
                    'SiteID': node.get('SiteID', ''),
                    'SiteOrderID': node.get('SiteOrderID', ''),
                    'DistributionCenterTypeRollup': node.get('DistributionCenterTypeRollup', ''),
                    'TotalShippingPrice': node.get('TotalShippingPrice', ''),
                    'TotalTaxPrice': node.get('TotalTaxPrice', ''),
                    'TotalGiftOptionPrice': node.get('TotalGiftOptionPrice', ''),
                    'PromotionAmount': node.get('PromotionAmount', ''),
                    'PromotionCode': node.get('PromotionCode', ''),
                    'AdditionalCostOrDiscount': node.get('AdditionalCostOrDiscount', ''),
                    'TotalInsurancePrice': node.get('TotalInsurancePrice', ''),
                    'TotalPrice': node.get('TotalPrice', ''),
                    'SpecialInstructions': node.get('SpecialInstructions', ''),
                    'PrivateNotes': node.get('PrivateNotes', ''),
                    'TotalGiftOptionTaxPrice': node.get('TotalGiftOptionTaxPrice', ''),
                    'TotalShippingTaxPrice': node.get('TotalShippingTaxPrice', ''),
                    'Paymentstatus' : node.get('PaymentStatus', ''),
                    })
        if ship_info:
            res.update({'ship_info': ship_info})
        if  not res.get('lines'):
            res.update({'lines': {}})
        if node.get('CreatedDateUtc'):
            create_date = self.convert_date_time(node.get('CreatedDateUtc', ''),)
            res.update({'date_order': create_date})

        if node.get('Items'):
            for line_item in node.get('Items'):
                if line_item.get('ID'):
                    LineItemID = line_item.get('ID')
                    res['lines'].update({LineItemID: {}})
                    res['lines'][LineItemID].update({'UnitPrice': float(line_item.get('UnitPrice') or 0.0)})
                    res['lines'][LineItemID].update({'Quantity': float(line_item.get('Quantity') or 0)})
                    res['lines'][LineItemID].update({'SKU': line_item.get('Sku') or ''})
                    res['lines'][LineItemID].update({'Title': line_item.get('Title') or ''})
                    res['lines'][LineItemID].update({'ProductID': line_item.get('ProductID') or ''})
                    res['lines'][LineItemID].update({'TaxPrice': line_item.get('TaxPrice') or 0.0})
                    promo_amt=0.0
                    if line_item.get('Promotions'):
                        for promo in line_item.get('Promotions'):
                            promo_amt = promo_amt +(promo.get('Amount') or 0.0 )+(promo.get('ShippingAmount') or 0.0 )
                        res['lines'][LineItemID].update({'promo_amt': promo_amt or '0.0','code':promo.get('Code') or ''})

        if node.get('Fulfillments'):
            for fulfilment in node.get('Fulfillments'):
                if 'DistributionCenterID' in fulfilment:
                    res.update({
                        'DistributionCenterID': fulfilment.get('DistributionCenterID', ''),
                    })
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
        phone = address.get('PhoneNumberDay', '')
        domain = [('type', '=', address_type), ('parent_id', '=', customer.id), ('active', '=', True), ('city', '=ilike', city),
                  ('zip', '=', zip_code), ]
        if street:
            domain.append(('street', '=ilike', street))
        if street1:
            domain.append(('street2', '=ilike', street1))
        if phone:
            domain.append(('phone', '=', phone))
        del_addr = self.env['res.partner'].search(domain, limit=1)
        State = False
        Country = False
        if not del_addr:
            if  address.get('CountryCode', ''):
                Country = self.env['res.country'].search([('code', '=', address.get('CountryCode', ''))])
                if Country:
                    State = self.env['res.country.state'].search(
                        [('name', '=', address.get('RegionDescription', '')), ('country_id', '=', Country.id)])


            vals = {
                'name':  address.get('FirstName', '') +  '' + address.get('LastName', '') or '',
                'phone': address.get('PhoneNumberDay', '') or '',
                'street': street or '',
                'street2': street1 or '',
                'zip': address.get('PostalCode', '') ,
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

        vals ={}
        promo_amt = 0
        taxes = self.env['account.tax']
        is_review = False
        product = self.env['product.product'].search([('ca_product_id', '=', line.get('ProductID'))])
        if not product:
            raise UserError('Product %s not Found' % line.get('Title'))

        if line.get('UnitPrice', '') != product.lst_price:
            is_review = True
        else:
            is_review = False
        if line.get('promo_amt'):
            promo_amt = promo_amt + line.get('promo_amt')


        if line.get('TaxPrice') and line.get('UnitPrice', ''):
            tax = round(((line.get('TaxPrice')/line.get('UnitPrice', '')) *100),2)
            taxes = self.env['account.tax'].search([('amount', '=', tax), ('type_tax_use', '!=', 'purchase')])
            if not taxes:
                values= {'name':  str(tax),
                       'amount':tax
                       }
                taxes = self.env['account.tax'].create(values)
        vals = {

            'product_id': product.id,
            'product_uom_qty': line.get('Quantity', 0),
            'name': line.get('Title', 0) or product.name,
            'price_unit': line.get('UnitPrice', ''),
            'purchase_price': product.standard_price,
            'promotion_code': line.get('promo_code', ''),
            'promo_amt': promo_amt,
            'tax_id': [[6, False, taxes.ids or []]],
            'is_review':is_review

        }
        return vals


    def create_order(self, data,center_dict):
        """
        Create SaleOrder from EDI data
        :param data: dict
        :return: Order recordset
        """
        delivery_address = False
        is_review_lst =[]
        is_review = False
        if data.get('SiteID'):
            site = data.get('SiteID')
            site_name = data.get('SiteName')
            if site:
                Customer = self.env['res.partner'].search(
                [('ca_site_id', '=', site)])
            else:
                Customer = self.env['res.partner'].search(
                    [('name', '=ilike', site_name)])
            if not Customer:
                # Customer = self.env['res.partner'].search(
                #     [('name', '=ilike', 'Checkout Direct')])
                raise UserError('Customer  %s not Found ' % data.get('SiteName'))
        if data.get('ship_info', '') :
            address = data.get('ship_info', '')
            delivery_address = self.find_or_create_address(Customer, address, 'delivery')
        vals = {
            'partner_id':Customer.id,
            'is_edi_order': True,
            'name':data.get('order_no'),
            'chnl_adv_order_id': data.get('order_no'),
            'client_order_ref':  data.get('SiteOrderID'),
            'partner_shipping_id': delivery_address and delivery_address.id or Customer.id,  # 59,#
            'partner_invoice_id': Customer.id,  # 60,#
            'special_instruction': data.get('SpecialInstructions'),
            'private_note': data.get('PrivateNotes'),
            'total_price': data.get('TotalPrice'),
            'date_order':data.get('date_order'),
            #     # 'carrier_id': carrier and carrier.id or False,
            #     # 'note': notes,
        }
        line_vals = []
        promo_amt = 0
        for line in data.get('lines'):
            get_lines = self.process_line_item(data.get('lines').get(line), Customer)
            is_review_lst.append(get_lines.pop('is_review', False))
            line_vals.append((0, 0, get_lines))
            promo_amt = promo_amt+ get_lines.pop('promo_amt', False)


        pdt = self.env.user.company_id.shipping_cost_product_id
        # tax = self.env.user.company_id.tax_product_id
        gift = self.env.user.company_id.gift_product_id
        promo = self.env.user.company_id.promotion_product_id
        addt_cost = self.env.user.company_id.addt_cost_product_id
        insurance = self.env.user.company_id.insurance_product_id
        taxes = self.env['account.tax']
        if pdt :
            if data.get('TotalShippingTaxPrice') and  data.get('TotalShippingPrice', ''):
                tax = round((( data.get('TotalShippingTaxPrice') /  data.get('TotalShippingPrice', '')) * 100), 2)
                taxes = self.env['account.tax'].search([('amount', '=', tax), ('type_tax_use', '!=', 'purchase')])
                if not taxes:
                    values = {'name': str(tax),
                            'amount': tax
                            }
                    taxes = self.env['account.tax'].create(values)
            line_vals.append((0, 0, {'product_id': pdt.id,'price_unit': data.get('TotalShippingPrice', 0),'name':pdt.name,'tax_id': [[6, False, taxes.ids or []]],}))
        # if tax and data.get('TotalTaxPrice', 0) :
        #     line_vals.append(
        #         (0, 0, {'product_id': tax.id, 'price_unit': data.get('TotalTaxPrice', 0), 'name': tax.name}))
        if gift and data.get('TotalGiftOptionPrice', 0) :
            if data.get('TotalGiftOptionTaxPrice') :
                tax = round((( data.get('TotalGiftOptionTaxPrice') /  data.get('TotalGiftOptionPrice', '')) * 100), 2)
                taxes = self.env['account.tax'].search([('amount', '=', tax), ('type_tax_use', '!=', 'purchase')])
                if not taxes:
                    vals = {'name': str(tax),
                            'amount': tax
                            }
                    taxes = self.env['account.tax'].create(vals)
            line_vals.append(
                (0, 0, {'product_id': gift.id, 'price_unit': data.get('TotalGiftOptionPrice', 0), 'name': gift.name,'tax_id': [[6, False, taxes.ids or []]],}))
        if data.get('PromotionAmount', 0) or promo_amt and promo  :
            price_unit = data.get('PromotionAmount', 0) + promo_amt
            promo_name= data.get('PromotionCode', '') if data.get('PromotionCode', '') else  promo.name
            line_vals.append(
                (0, 0, {'product_id': promo.id, 'price_unit': price_unit, 'name':promo_name }))
        if addt_cost and data.get('AdditionalCostOrDiscount', 0):
            line_vals.append(
                (0, 0, {'product_id': addt_cost.id, 'price_unit': data.get('AdditionalCostOrDiscount', 0), 'name': addt_cost.name,'product_uom': 1,}))
        if insurance and data.get('TotalInsurancePrice', 0):
            line_vals.append(
                (0, 0, {'product_id': insurance.id, 'price_unit': data.get('TotalInsurancePrice', 0), 'name': insurance.name,'product_uom': 1,}))
        is_review = any(is_review_lst)
        vals.update({'order_line':line_vals,'is_review':is_review})
        if data.get('DistributionCenterTypeRollup', '') == "ExternallyManaged" and data.get('DistributionCenterID'):
            vals.update({
                'is_fba': True,
                'warehouse_id': center_dict.get(str(data['DistributionCenterID']), False),
            })
        SaleOrder = self.env ['sale.order']
        saleorder = SaleOrder.search(
            [('chnl_adv_order_id', '=', data.get('order_no')),('state', 'not in', ['cancel'])], limit=1)
        if saleorder:
            if saleorder.state in  ['draft', 'sent']:
                saleorder.write(vals)
        else:
            saleorder = SaleOrder.create(vals)
            if Customer.name != 'Checkout Direct' and data.get('Paymentstatus') == 'Cleared' :
                saleorder.action_confirm()
                saleorder.write({'date_order': data.get('date_order')})
                if saleorder.is_fba:
                    for pack in saleorder.picking_ids.move_line_ids:
                        if pack.product_qty > 0:
                            pack.write({'qty_done': pack.product_qty})
                    saleorder.picking_ids.action_done()

        return saleorder


    def _import_orders(self):
        cr = self.env.cr
        imported_date = datetime.now()
        if self.env.context.get('from_cron'):
            connector = self.env['ca.connector'].search([('state', '=', 'active'), ('auto_import_orders', '=', True)], limit=1)
        else:
            connector = self.env['ca.connector'].search([('state', '=', 'active')], limit=1)
        if not connector:
            return False

        date_filter = False
        if connector.orders_imported_date:
            last_imported_date = connector.orders_imported_date - timedelta(minutes=60)
            date_filter = "CreatedDateUtc ge %s" % last_imported_date.strftime("%Y-%m-%dT%H:%M:%SZ")
        res = connector.call('import_orders', filter=date_filter)
        center_dict = {center.res_id: center.warehouse_id.id for center in self.env['ca.distribution.center'].search([])}
        for values in res.get('value', []):
            try:
                vals = self._get_values(values)
                error_message = ''
                try:
                    SaleOrder = self.create_order(vals,center_dict)
                    cr.commit()

                    # Creating and Validating Invoice
                    if SaleOrder.invoice_status == 'to invoice':
                        invoices = SaleOrder._create_invoices(final=True)
                        invoices.post()
                        cr.commit()
                except Exception as e:
                    cr.rollback()
                    error_message = e
                    SaleOrder = False
                    if error_message:
                        self.create({'message': error_message,'name': "Error in Order Import"})
                        cr.commit()
            except Exception as e:
                cr.rollback()
                error_message = e
                if error_message:
                    self.create({'message': error_message, 'name': "Error in Order Import"})
                    cr.commit()
        if res.get('@odata.nextLink') and connector:
            connector.write(
                {'orders_import_nextlink': res.get('@odata.nextLink', '').split('$skip=')[1]})

            # self._import_orders()
        else:
            connector.write({
                'orders_import_nextlink': '',
                'orders_imported_date': imported_date,
            })
        cr.commit()


        return True




