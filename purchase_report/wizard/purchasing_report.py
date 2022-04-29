# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PurchasingReportFilter(models.TransientModel):
    _name = "purchasing.report.filter"
    _description = "Purchasing Report Filter"

    categ_id = fields.Many2one('product.category', string="Category")

    def action_export(self):
        return {
            'type' : 'ir.actions.act_url',
            'url': '/web/purchase/report/export?category=%s' % self.categ_id.id,
            'target': 'new',
        }




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
