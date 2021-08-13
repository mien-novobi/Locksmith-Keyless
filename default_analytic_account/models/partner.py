# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    default_analytic_account_id = fields.Many2one('account.analytic.account', string="Default Analytic Account")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
