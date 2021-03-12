# -*- coding: utf-8 -*-

from datetime import datetime

from odoo import api, fields, models


class UpdateQueue(models.Model):
    _name = "ca.update.queue"
    _description = "Channel Advisor Update Queue"
    _rec_name = "product_id"

    product_id = fields.Many2one('product.product', string="Product")
    update_type = fields.Selection([
        ('quantity', 'Quantity'),
        ('list_price', 'Sales Price'),
        ('standard_price', 'Cost'),
    ], string="Type")

    @api.model
    def _cron_process_update_queue(self, batch_size=80):
        cr = self.env.cr

        queue_size = self.search_count([('update_type', '=', 'quantity')])
        dist_centers = self.env['ca.distribution.center'].search([('type', '=', 'Warehouse'), ('warehouse_id', '!=', False)])

        if not queue_size or not dist_centers:
            return False

        apps = self.env['ca.connector'].sudo().search([('state', '=', 'active')])
        for app in apps:
            profile_ids = app.ca_account_ids.mapped('account_id')
            while queue_size > 0:
                queue_items = self.search([
                    ('update_type', '=', 'quantity'),
                    ('product_id.ca_product_id', '!=', False),
                    ('product_id.ca_profile_id', 'in', profile_ids),
                    ('product_id.ca_product_type', 'in', ['Item', 'Child']),
                ], limit=batch_size)

                if not queue_items:
                    break
                else:
                    queue_size -= batch_size

                data = {}
                products = queue_items.mapped('product_id')
                for product in products:
                    vals = {'Value': {'UpdateType': 'Absolute', 'Updates': []}}
                    for dist_center in dist_centers:
                        qty_available = product.with_context(warehouse=dist_center.warehouse_id.id).free_qty
                        vals['Value']['Updates'].append({
                            'DistributionCenterID': int(dist_center.res_id),
                            'Quantity': int(qty_available),
                        })
                    data[product.ca_product_id] = vals
                try:
                    if data:
                        app.call('batch_update_quantity', batch_data=data)
                        products.write({'ca_qty_updated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                    queue_items.unlink()
                    cr.commit()
                except Exception as e:
                    cr.rollback()
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

