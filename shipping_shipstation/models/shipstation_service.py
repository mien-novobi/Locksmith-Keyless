# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.exceptions import UserError


class ShipstationService(models.Model):
    _name = "shipstation.service"
    _description = "Shipstation Serivce"

    name = fields.Char(string="Name")
    code = fields.Char(string="Code")
    is_domestic = fields.Boolean(string="Is Domestic?")
    is_international = fields.Boolean(string="Is International?")
    carrier_id = fields.Many2one('shipstation.carrier', string="Shipstation Carrier", ondelete="cascade")
    company_id = fields.Many2one('res.company', string="Company")
    account_id = fields.Many2one('shipstation.accounts', string="Account")

    def import_services(self, account=False):
        if not account:
            raise UserError("Shipstation Account not defined to import Warehouse list")
        for carrier in self.env['shipstation.carrier'].search([('account_id', '=', account.id)]):
            response = account._send_request('carriers/listservices?carrierCode=%s' % carrier.code, {})
            for carrier_service in response:
                prepared_vals = {
                    'name': carrier_service.get('name', False),
                    'code': carrier_service.get('code', False),
                    'is_domestic': carrier_service.get('domestic', False),
                    'is_international': carrier_service.get('international', False),
                    'carrier_id': carrier.id,
                    'account_id':account.id,
                    'company_id':account.company_id and account.company_id.id or False,
                }
                existing_carrier = self.search([('code', '=', carrier_service.get('code', False))], limit=1)
                if existing_carrier:
                    existing_carrier.write(prepared_vals)
                else:
                    self.create(prepared_vals)
        return True


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
