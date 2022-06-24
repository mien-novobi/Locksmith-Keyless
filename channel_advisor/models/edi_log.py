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

    name = fields.Char(string="Order Reference")
    message = fields.Text(string='Error Message')
    attachment_id = fields.Many2one('ir.attachment', 'File')
    sale_id = fields.Many2one('sale.order', 'Sale Order')
    state = fields.Selection([
        ('new', 'New'),
        ('done', 'Reimported'),
    ], string="Status", default="new")

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
        ship_info['BuyerEmailAddress'] =  node.get('BuyerEmailAddress', '')
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
        name = address.get('FirstName', '') + address.get('LastName', '')
        email = address.get('BuyerEmailAddress', '')
        street  = address.get('address1', '')
        street2  = address.get('address2', '')
        state = address.get('RegionDescription', '')
        city = address.get('City', '')
        zip_code = address.get('PostalCode', '')
        phone = address.get('PhoneNumberDay', '')
        domain = [('active', '=', True)]

        if email:
            domain += [('email', '=', email)]
        elif phone:
            domain += [('phone', '=', phone)]
        else:
            domain += [('name', 'ilike', name)]
            if city:
                domain.append(('city', '=ilike', city))
            if street:
                domain.append(('street', '=ilike', street))
            if street2:
                domain.append(('street2', '=ilike', street2))
            if zip_code:
                domain.append(('zip', '=', zip_code))

        del_addr = self.env['res.partner'].search(domain, limit=1)
        if del_addr:
            del_addr.write({
                'parent_id': False,
                'type': 'contact',
                'company_type': 'person',
            })
        else:
            State = False
            Country = False
            if  address.get('CountryCode', ''):
                Country = self.env['res.country'].search([('code', '=', address.get('CountryCode', ''))])
                if Country:
                    State = self.env['res.country.state'].search(
                        [('name', '=', address.get('RegionDescription', '')), ('country_id', '=', Country.id)])

            vals = {
                'name':  address.get('FirstName', '') +  '' + address.get('LastName', '') or '',
                'email': email,
                'phone': phone,
                'street': street,
                'street2': street2,
                'zip': zip_code,
                'city': city,
                'state_id': State and State.id or False,
                'country_id': Country and Country.id or False,
                'type': 'contact',
                'company_type': 'person',
                # 'parent_id': customer.id
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

        if line.get('TaxPrice') and line.get('UnitPrice', '') and line.get('Quantity', 0):
            tax = round(((line.get('TaxPrice') / (line.get('UnitPrice', '') * line.get('Quantity', 0))) * 100), 2)
            taxes = self.env['account.tax'].search([('amount', '=', tax), ('type_tax_use', '!=', 'purchase')])
            if not taxes:
                values = {'name': str(tax),
                          'amount': tax
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
        if Customer.name == "Shopify" or Customer.ca_site_id == 862:
            if delivery_address:
                Customer = delivery_address
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

        if not saleorder:
            saleorder = SaleOrder.create(vals)

        if saleorder.state in  ['draft', 'sent'] and Customer.name != 'Checkout Direct' and data.get('Paymentstatus') == 'Cleared':
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
        imported_date = datetime.now() - timedelta(minutes=30)
        if self.env.context.get('from_cron'):
            connector = self.env['ca.connector'].search([('state', '=', 'active'), ('auto_import_orders', '=', True)], limit=1)
        else:
            connector = self.env['ca.connector'].search([('state', '=', 'active')], limit=1)
        if not connector:
            return False

        date_filter = False
        if connector.orders_imported_date:
            last_imported_date = connector.orders_imported_date - timedelta(minutes=60)
            date_filter = "CreatedDateUtc ge %s and CreatedDateUtc lt %s" % (last_imported_date.strftime("%Y-%m-%dT%H:%M:%SZ"), imported_date.strftime("%Y-%m-%dT%H:%M:%SZ"))

        res = connector.call('import_orders', filter=date_filter)

        center_dict = {center.res_id: center.warehouse_id.id for center in self.env['ca.distribution.center'].search([])}
        for values in res.get('value', []):
            try:
                vals = self._get_values(values) or {}
                error_message = ''
                try:
                    SaleOrder = self.create_order(vals,center_dict)
                    cr.commit()

                    # Creating and Validating Invoice
                    if SaleOrder.invoice_status == 'to invoice':
                        invoices = SaleOrder._create_invoices(final=True)
                        invoices.pay_and_reconcile(connector.default_journal_id)
                        cr.commit()
                except Exception as e:
                    cr.rollback()
                    error_message = e
                    SaleOrder = False
                    ca_order_id = vals.get('order_no', '')
                    if ca_order_id or error_message:
                        self.create({
                            'name': ca_order_id,
                            'message': error_message,
                            'state': 'new',
                        })
                        cr.commit()
            except Exception as e:
                cr.rollback()
                error_message = e
                if error_message:
                    self.create({
                        'name': values.get('ID', ''),
                        'message': error_message,
                        'state': 'new',
                    })
                    cr.commit()

        if res.get('@odata.nextLink') and connector:
            connector.write(
                {'orders_import_nextlink': res.get('@odata.nextLink', '').split('$skip=')[1]})
            self._import_orders()
        else:
            connector.write({
                'orders_import_nextlink': '',
                'orders_imported_date': imported_date,
            })
        cr.commit()


        return True

    @api.model
    def _cron_confirm_ca_order(self, limit=None):
        connector = self.env['ca.connector'].sudo().search([('state', '=', 'active')], limit=1)
        if not connector:
            return False

        cr = self.env.cr
        SaleOrder = self.env ['sale.order'].sudo()
        orders = SaleOrder.search([
            ('is_edi_order', '=', True),
            ('chnl_adv_order_id', '!=', False),
            ('state', 'in', ['draft', 'sent']),
        ], limit=limit)

        for order in orders:
            try:
                res = connector.call('get_payment_status', order_id=order.chnl_adv_order_id) or {}
                if res.get('PaymentStatus', 'pending') == 'Cleared':
                    order.action_confirm()
                    if res.get('CreatedDateUtc'):
                        order_date = self.convert_date_time(res['CreatedDateUtc'])
                        order.write({'date_order': order_date})

                    if order.is_fba:
                        for pack in order.picking_ids.move_line_ids:
                            if pack.product_qty > 0:
                                pack.write({'qty_done': pack.product_qty})
                        order.picking_ids.action_done()

                    cr.commit()

                    if order.invoice_status == 'to invoice':
                        invoices = order._create_invoices(final=True)
                        invoices.pay_and_reconcile(connector.default_journal_id)
                        cr.commit()

            except Exception as e:
                cr.rollback()

        return True

    def _reimport(self):
        connector = self.env['ca.connector'].sudo().search([('state', '=', 'active')], limit=1)
        if not connector:
            return False

        cr = self.env.cr
        SaleOrder = self.env['sale.order'].sudo()
        dist_centers = {center.res_id: center.warehouse_id.id for center in self.env['ca.distribution.center'].search([])}

        for rec in self:
            try:
                sale_order = SaleOrder.search([('chnl_adv_order_id', '=', rec.name),('state', 'not in', ['cancel'])], limit=1)
                if not sale_order:
                    res = connector.call('retrieve_order', order_id=rec.name)
                    vals = self._get_values(res) or {}
                    sale_order = self.create_order(vals, dist_centers)

                rec.write({
                    'sale_id': sale_order.id,
                    'state': 'done',
                })
                cr.commit()

                # Creating and Validating Invoice
                if sale_order.invoice_status == 'to invoice':
                    invoices = sale_order._create_invoices(final=True)
                    invoices.pay_and_reconcile(connector.default_journal_id)
                    cr.commit()
            except Exception as e:
                cr.rollback()
                rec.message = e
                cr.commit()

    @api.model
    def _cron_reimport_orders(self, limit=None):
        failed_orders = self.sudo().search([('state', '=', 'new'), ('name', '!=', False)], limit=limit)
        failed_orders._reimport()

    def action_reimport(self):
        self.ensure_one()
        if self.state == 'new':
            self._reimport()
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

