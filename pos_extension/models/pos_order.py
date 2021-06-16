# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    to_sms = fields.Boolean('To SMS')

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['to_sms'] = ui_order.get('to_sms', False)
        return res

    @api.model
    def _process_order(self, order, draft, existing_order):
        order_id = super(PosOrder, self)._process_order(order, draft, existing_order)

        pos_order = self.browse(order_id)
        if pos_order.to_sms:
            partner = pos_order.partner_id
            template = pos_order.config_id.sudo().sms_template_id
            message = template.sudo()._render_template(template.body, 'pos.order', pos_order.ids)[pos_order.id]
            self.env['sms.sms'].sudo().create({
                'body': message,
                'partner_id': partner.id,
                'number': partner.mobile or partner.phone,
            }).send()

        return order_id


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
