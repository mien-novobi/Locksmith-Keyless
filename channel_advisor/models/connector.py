# -*- coding: utf-8 -*-

import json
import base64
import requests
from datetime import datetime, timedelta

from odoo import api, fields, models
import logging
class ChannelAdvisorConnector(models.Model):
    _name = "ca.connector"
    _description = "Channel Advisor Connector"

    base_url = "https://api.channeladvisor.com"

    name = fields.Char(string="Name")
    description = fields.Char(string="Description")
    application_id = fields.Char(string="Application ID")
    shared_secret = fields.Char(string="Shared Secret")
    refresh_token = fields.Char(string="Refresh Token")
    access_token = fields.Char(string="Access Token")
    client_id = fields.Char(compute="_compute_client_id", store=True)
    expiry_date = fields.Datetime(string="Expire At")
    state = fields.Selection([
        ('draft', 'Inactive'),
        ('active', 'Active'),
    ], string="Status", default="draft")
    auto_import_orders = fields.Boolean(string="Auto Import Orders?", default=True)
    orders_imported_date = fields.Datetime(string="Orders Last Imported Date")
    auto_import_products = fields.Boolean(string="Auto Import Products?", default=True)
    products_imported_date = fields.Datetime(string="Products Last Imported Date")
    ca_account_ids = fields.Many2many('ca.account', string="Accounts")
    product_import_nextlink = fields.Char(string="Products Import NextLink")
    orders_import_nextlink = fields.Char(string="Orders Import NextLink")
    orders_item_import_nextlink = fields.Char(string="Items Import NextLink")
    auto_update_price = fields.Boolean(string="Auto Update Price?", default=False)
    auto_update_cost = fields.Boolean(string="Auto Update Cost?", default=False)
    default_journal_id = fields.Many2one('account.journal', string="Default Payment Journal")

    @api.depends('application_id', 'shared_secret')
    def _compute_client_id(self):
        for rec in self:
            auth_code = "%s:%s" % (rec.application_id, rec.shared_secret)
            client_id = base64.b64encode(auth_code.encode("utf-8"))
            rec.client_id = client_id.decode("utf-8")

    def call(self, method=None, **kwargs):
        """
        This function is responsible for making all api calls with channeladvisor.

        :param `str`  method : api call identifier
        :param `dict` kwargs : required api parameters

        :rtype               : dict
        :returns             : response data (res.json())
        """
        self.ensure_one()
        data = {}

        if method == "import_products":
            resource_url = self.base_url + "/v1/Products?access_token=%s&$expand=Images" % self._access_token()
            if kwargs.get('filter'):
                resource_url += "&$filter=%s" % kwargs['filter']

            if kwargs.get('select'):
                resource_url += "&$select=%s" %  ','.join(kwargs['select'])

            if self.product_import_nextlink:
                resource_url += "&$skip=%s" % self.product_import_nextlink

            res = requests.get(resource_url)
            data = res.json()

        elif method == "import_orders":
            resource_url = self.base_url + "/v1/Orders?access_token=%s&$expand=Items($expand=Promotions),Fulfillments" % self._access_token()
            if kwargs.get('filter'):
                resource_url += "&$filter=%s" % kwargs['filter']
            if self.orders_import_nextlink:
                resource_url += "&$skip=%s" % self.orders_import_nextlink
            res = requests.get(resource_url)
            data = res.json()

        elif method == "retrieve_order":
            if kwargs.get('order_id'):
                resource_url = self.base_url + "/v1/Orders(%s)?access_token=%s&$expand=Items($expand=Promotions),Fulfillments" % (kwargs.get('order_id'), self._access_token())
                res = requests.get(resource_url)
                data = res.json()

        elif method == "update_quantity":
            if kwargs.get('product_id') and kwargs.get('vals'):
                header = {'Content-Type': 'application/json'}
                resource_url = self.base_url + "/v1/Products(%s)/UpdateQuantity?access_token=%s" % (kwargs['product_id'], self._access_token())
                res = requests.post(resource_url, headers=header, json=kwargs['vals'])
                # There is nothing to return

        elif method == "batch_update_quantity":
            batch_data = kwargs.get('batch_data', {})
            data = []
            for i, product_id in enumerate(batch_data):
                data.append("--changeset\nContent-Type: application/http\nContent-Transfer-Encoding: binary\nContent-ID: %(content_id)d\n\nPOST %(resource_url)s HTTP/1.1\nContent-Type: application/json\n\n%(values)s" % {
                    'content_id': i + 1,
                    'resource_url': self.base_url + "/V1/Products(%s)/UpdateQuantity" % (product_id),
                    'values': json.dumps(batch_data[product_id], indent=4),
                })

            if data:
                header = {'Content-Type': 'multipart/mixed; boundary=changeset'}
                request_url = self.base_url + "/v1/$batch?access_token=%s" % (self._access_token())
                body = "--batch Content-Type: multipart/mixed; boundary=changeset\n%(data)s\n--changeset--\n--batch--" % {'data': '\n'.join(data)}
                res = requests.post(request_url, headers=header, data=body)
                # There is nothing to return

        elif method == "update_price":
            if kwargs.get('product_id') and kwargs.get('vals'):
                header = {'Content-Type': 'application/json'}
                resource_url = self.base_url + "/v1/Products(%s)?access_token=%s" % (kwargs['product_id'], self._access_token())
                res = requests.put(resource_url, headers=header, json=kwargs['vals'])
                # There is nothing to return

        elif method == "refresh_access_token":
            endpoint_url = self.base_url + "/oauth2/token"
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': "Basic %s" % self.client_id
            }
            body = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
            }
            res = requests.post(endpoint_url, headers=headers, data=body)
            data = res.json()

        elif method == "get_accounts":
            resource_url = self.base_url + "/v1/Profiles?access_token=%s" % self._access_token()
            res = requests.get(resource_url)
            data = res.json()

        elif method == "get_distribution_centers":
            resource_url = self.base_url + "/v1/DistributionCenters?access_token=%s" % self._access_token()
            res = requests.get(resource_url)
            data = res.json()

        elif method == "retrieve_bundle_components":
            if kwargs.get('bundle_id'):
                resource_url = self.base_url + "/v1/Products(%s)/BundleComponents?access_token=%s" % (kwargs['bundle_id'], self._access_token())
                logging.info(resource_url)
                res = requests.get(resource_url)
                logging.info(res.status_code)
                if not res.status_code not in [400, 401]:
                    data = res.json()

        elif method == "get_payment_status":
            if kwargs.get('order_id'):
                resource_url = self.base_url + "/v1/Orders(%s)?access_token=%s&$select=PaymentStatus,CreatedDateUtc" % (kwargs['order_id'], self._access_token())
                res = requests.get(resource_url)
                data = res.json()

        return data

    def _refresh_access_token(self):
        for app in self:
            res = app.call('refresh_access_token')
            if 'access_token' in res:
                expires_in = res.get('expires_in', 3600) - 600
                app.write({
                    'access_token': res.get('access_token'),
                    'expiry_date': datetime.now() + timedelta(seconds=expires_in),
                })

        return True

    def _access_token(self):
        self.ensure_one()
        if not self.access_token or self.expiry_date < datetime.now():
            self._refresh_access_token()

        return self.access_token

    def _get_accounts(self):
        CaAccount = self.env['ca.account'].sudo()
        for app in self:
            res = app.call('get_accounts')
            account_ids = []
            for vals in res.get('value', []):
                account = CaAccount.search([('account_id', '=', vals.get('ID'))])
                if account:
                    account.write({
                        'name': vals.get('AccountName', ''),
                        'company_name': vals.get('CompanyName', ''),
                        'default_dist_center_id': vals.get('DefaultDistributionCenterID', ''),
                    })
                else:
                    account = CaAccount.create({
                        'name': vals.get('AccountName', ''),
                        'account_id': vals.get('ID', ''),
                        'company_name': vals.get('CompanyName', ''),
                        'default_dist_center_id': vals.get('DefaultDistributionCenterID', ''),
                    })
                account_ids.append(account.id)
            app.write({'ca_account_ids': [(6, 0, account_ids)]})

    def _get_distribution_centers(self):
        DistributionCenter = self.env['ca.distribution.center'].sudo()
        for app in self:
            res = app.call('get_distribution_centers')
            for vals in res.get('value', []):
                center = DistributionCenter.search([('res_id', '=', vals.get('ID'))])
                if not center:
                    DistributionCenter.create({
                        'name': vals.get('Name', ''),
                        'code': vals.get('Code', ''),
                        'type': vals.get('Type', ''),
                        'res_id': vals.get('ID', ''),
                    })

    def _import_products(self, run_by="auto"):
        cr = self.env.cr
        imported_date = datetime.now()
        Product = self.env['product.product'].sudo()
        categories = {categ.name: categ.id for categ in self.env['product.category'].sudo().search([])}
        for app in self:
            date_filter = False
            if app.products_imported_date:
                last_imported_date = app.products_imported_date - timedelta(minutes=10)
                date_filter = "UpdateDateUtc ge %s" % last_imported_date.strftime("%Y-%m-%dT%H:%M:%SZ")

            select = [
                'ID',
                'Sku',
                'Title',
                'ProfileID',
                'ProductType',
                'MPN',
                'Brand',
                'Cost',
                'Weight',
                'Condition',
                'RetailPrice',
                'Description',
                'Manufacturer',
                'Classification',
                'ParentProductID',
            ]

            res = app.call('import_products', filter=date_filter, select=select)
            for values in res.get('value', []):
                try:
                    vals = {
                        'name': values.get('Title') or values.get('Sku'),
                        'default_code': values.get('Sku'),
                        'description_sale': values.get('Description'),
                        'ca_product_id': values.get('ID'),
                        'ca_profile_id': values.get('ProfileID'),
                        'weight': values.get('Weight') or 0,
                        'standard_price': values.get('Cost') or 0,
                        'lst_price': values.get('RetailPrice') or 0,
                        'categ_id': categories.get(values.get('Classification'), 1),
                        'ca_brand': values.get('Brand') or '',
                        'ca_mpn': values.get('MPN') or '',
                        'ca_product_type': values.get('ProductType') or '',
                        'ca_parent_product_id': values.get('ParentProductID') or '',
                        'ca_condition': values.get('Condition') or '',
                        'ca_manufacturer': values.get('Manufacturer') or '',
                        'is_kit': True if values.get('ProductType') == 'Bundle' else False,
                    }
                    product = Product.search([('ca_product_id', '=', values.get('ID')), ('ca_profile_id', '=', values.get('ProfileID'))])
                    if not product:
                        product = Product.search([('default_code', '=', values.get('Sku')), ('ca_product_id', '=', False)])

                    if not product.image_1920 and values.get('Images'):
                        img_url = values['Images'][0].get('Url')
                        img_data = requests.get(img_url)
                        if img_data.ok:
                            vals['image_1920'] = base64.b64encode(img_data.content)

                    if product:
                        product.with_context(ca_import=True).write(vals)
                    else:
                        vals['type'] = 'product'
                        Product.with_context(ca_import=True).create(vals)
                    cr.commit()
                except Exception as e:
                    cr.rollback()

            if res.get('@odata.nextLink'):
                app.product_import_nextlink = res.get('@odata.nextLink', '').split('$skip=')[1]
                cr.commit()
                if run_by == 'auto':
                    app._import_products()
            else:
                app.write({
                    'product_import_nextlink': '',
                    'products_imported_date': imported_date,
                })
                cr.commit()

    def _cron_update_quantity(self, limit=80):
        dist_centers = self.env['ca.distribution.center'].search([('type', '=', 'Warehouse'), ('warehouse_id', '!=', False)])
        if not dist_centers:
            return

        cr = self.env.cr
        apps = self.search([('state', '=', 'active')])
        for app in apps:
            profile_ids = app.ca_account_ids.mapped('account_id')
            products = self.env['product.product'].search([
                ('ca_product_id', '!=', False),
                ('ca_profile_id', 'in', profile_ids),
                ('ca_product_type', 'in', ['Item', 'Child']),
                '|', ('ca_qty_updated_date', '=', False),
                ('ca_qty_updated_date', '<', datetime.now() - timedelta(hours=3)),
            ], limit=limit)
            for product in products:
                try:
                    vals = {'Value': {'UpdateType': 'Absolute', 'Updates': []}}
                    for dist_center in dist_centers:
                        if product.is_kit:
                            qty_available = product.with_context(warehouse=dist_center.warehouse_id.id).kit_free_qty
                        else:
                            qty_available = product.with_context(warehouse=dist_center.warehouse_id.id).free_qty

                        vals['Value']['Updates'].append({
                            'DistributionCenterID': int(dist_center.res_id),
                            'Quantity': int(qty_available),
                        })
                    app.call('update_quantity', product_id=product.ca_product_id, vals=vals)
                    product.ca_qty_updated_date = datetime.now()
                    cr.commit()
                except Exception as e:
                    cr.rollback()

    def _cron_import_products(self):
        apps = self.search([('state', '=', 'active'), ('auto_import_products', '=', True)])
        apps._import_products()

    def action_import_products(self):
        self.ensure_one()
        self._import_products(run_by="manual")
        return True

    def _cron_import_orders(self):
        apps = self.search([('state', '=', 'active'), ('auto_import_orders', '=', True)])
        if apps:
            apps.env['transaction.log'].with_context({'from_cron': True})._import_orders()

    def action_import_orders(self):
        self.ensure_one()
        self.env['transaction.log']._import_orders()
        return True

    def action_refresh_access_token(self):
        self.ensure_one()
        self._refresh_access_token()

    def action_confirm(self):
        self.ensure_one()
        self._refresh_access_token()
        if self.access_token:
            self._get_accounts()
            self._get_distribution_centers()
            self.state = 'active'
        return True

    def action_reset(self):
        self.ensure_one()
        self.state = 'draft'

    def action_update_quantity(self):
        self.ensure_one()
        UpdateQueue = self.env['ca.update.queue']

        products = self.env['product.product'].search([('ca_product_type', 'in', ['Item', 'Child']), ('ca_product_id', '!=', False)])
        queued_items = UpdateQueue.search([('update_type', '=', 'quantity')]).mapped('product_id')
        products_to_update = products - queued_items

        for product in products_to_update:
            UpdateQueue.create({
                'update_type': 'quantity',
                'product_id': product.id,
            })

        UpdateQueue._cron_process_update_queue()
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
