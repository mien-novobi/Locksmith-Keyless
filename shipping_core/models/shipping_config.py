# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ShippingCarrier(models.Model):
    _name = "shipping.carrier"
    _description = "Details about the carrier"

    name = fields.Char('Shipping Carrier', required=True)
    model_name = fields.Char("Model name", required=True, help="Odoo Model Name")
    active = fields.Boolean('Active', default=True)
    dropoff_type_ids = fields.One2many('shipping.dropoff.type', 'carrier_id', 'Dropoff Type')
    packaging_type_ids = fields.One2many('shipping.packaging.type', 'carrier_id', 'Packaging Type')
    package_detail_ids = fields.One2many('shipping.package.detail', 'carrier_id', 'Package Details')
    physical_packaging_ids = fields.One2many('shipping.physical.packaging', 'carrier_id', 'Physical Packaging')
    freight_ids = fields.One2many('freight.class', 'carrier_id', 'Freight Class')
    company_id = fields.Many2one('res.company', string='Company')

    def copy_data(self, default=None):
        if default is None:
            default = {}
        if 'dropoff_type_ids' not in default:
            default['dropoff_type_ids'] = [(0, 0, line.copy_data()[0]) for line in self.dropoff_type_ids]
        if 'packaging_type_ids' not in default:
            default['packaging_type_ids'] = [(0, 0, line.copy_data()[0]) for line in self.packaging_type_ids]
        if 'package_detail_ids' not in default:
            default['package_detail_ids'] = [(0, 0, line.copy_data()[0]) for line in self.package_detail_ids]
        if 'physical_packaging_ids' not in default:
            default['physical_packaging_ids'] = [(0, 0, line.copy_data()[0]) for line in self.physical_packaging_ids]
        if 'freight_ids' not in default:
            default['freight_ids'] = [(0, 0, line.copy_data()[0]) for line in self.freight_ids]
        return super(ShippingCarrier, self).copy_data(default)


class ShippingDropoffType(models.Model):
    _name = "shipping.dropoff.type"
    _description = "Shipping Dropoff Type"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    carrier_id = fields.Many2one('shipping.carrier', 'Carrier')
    is_default = fields.Boolean('Default')


class ShippingPackagingType(models.Model):
    _name = "shipping.packaging.type"
    _description = "Shipping Packaging Type"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    carrier_id = fields.Many2one('shipping.carrier', 'Carrier')
    is_default = fields.Boolean('Default')


class ShippingPackageDetail(models.Model):
    _name = "shipping.package.detail"
    _description = "Shipping Package Detail"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    carrier_id = fields.Many2one('shipping.carrier', 'Carrier')
    is_default = fields.Boolean('Default')


class ShippingPhysicalPackaging(models.Model):
    _name = "shipping.physical.packaging"
    _description = "Shipping Physical Packaging"

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    carrier_id = fields.Many2one('shipping.carrier', 'Carrier')
    is_default = fields.Boolean('Default')


class FreightClass(models.Model):
    _name = "freight.class"
    _description = "Freight class "

    name = fields.Char(string='Name', required=True)
    carrier_id = fields.Many2one('shipping.carrier', 'Carrier')


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
