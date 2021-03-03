# -*- coding: utf-8 -*-

from odoo import api, fields, models


class DistributionCenter(models.Model):
    _name = "ca.distribution.center"
    _description = "Channel Advisor Distribution Centers"

    name = fields.Char(string="Account Name")
    code = fields.Char(string="Code")
    type = fields.Char(string="Type")
    res_id = fields.Char(string="Distribution Center ID")
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

