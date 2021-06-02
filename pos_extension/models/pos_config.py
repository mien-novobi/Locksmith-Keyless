# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    auto_invoice = fields.Boolean(string="Auto Invoicing", default=True)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
