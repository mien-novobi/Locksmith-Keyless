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

        SaleReport = request.env['sale.report'].sudo()
        PurchaseOrder = request.env['purchase.order'].sudo()
        today = date.today()
        from_date = today - relativedelta(months=12, day=1)
        domain_dates = {}
        for i in range(0, 13):
            date_start = from_date + relativedelta(months=i)
            headers.insert(9 + i, date_start.strftime('%b-%y'))
            domain_dates[date_start.strftime('%B %Y')] = 9 + i

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
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                0,
                bool(product.route_ids.filtered(lambda r: r.name == 'Dropship')),
                product.categ_id.name,
                product.seller_ids[:1].name.name or '',
            ]

            product_sales = SaleReport.read_group([
                ('product_id', '=', product.id),
                ('state', 'in', ['sale', 'done']),
                ('date', '>=', from_date.strftime('%Y-%m-%d')),
                ('date', '<=', today.strftime('%Y-%m-%d')),
            ], ['date', 'price_subtotal', 'product_uom_qty'],
            groupby=['date:month'],
            orderby='date ASC', lazy=True)
            sales_total = 0
            sales_qty_total = 0
            for rec in product_sales:
                sales_total += rec.get('price_subtotal', 0.0)
                sales_qty = rec.get('product_uom_qty', 0.0)
                sales_qty_total += sales_qty
                vals[domain_dates.get(rec['date:month'])] = sales_qty

            vals[8] = sales_qty_total / 13
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
