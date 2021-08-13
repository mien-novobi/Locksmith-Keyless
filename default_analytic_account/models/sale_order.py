# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange('partner_id')
    def _onchange_set_analytic_account(self):
        if self.partner_id.default_analytic_account_id:
            self.analytic_account_id = self.partner_id.default_analytic_account_id.id
        else:
            self.analytic_account_id = int(self.env['ir.config_parameter'].sudo().get_param('sale.default_analytic_account_id', default=0)) or False

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if not res.analytic_account_id and vals.get('is_edi_order', False):
            res._onchange_set_analytic_account()
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
