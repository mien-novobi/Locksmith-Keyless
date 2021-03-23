# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_commission_updated = fields.Boolean(default=False)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
