# -*- coding: utf-8 -*-
import io
import csv
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import http, fields
from odoo.http import request


class PurchaseReportExport(http.Controller):

    @http.route('/web/purchase/report/export', type="http", auth="user")
    def export_purchasing_report(self, **kargs):
        csv_file = io.StringIO()
        writer = csv.writer(csv_file)

        headers = ['Internal Reference', 'Name', 'Cost', 'Sales Price', 'MARK-UP', 'Quantity On Hand', 'Quantity Back Ordered', 'Quantity on order', 'Monthly Avg Sales', 'MIN QUANTITY', 'MAX QUANTITY', 'Dropship (False/True)', 'Product Category', 'Vendor']

        today = date.today()
        from_date = today - relativedelta(months=12, day=1)
        date_start = from_date
        domain_dates = []
        for i in range(1, 14):
            headers.insert(8 + i, date_start.strftime('%b-%y'))
            date_end = from_date + relativedelta(months=i)
            domain_dates += [(date_start, date_end)]
            date_start = date_end

        writer.writerow(headers)

        products = request.env['product.product'].sudo().search([
            ('type', '=', 'product'),
            ('purchase_ok', '=', True),
            ('categ_id', '=?', int(kargs.get('category', False))),
        ])
        SaleOrderLine = request.env['sale.order.line'].sudo()
        PurchaseOrderLine = request.env['purchase.order.line'].sudo()

        for product in products:
            product_available = product._product_available().get(product.id, {})
            product_sales = SaleOrderLine.search([
                ('product_id', '=', product.id),
                ('order_id.state', 'in', ['sale', 'done']),
                ('order_id.date_order', '>=', from_date.strftime('%Y-%m-%d')),
                ('order_id.date_order', '<=', today.strftime('%Y-%m-%d')),
            ])
            sales_avg = sum(product_sales.mapped('product_uom_qty')) / 12
            vals = [
                product.default_code or '',
                product.display_name,
                product.standard_price,
                product.lst_price,
                '',
                product_available.get('qty_available', 0),
                0,
                product_available.get('incoming_qty', 0),
                sales_avg,
                '',
                '',
                bool(product.route_ids.filtered(lambda r: r.name == 'Dropship')),
                product.categ_id.name,
                product.seller_ids[:1].name.name or '',
            ]

            for i, domain_date in enumerate(domain_dates):
                product_purchases = PurchaseOrderLine.search([
                    ('product_id', '=', product.id),
                    ('order_id.state', 'in', ['purchase', 'done']),
                    ('order_id.date_approve', '>=', domain_date[0].strftime('%Y-%m-%d')),
                    ('order_id.date_approve', '<', domain_date[1].strftime('%Y-%m-%d')),
                ])
                purchase_sum = sum(product_purchases.mapped('product_qty'))
                vals.insert(9 + i, purchase_sum)

            writer.writerow(vals)

        response = request.make_response(
            csv_file.getvalue(),
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', 'attachment; filename=purchasing_report.csv;')])

        return response


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
