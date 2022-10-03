# -*- coding: utf-8 -*-
import io
import csv
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import http, fields,api
from odoo.http import request
import base64
import pandas as pd

class PurchaseReportExport(http.Controller):

    @http.route('/web/purchase/report/export/<int:id>', type="http", auth="user")
    def export_purchasing_report(self, id=None, **kargs):
        report_filter = request.env['purchasing.report.filter'].sudo().browse(id)

        headers = ['Internal Reference', 'Name', 'Cost', 'Sales Price', 'MARK-UP', 'Quantity On Hand', 'ABC classification', 'Quantity on order', 'Monthly Avg Sales', 'MIN QUANTITY', 'MAX QUANTITY', 'TOTAL UNITS SOLD', 'TOTAL $ SOLD', 'Dropship (False/True)', 'Product Category', 'Vendor']

        # SaleReport = request.env['sale.report'].sudo()
        StockMove = request.env['stock.move.line'].sudo()
        PurchaseOrder = request.env['purchase.order'].sudo()
        today = date.today()
        from_date = today - relativedelta(months=12, day=1)
        domain_dates = {}
        for i in range(0, 13):
            date_start = from_date + relativedelta(months=i)
            headers.insert(9 + i, date_start.strftime('%b-%y'))
            domain_dates[date_start.strftime('%B %Y')] = 9 + i

        domain = [('type', '=', 'product'), ('purchase_ok', '=', True),('ca_bundle_product_ids', '=', False),('ca_product_type', 'in', ['Item', 'Child'])]
        if report_filter.categ_id:
            domain += [('categ_id', '=', report_filter.categ_id.id)]

        if report_filter.partner_id:
            product_ids = PurchaseOrder.search([('partner_id', '=', report_filter.partner_id.id), ('state', 'in', ['purchase', 'done'])]).mapped('order_line.product_id').ids
            domain += [('id', 'in', product_ids)]

        # if report_filter.include_child:
        #     domain += []
        #
        #     # domain += [('ca_product_type', 'in', ['Item', 'Parent', 'Child'])]
        # else:
        #     # domain += [('ca_product_type', 'in', ['Item', 'Parent'])]
        #     domain += [('ca_product_type', 'in', ['Item'])]

        data = []
        sales_sum = 0

        query = """
                    select 
        	            product_id,
        	            to_char(date at time zone 'utc' at time zone %s, 'Mon-YY') as month,
        	            sum(product_qty) as qty 
                    from stock_move sm
                    left join stock_picking_type spt on (spt.id = sm.picking_type_id)
                    where 
        	            sm.product_id in %s 
        	            and 
        	            spt.code='outgoing' 
        	            or
        	            spt.is_drop_shipping = 't'
        	            and 
        	            sm.state='done' 
        	            and 
        	            ((sm.date at time zone %s)::timestamp::date) >= %s
        	            and
        	            ((sm.date at time zone %s)::timestamp::date) <= %s
                    group by product_id,month
                """
        products = request.env['product.product'].sudo().search(domain)
        product_ids = (x.id for x in products)
        tz = request.env.user.tz and request.env.user.tz or "America/New_York"
        request.env.cr.execute(query, (
            tz, tuple(product_ids), tz, from_date.strftime('%Y-%m-%d'), tz, today.strftime('%Y-%m-%d')))
        qdata = request.env.cr.dictfetchall()
        df = pd.DataFrame(qdata)
        df.set_index(['product_id', 'month'], inplace=True)

        def get_data(key1, key2):
            try:
                qty_data = df.loc[key1, key2]['qty']
                return qty_data
            except:
                return 0

        for product in products:

            #            product_available = product._product_available().get(product.id, {})
            margin = (1 - (product.standard_price / product.lst_price)) if product.lst_price else 0
            vals = [
                product.default_code or '',
                product.display_name,
                product.standard_price,
                product.lst_price,
                '%.2f%%' % (margin * 100),
                product.qty_available,
                '',
                product.incoming_qty,
                0,
                get_data(product.id, headers[9]),
                get_data(product.id, headers[10]),
                get_data(product.id, headers[11]),
                get_data(product.id, headers[12]),
                get_data(product.id, headers[13]),
                get_data(product.id, headers[14]),
                get_data(product.id, headers[15]),
                get_data(product.id, headers[16]),
                get_data(product.id, headers[17]),
                get_data(product.id, headers[18]),
                get_data(product.id, headers[19]),
                get_data(product.id, headers[20]),
                get_data(product.id, headers[21]),
                0,
                0,
                0,
                0,
                bool(product.route_ids.filtered(lambda r: r.name == 'Dropship')),
                product.categ_id.name,
                product.seller_ids[:1].name.name or '',
            ]

            sales_total = 0
            sales_qty_total = 0
            sales_total += sum(vals[9:21]) * product.lst_price
            sales_qty_total += sum(vals[9:21])

            sales_sum += sales_total
            vals[8] = '%.2f' % (sales_qty_total / 13)
            vals[22] = product.reordering_min_qty
            vals[23] = product.reordering_max_qty
            vals[24] = sales_qty_total
            vals[25] = sales_total
            data.append(vals)
        data.sort(key=lambda r: r[25], reverse=True)
        sum_a = sales_sum * 0.8
        sum_b = sales_sum * 0.15
        sum_c = sales_sum * 0.05

        csv_file = io.StringIO()
        csv_bytes = io.BytesIO()
        writer = csv.writer(csv_file)
        writer.writerow(headers)

        sales_total = 0
        for vals in data:
            sales_total += vals[25]
            if sum_a:
                if sales_total <= sum_a:
                    vals[6] = 'A'
                else:
                    sales_total = 0
                    sum_a = 0
                    vals[6] = 'A'
            elif sum_b:
                if sales_total <= sum_b:
                    vals[6] = 'B'
                else:
                    sum_b = 0
                    vals[6] = 'B'
            else:
                vals[6] = 'C'

            writer.writerow(vals)
        # data = []
        # sales_sum = 0
        # products = request.env['product.product'].sudo().search(domain)
        # for product in products:
        #     product_available = product._product_available().get(product.id, {})
        #     margin = (1 - (product.standard_price / product.lst_price)) if product.lst_price else 0
        #     vals = [
        #         product.default_code or '',
        #         product.display_name,
        #         product.standard_price,
        #         product.lst_price,
        #         '%.2f%%' % (margin * 100),
        #         product_available.get('qty_available', 0),
        #         '',
        #         product_available.get('incoming_qty', 0),
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         0,
        #         bool(product.route_ids.filtered(lambda r: r.name == 'Dropship')),
        #         product.categ_id.name,
        #         product.seller_ids[:1].name.name or '',
        #     ]
        #
        #     product_sales = StockMove.read_group([
        #         ('product_id', '=', product.id), '|',('picking_id.picking_type_code', '=', 'outgoing'),('picking_id.picking_type_id.is_drop_shipping', '=', True),
        #         ('date', '>=', from_date.strftime('%Y-%m-%d')),
        #         ('date', '<=', today.strftime('%Y-%m-%d')),
        #     ], ['date', 'product_uom_qty', 'qty_done'],
        #         # ], ['date', 'price_subtotal', 'product_uom_qty'],
        #         groupby=['date:month'],
        #         orderby='date ASC', lazy=True)
        #     sales_total = 0
        #     sales_qty_total = 0
        #     for rec in product_sales:
        #         sales_total += (rec.get('product_uom_qty', 0.0) + rec.get('qty_done', 0.0)) * product.lst_price
        #         # sales_total += rec.get('price_subtotal', 0.0)
        #         sales_qty = rec.get('product_uom_qty', 0.0) + rec.get('qty_done', 0.0)
        #         sales_qty_total += sales_qty
        #         vals[domain_dates.get(rec['date:month'])] = sales_qty
        #
        #     sales_sum += sales_total
        #     vals[8] = '%.2f' % (sales_qty_total / 13)
        #     vals[22] = product.reordering_min_qty
        #     vals[23] = product.reordering_max_qty
        #     vals[24] = sales_qty_total
        #     vals[25] = sales_total
        #     data.append(vals)
        #
        # data.sort(key=lambda r: r[25], reverse=True)
        # sum_a = sales_sum * 0.8
        # sum_b = sales_sum * 0.15
        # sum_c = sales_sum * 0.05
        #
        # csv_file = io.StringIO()
        # writer = csv.writer(csv_file)
        # writer.writerow(headers)
        #
        # sales_total = 0
        # for vals in data:
        #     sales_total += vals[25]
        #     if sum_a:
        #         if sales_total <= sum_a:
        #             vals[6] = 'A'
        #         else:
        #             sales_total = 0
        #             sum_a = 0
        #             vals[6] = 'A'
        #     elif sum_b:
        #         if sales_total <= sum_b:
        #             vals[6] = 'B'
        #         else:
        #             sum_b = 0
        #             vals[6] = 'B'
        #     else:
        #         vals[6] = 'C'
        #
        #     writer.writerow(vals)

        response = request.make_response(
            csv_file.getvalue(),
            headers=[
                ('Content-Type', 'application/octet-stream'),
                ('Content-Disposition', 'attachment; filename=purchasing_report.csv;')])

        return response


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
