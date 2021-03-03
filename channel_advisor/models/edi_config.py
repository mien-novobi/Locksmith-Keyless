# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import re
import logging as log
from datetime import datetime, timedelta



class EdiConfig(models.Model):
    _name = 'edi.config'
    _description = 'EDI CONFIGURATION'

    name = fields.Char(string= 'Name')
    username = fields.Char(string= 'Username')
    password = fields.Char(string= 'Password')
    file_path_in = fields.Char(string= 'Path to Read EDI', help= 'Path for 850 EDI')
    file_path_out = fields.Char(string= 'Path to Write EDI', )
    partner_id = fields.Many2one('res.partner', string= 'EDI Partner')



EdiConfig()
