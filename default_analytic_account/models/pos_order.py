# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _prepare_invoice_line(self, order_line):
        vals = super(PosOrder, self)._prepare_invoice_line(order_line)
        vals['analytic_account_id'] = order_line.order_id.config_id.default_analytic_account_id.id
        return vals


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
