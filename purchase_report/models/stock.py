# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _



_logger = logging.getLogger(__name__)


class StockPicking(models.Model):
    _inherit = "stock.picking.type"

    is_drop_shipping = fields.Boolean('Is dropship')
