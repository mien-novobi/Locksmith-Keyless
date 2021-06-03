# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _process_order(self, order, draft, existing_order):
        order_id = super(PosOrder, self)._process_order(order, draft, existing_order)

        pos_order = self.browse(order_id)
        partner = pos_order.partner_id
        if partner and (partner.mobile or partner.phone) and pos_order.config_id.sms_notify and pos_order.config_id.sms_template_id:
            template = pos_order.config_id.sms_template_id
            message = template._render_template(template.body, 'pos.order', pos_order.ids)[pos_order.id]
            self.env['sms.sms'].sudo().create({
                'body': message,
                'number': partner.mobile or partner.phone,
            }).send()

        return order_id


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
