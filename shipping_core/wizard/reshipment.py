# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

from odoo.tools.float_utils import float_round


class ReshipmentLine(models.TransientModel):
    _name = "reshipment.line"
    _description = "Reshipment Line"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string="Product", required=True, domain="[('id', '=', product_id)]")
    quantity = fields.Float("Quantity", digits="Product Unit of Measure", required=True)
    move_id = fields.Many2one('stock.move', "Move")
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', related='move_id.product_uom')
    wizard_id = fields.Many2one('picking.reshipment', string="Wizard")


class PickingReshipment(models.TransientModel):
    _name = "picking.reshipment"
    _description = "Reshipment"

    picking_id = fields.Many2one('stock.picking')
    reshipment_moves = fields.One2many('reshipment.line', 'wizard_id', 'Moves')

    @api.model
    def default_get(self, fields):
        if len(self.env.context.get('active_ids', list())) > 1:
            raise UserError("You may only return one picking at a time!")
        res = super(PickingReshipment, self).default_get(fields)
        reshipment_moves = []
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        if picking:
            res.update({'picking_id': picking.id})
            if picking.state != 'done':
                raise UserError(_("You may only reship Done pickings"))
            for move in picking.move_lines:
                if move.scrapped:
                    continue

                quantity = move.product_uom_qty
                quantity = float_round(move.product_uom_qty, precision_rounding=move.product_uom.rounding)
                reshipment_moves.append((0, 0, {'product_id': move.product_id.id, 'quantity': quantity, 'move_id': move.id, 'uom_id': move.product_id.uom_id.id}))
            if not reshipment_moves:
                raise UserError(_("No products to reship!"))
            if 'reshipment_moves' in fields:
                res.update({'reshipment_moves': reshipment_moves})
        return res

    def _prepare_move_default_values(self, return_line, new_picking):
        vals = {
            'sale_line_id': False,
            'picking_id': new_picking.id,
            'product_uom_qty': return_line.quantity,
        }
        return vals

    def _create_reshipment(self):
        # create new picking for reshipment
        picking_type_id = self.picking_id.picking_type_id and self.picking_id.picking_type_id.id
        new_picking = self.picking_id.copy({
            'move_lines': [],
            'picking_type_id': picking_type_id,
            'state': 'draft',
            'reshipment': True,
            'origin': _("Reshipment of %s") % self.picking_id.name})
        new_picking.message_post_with_view('mail.message_origin_link',
            values={'self': new_picking, 'origin': self.picking_id},
            subtype_id=self.env.ref('mail.mt_note').id)
        reshipment_line_count = 0
        for reshipment_line in self.reshipment_moves:
            if not reshipment_line.move_id:
                raise UserError(_("You have manually created product lines, please delete them to proceed"))
            # TODO sle: float_is_zero?
            if reshipment_line.quantity:
                reshipment_line_count += 1
                vals = self._prepare_move_default_values(reshipment_line, new_picking)
                r = reshipment_line.move_id.copy(vals)

        if not reshipment_line_count:
            raise UserError(_("Please specify at least one non-zero quantity."))

        new_picking.action_confirm()
        new_picking.action_assign()
        return new_picking.id, picking_type_id

    def create_reshipment(self):
        for wizard in self:
            new_picking_id, pick_type_id = wizard._create_reshipment()
        # Override the context to disable all the potential filters that could have been set previously
        ctx = dict(self.env.context)
        ctx.update({
            'search_default_picking_type_id': pick_type_id,
            'search_default_draft': False,
            'search_default_assigned': False,
            'search_default_confirmed': False,
            'search_default_ready': False,
            'search_default_late': False,
            'search_default_available': False,
        })
        return {
            'name': _('Reshipment'),
            'view_type': 'form',
            'view_mode': 'form,tree,calendar',
            'res_model': 'stock.picking',
            'res_id': new_picking_id,
            'type': 'ir.actions.act_window',
            'context': ctx,
        }


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
