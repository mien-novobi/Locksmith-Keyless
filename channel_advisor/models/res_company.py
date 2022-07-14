# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging


class ResCompany(models.Model):
    _inherit = "res.company"

    shipping_cost_product_id = fields.Many2one('product.product', string="Shipping Cost Product")
    tax_product_id = fields.Many2one('product.product', string="TotalTaxPrice Product")
    gift_product_id = fields.Many2one('product.product', string="TotalGiftOptionPrice Product")
    addt_cost_product_id = fields.Many2one('product.product', string="AdditionalCostOrDiscount Product")
    insurance_product_id = fields.Many2one('product.product', string="TotalInsurancePrice Product")
    promotion_product_id = fields.Many2one('product.product', string="PromotionAmount Product")

    def action_update_analytic_account(self):
        order_lst = [63942, 63907, 63906, 63905, 63897, 63895, 63882, 63870, 63861, 63860, 63851, 63850, 63841, 63831,
                     63813, 63806, 63800, 63789, 63786, 63775, 63762, 63759, 63758, 63761, 63746, 63743, 63731, 63732,
                     63714, 63705, 63704, 63684, 63676, 63674, 63668, 63660, 63653, 63651, 63652, 63648, 63637, 63605,
                     63602, 63600, 63594, 63562, 63560, 63545, 63546, 63542, 63523, 63521, 63506, 63504, 63498, 63494,
                     63479, 63471, 63454, 63450, 63436, 63429, 63425, 63410, 63400, 63399, 63390, 63389, 63388, 63381,
                     63380, 63369, 63365, 63366, 63362, 63361, 63343, 63339, 63340, 63338, 63335, 63334, 63323, 63301,
                     63303, 63296, 63283, 63282, 63277, 63276, 63275, 63278, 63279, 63256, 63253, 63243, 63237, 63236,
                     63238, 63218, 63206, 63199, 63192, 63184, 63182, 63181, 63163, 63156, 63155, 63154, 63150, 63133,
                     63134, 63118, 63116, 63109, 63098, 63088, 63072, 63071, 63062, 63055, 63054, 63053, 63043, 63032,
                     63033, 63016, 63014, 63007, 63001, 62995, 62973, 62956, 62955, 62943, 62926, 62912, 62889, 62884,
                     62870, 62855, 62836, 62812, 62775, 62770, 62768, 62761, 62756, 62750, 62748, 62747, 62730, 62714,
                     62703, 62699, 62695, 62687, 62683, 62682, 62679, 62678, 62674, 62663, 62653, 62649, 62777, 62634,
                     62621, 62618, 62614, 62603, 62600, 62591, 62592, 62588, 62581, 62582, 62584, 62575, 62568, 62565,
                     62563, 62564, 62558, 62551, 62552, 62548, 62547, 62541, 62539, 62536, 62535, 62527, 62526, 62522,
                     62520, 62518, 62516, 62515, 62508, 62507, 62506, 62505, 62501, 62500, 62495, 62488, 62484, 62483,
                     62476, 62477, 62474, 62473, 62472, 62471, 62468, 62465, 62464, 62463, 62458, 62459, 62460, 62455,
                     62449, 62448, 62440, 62439, 62432, 62433, 62428, 62422, 62419, 62415, 62412, 62411, 62407, 62399,
                     62390, 62395, 62392, 62383, 62380, 62378, 62377, 62376, 62375, 62371, 62370, 62367, 62369, 62368,
                     62362, 62363, 62361, 62360, 62358, 62353, 62350, 62335, 62331, 62330, 62320, 62315, 62316, 62313,
                     62310, 62307, 62304, 62298, 62294, 62293, 62287, 62278, 62276, 62273, 62267, 62261, 62258, 62252,
                     62250, 62247, 62246, 62245, 62238, 62236, 62234, 62229, 62398, 62224, 62222, 62221, 62216, 62212,
                     62211, 62204, 62206, 62205, 62188, 62187, 62186, 62167, 62161, 62154, 62153, 62149, 62140, 62127,
                     62119, 62111, 62092, 62091, 62086, 62083, 62080, 62076, 62073, 62070, 62069, 62062, 62058, 62057,
                     62059, 62052, 62051, 62049, 62044, 62043, 62037, 62036, 62033, 62032, 62027, 62022, 62021, 62016,
                     62014, 62013, 62008, 62002, 61997, 61982, 61981, 61958, 61956, 61957, 61953, 61951, 61950, 61948,
                     61947, 61946, 61944, 61940, 61938, 61937, 61930, 61926, 61925, 61921, 61905, 61898, 61883, 61876,
                     61875, 61872, 61868, 61865, 61861, 61859, 61851, 61832, 61830, 61825, 61824, 61813, 61809, 61806,
                     61802, 61792, 61790, 61788, 61789, 61787, 61786, 61771, 61765, 61758, 61759, 61757, 61755, 61749,
                     61735, 61730, 61726, 61718, 61701, 61692, 61687, 61675, 61670, 61668, 61665, 61662, 61661, 61658,
                     61656, 61646, 61641, 61640, 61622, 61620, 61617, 61616, 61615, 61612, 61611, 61610, 61608, 61586,
                     61581, 61567, 61566, 61564, 61559, 61558, 61541, 65303, 65296, 65210, 65185, 65160, 65051, 64979,
                     64916,
                     64917, 64894, 64849, 64801, 64790, 64787, 64780, 64779, 64753, 64737, 64726, 64708, 64662, 64634,
                     64587, 64577,
                     ]
        # order_lst =[64577,64587]
        sale_order = self.env['sale.order'].browse(order_lst)
        for rec in sale_order:
            logging.info("sale_order")
            logging.info(rec.analytic_account_id.id)
            if rec.analytic_account_id.id == 8:
                rec.write({'analytic_account_id': 2})

            for invoice in rec.invoice_ids:
                logging.info("Invoice")
                logging.info(invoice.invoice_line_ids.analytic_account_id)
                invoice.invoice_line_ids.write({'analytic_account_id': 2})


ResCompany()
