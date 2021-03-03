# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    carrier_account_id = fields.Char('Carrier Account')

    def _get_address(self):
        """
            The compacted method used to return all shipper info
            when called upon.
            method is called to fetch receiver(to customer) info or
            shipper(from company)
        """
        return {
            'name': self.name,
            'company_name': self.parent_id and self.parent_id.name or self.name or '',
            'phone': self.phone or self.mobile or '',
            'address': self.street or '',
            'address1': self.street2 or '',
            'city': self.city or '',
            'state_code': self.state_id and self.state_id.code or '',
            'country_code': self.country_id and self.country_id.code or '',
            'country_name': self.country_id and self.country_id.name or '',
            'zip': self.zip or ''
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

