# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ShippingDimensions(models.TransientModel):
    _name = "shipping.dimensions"
    _description = "Store the data of dimension"

    @api.model
    def default_get(self, fields_list):
        defaults = super(ShippingDimensions, self).default_get(fields_list)
        if self.env.context.get('pick_id'):
            picking_id = self.env['stock.picking'].browse(self.env.context['pick_id'])
            if picking_id.picking_type_id and picking_id.picking_type_id.code:
                defaults['picking_type'] = picking_id.picking_type_id.code
        return defaults

    depth = fields.Integer('Package Length')
    width = fields.Integer('Package Width')
    height = fields.Integer('Package Height')
    weight = fields.Float('Package Weight')
    dimension_unit = fields.Selection([('CM','CM'),('IN','Inch')], default='IN', string='Dimension Unit')
    immediate_picking_id = fields.Many2one('stock.immediate.transfer')
    backorder_confirmation_id = fields.Many2one('stock.backorder.confirmation')
    overprocessed_transfer_id = fields.Many2one('stock.overprocessed.transfer')
    picking_type = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal'),
    ])


class StockImmediateTransfer(models.TransientModel):
    _inherit = "stock.immediate.transfer"

    dimension_ids = fields.One2many('shipping.dimensions', 'immediate_picking_id', string='Dimensions')
    picking_type = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal'),
    ], string='Picking Type')

    @api.model
    def default_get(self, fields_list):
        defaults = super(StockImmediateTransfer, self).default_get(fields_list)
        if self.env.context.get('pick_id'):
            picking_id = self.env['stock.picking'].browse(self.env.context['pick_id'])
            if picking_id.picking_type_id and picking_id.picking_type_id.code:
                defaults['picking_type'] = picking_id.picking_type_id.code
        return defaults

    def process(self):
        if self.picking_type == 'outgoing':
            if not self.dimension_ids :
                raise UserError(_('Invalid Data \n Please Update Dimensions'))
            for picking in self.pick_ids:
                picking.update_shipping_dimension(self.dimension_ids)
        res = super(StockImmediateTransfer, self).process()
        base_url = self.env['ir.config_parameter'].get_param(key='web.base.url')
        labe_link = '/web_label/print_label/ir.attachment/datas/datas_fname/'
        url = ''
        atta_ids = ''
        for dimensions in self.pick_ids.mapped('dimension_ids'):
            # for attachment in dimensions:
            if dimensions.attachment_id:
                atta_ids='%s%s,' %(atta_ids, dimensions.attachment_id.id)
        url="%s%s%s" %(base_url,labe_link,atta_ids)
        if url.endswith(','):
            url = url[:-1]
        if url and atta_ids and self.picking_type == 'outgoing':
            return {
                'type': 'ir.actions.act_url',
                'res_model': 'ir.actions.act_url',
                'url': url ,
                'target': 'new',
                'before_action':'close',
                'tag': 'reload',
            }
        return res


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    dimension_ids = fields.One2many('shipping.dimensions', 'backorder_confirmation_id', string='Dimensions')
    picking_type = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal'),
    ], string='Picking Type')

    @api.model
    def default_get(self, fields_list):
        defaults = super(StockBackorderConfirmation, self).default_get(fields_list)
        if self.env.context.get('pick_id'):
            picking_id = self.env['stock.picking'].browse(self.env.context['pick_id'])
            if picking_id.picking_type_id and picking_id.picking_type_id.code:
                defaults['picking_type'] = picking_id.picking_type_id.code
        return defaults

    def process(self):
        if self.picking_type == 'outgoing':
            if not self.dimension_ids :
                raise UserError(_('Invalid Data \n Please Update Dimensions'))
            for picking in self.pick_ids:
                picking.update_shipping_dimension(self.dimension_ids)
        res = super(StockBackorderConfirmation, self).process()
        base_url = self.env['ir.config_parameter'].get_param(key='web.base.url')
        labe_link = '/web_label/print_label/ir.attachment/datas/datas_fname/'
        url = ''
        atta_ids = ''
        for dimensions in self.pick_ids.mapped('dimension_ids'):
            # for attachment in dimensions:
            if dimensions.attachment_id:
                atta_ids='%s%s,' %(atta_ids, dimensions.attachment_id.id)
        url="%s%s%s" %(base_url,labe_link,atta_ids)
        if url.endswith(','):
            url = url[:-1]
        if url and atta_ids and self.picking_type == 'outgoing':
            return {
                'type': 'ir.actions.act_url',
                'res_model': 'ir.actions.act_url',
                'url': url ,
                'target': 'new',
                'before_action':'close',
                'tag': 'reload',
            }
        return res

    def process_cancel_backorder(self):
        if self.picking_type == 'outgoing':
            if not self.dimension_ids :
                raise UserError(_('Invalid Data \n Please Update Dimensions'))
            for picking in self.pick_ids:
                picking.update_shipping_dimension(self.dimension_ids)
        res = super(StockBackorderConfirmation, self).process_cancel_backorder()
        base_url = self.env['ir.config_parameter'].get_param(key='web.base.url')
        labe_link = '/web_label/print_label/ir.attachment/datas/datas_fname/'
        url = ''
        atta_ids = ''
        for dimensions in self.pick_ids.mapped('dimension_ids'):
            # for attachment in dimensions:
            if dimensions.attachment_id:
                atta_ids='%s%s,' %(atta_ids, dimensions.attachment_id.id)
        url="%s%s%s" %(base_url,labe_link,atta_ids)
        if url.endswith(','):
            url = url[:-1]
        if url and atta_ids and self.picking_type == 'outgoing':
            return {
                'type': 'ir.actions.act_url',
                'res_model': 'ir.actions.act_url',
                'url': url ,
                'target': 'new',
                'before_action':'close',
                'tag': 'reload',
            }
        return res


class StockOverProcessedTransfer(models.TransientModel):
    _inherit = "stock.overprocessed.transfer"

    dimension_ids = fields.One2many('shipping.dimensions', 'overprocessed_transfer_id', string='Dimensions')
    picking_type = fields.Selection([
        ('incoming', 'Vendors'),
        ('outgoing', 'Customers'),
        ('internal', 'Internal'),
    ], string='Picking Type')

    @api.model
    def default_get(self, fields_list):
        defaults = super(StockOverProcessedTransfer, self).default_get(fields_list)
        if self.env.context.get('pick_id'):
            picking_id = self.env['stock.picking'].browse(self.env.context['pick_id'])
            if picking_id.picking_type_id and picking_id.picking_type_id.code:
                defaults['picking_type'] = picking_id.picking_type_id.code
        return defaults

    def action_confirm(self):
        self.ensure_one()
        if self.picking_type == 'outgoing':
            if not self.dimension_ids :
                raise UserError(_('Invalid Data \n Please Update Dimensions'))
            if self.picking_id:
                self.picking_id.update_shipping_dimension(self.dimension_ids)
        res = super(StockOverProcessedTransfer, self).action_confirm()
        base_url = self.env['ir.config_parameter'].get_param(key='web.base.url')
        labe_link = '/web_label/print_label/ir.attachment/datas/datas_fname/'
        url = ''
        atta_ids = ''
        for dimensions in self.picking_id.mapped('dimension_ids'):
            # for attachment in dimensions:
            if dimensions.attachment_id:
                atta_ids='%s%s,' %(atta_ids, dimensions.attachment_id.id)
        url="%s%s%s" %(base_url,labe_link,atta_ids)
        if url.endswith(','):
            url = url[:-1]
        if url and atta_ids and self.picking_type == 'outgoing':
            return {
                'type': 'ir.actions.act_url',
                'res_model': 'ir.actions.act_url',
                'url': url ,
                'target': 'new',
                'before_action':'close',
                'tag': 'reload',
            }
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
