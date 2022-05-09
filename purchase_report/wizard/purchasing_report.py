# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchasingReportFilter(models.TransientModel):
    _name = "purchasing.report.filter"
    _description = "Purchasing Report Filter"

    categ_id = fields.Many2one('product.category', string="Category")
    partner_id = fields.Many2one('res.partner', string="Vendors")
    include_child = fields.Boolean(default=False)

    def action_export(self):
        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/purchase/report/export/%s' % self.id,
            'target': 'new',
        }




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
