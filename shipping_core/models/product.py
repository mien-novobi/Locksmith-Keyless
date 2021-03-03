# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    depth = fields.Integer('Depth')
    height = fields.Integer('Height')
    width = fields.Integer('Width')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
