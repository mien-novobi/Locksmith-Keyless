# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockImportLabel(models.TransientModel):
    _name = "stock.import.label"
    _description = "Import Label Line"

    label_lines = fields.One2many('stock.import.label.line', 'label_id', 'Dimension')
    carrier_price = fields.Float('Shipping cost', required=1)

    def import_label(self):
        Picking = self.env['stock.picking'].browse(self._context.get('active_id'))
        if not self.label_lines:
            raise UserError(_('Label not found'))
        for line in self.label_lines:
            if not line.label:
                raise UserError(_('Label not found'))
            Attachment = self.env['ir.attachment'].create({
                'name': line.tracking_number,
                'datas_fname':"%s" % line.tracking_number,
                'datas': line.label,
                'description': 'Shipping Label for %s' % line.tracking_number,
                # 'res_model': Picking._name,
                # 'res_id': Picking.id,
                'type':'binary',
            })
            self.env['picking.dimensions'].create({
                'package_depth' : line.package_length,
                'package_width' :line.package_breadth,
                'package_height' :line.package_height,
                'package_weight' :line.package_weight,
                'package_unit' :line.package_unit,
                'attachment_id' :Attachment.id,
                'tracking_number' :line.tracking_number,
                'is_used' : False,
                'picking_id':Picking.id,
            })
        return Picking.write({'carrier_price':self.carrier_price})


class StockImportLabelLine(models.TransientModel):
    _name = "stock.import.label.line"
    _description = "Import Label Line"

    label_id = fields.Many2one('stock.import.label', 'Label')
    package_length = fields.Integer('Length', required=1)
    package_breadth = fields.Integer('Width', required=1)
    package_height = fields.Integer('Height', required=1)
    package_weight = fields.Float('Weight', required=1)
    package_unit = fields.Selection([('CM','CM'),('IN','Inch')], 'Unit', default='IN', required=1)
    tracking_number = fields.Char('Tracking Number', required=1)
    label = fields.Binary("Label", required=1)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
