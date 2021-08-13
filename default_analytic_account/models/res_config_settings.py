# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    sale_analytic_id = fields.Many2one('account.analytic.account', config_parameter="sale.default_analytic_account_id", string="Default Analytic Account")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
