# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    markup_rate = fields.Float('Mark Up Rate', default=20.0)
    configuration = fields.Boolean(string="Shipping Configuration")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
