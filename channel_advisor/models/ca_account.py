# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ChannelAdvisorAccount(models.Model):
    _name = "ca.account"
    _description = "Channel Advisor Accounts"

    name = fields.Char(string="Account Name")
    company_name = fields.Char(string="Company Name")
    account_id = fields.Char(string="Account ID")
    default_dist_center_id = fields.Char(string="Default Distribution Center ID")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

