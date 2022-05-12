# -*- coding: utf-8 -*-
import io
import csv
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import http, fields
from odoo.http import request


class PurchaseReportExport(http.Controller):

    @http.route('/web/purchase/report/export/<int:id>', type="http", auth="user")
    def export_purchasing_report(self, id=None, **kargs):
        report_filter = request.env['purchasing.report.filter'].sudo().browse(id)

        csv_file = io.StringIO()
        writer = csv.writer(csv_file)

        headers = ['Internal Reference', 'Name', 'Cost', 'Sales Price', 'MARK-UP', 'Quantity On Hand', 'Quantity Back Ordered', 'Quantity on order', 'Monthly Avg Sales', 'MIN QUANTITY', 'MAX QUANTITY', 'TOTAL UNITS SOLD', 'TOTAL $ SOLD', 'Dropship (False/True)', 'Product Category', 'Vendor']

        SaleOrderLine = request.env['sale.order.line'].sudo()
        PurchaseOrder = request.env['purchase.order'].sudo()
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

        domain = [('type', '=', 'product'), ('purchase_ok', '=', True)]
        if report_filter.categ_id:
            domain += [('categ_id', '=', report_filter.categ_id.id)]

        if report_filter.partner_id:
            product_ids = PurchaseOrder.search([('partner_id', '=', report_filter.partner_id.id), ('state', 'in', ['purchase', 'done'])]).mapped('order_line.product_id').ids
            domain += [('id', 'in', product_ids)]

        if report_filter.include_child:
            domain += [('ca_product_type', 'in', ['Item', 'Parent', 'Child'])]
        else:
            domain += [('ca_product_type', 'in', ['Item', 'Parent'])]


        products = request.env['product.product'].sudo().search(domain)


        for product in products:
            product_available = product._product_available().get(product.id, {})
            margin = (1 - (product.standard_price / product.lst_price)) if product.lst_price else 0
            vals = [
                product.default_code or '',
                product.display_name,
                product.standard_price,
                product.lst_price,
                margin,
                product_available.get('qty_available', 0),
                0,
                product_available.get('incoming_qty', 0),
                0,
                '',
                '',
                '',
                '',
                bool(product.route_ids.filtered(lambda r: r.name == 'Dropship')),
                product.categ_id.name,
                product.seller_ids[:1].name.name or '',
            ]

            sales_data = []
            sales_total = 0
            for i, domain_date in enumerate(domain_dates):
                product_sales = SaleOrderLine.search([
                    ('product_id', '=', product.id),
                    ('order_id.state', 'in', ['sale', 'done']),
                    ('order_id.date_order', '>=', domain_date[0].strftime('%Y-%m-%d')),
                    ('order_id.date_order', '<', domain_date[1].strftime('%Y-%m-%d')),
                ])
                sales_total += sum(product_sales.mapped('price_subtotal'))
                sales_sum = sum(product_sales.mapped('product_uom_qty'))
                sales_data.append(sales_sum)
                vals.insert(9 + i, sales_sum)

            sales_qty_total = sum(sales_data)
            vals[8] = sales_qty_total / 12
            vals[22] = product.reordering_min_qty
            vals[23] = product.reordering_max_qty
            vals[24] = sales_qty_total
            vals[25] = sales_total
            writer.writerow(vals)

        response = request.make_response(
            csv_file.getvalue(),
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', 'attachment; filename=purchasing_report.csv;')])

        return response


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
