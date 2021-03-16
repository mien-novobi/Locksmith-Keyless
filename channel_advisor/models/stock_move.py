# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if 'state' in vals:
            UpdateQueue = self.env['ca.update.queue'].sudo()
            for move in self.filtered(lambda r: r.product_id.ca_product_type in ['Item', 'Child']):
                if move.state == 'done' or (move.picking_type_id.code == 'outgoing' and move.state == 'assigned'):
                    UpdateQueue.push(move.product_id, 'quantity')
                    for kit in move.product_id.ca_bundle_ids.mapped('bundle_id').filtered(lambda r: r.ca_product_type in ['Item', 'Child']):
                        UpdateQueue.push(kit.product_variant_id, 'quantity')
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

