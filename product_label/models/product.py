# -*- coding: utf-8 -*-

import re

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_ca_attribute(self, attrib=None):
        self.ensure_one()
        value = ''
        if attrib and self.description_sale:
            cleaner = re.compile('<.*?>')
            description = self.description_sale.replace('<br />', '<br>')
            attributes = description.split('<br>')
            vals = [attribute.split(':')[-1] for attribute in attributes if re.search(attrib, attribute, re.IGNORECASE)]
            value = vals and cleaner.sub('', vals[0].strip()) or ''
        return value


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def get_ca_attribute(self, attrib=None):
        self.ensure_one()
        value = ''
        if attrib and self.description_sale:
            cleaner = re.compile('<.*?>')
            description = self.description_sale.replace('<br />', '<br>')
            attributes = description.split('<br>')
            vals = [attribute.split(':')[-1] for attribute in attributes if re.search(attrib, attribute, re.IGNORECASE)]
            value = vals and cleaner.sub('', vals[0].strip()) or ''
        return value


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
