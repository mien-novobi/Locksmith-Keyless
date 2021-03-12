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
                    if not UpdateQueue.search([('update_type', '=', 'quantity'), ('product_id', '=', move.product_id.id)]):
                        UpdateQueue.create({
                            'update_type': 'quantity',
                            'product_id': move.product_id.id,
                        })
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

