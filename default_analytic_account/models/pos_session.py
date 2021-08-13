# -*- coding: utf-8 -*-

from odoo import api, fields, models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _create_account_move(self):
        res = super(PosSession, self)._create_account_move()
        if self.config_id.default_analytic_account_id:
            default_analytic_account_id = self.config_id.default_analytic_account_id.id
            for line in self.move_id.line_ids:
                line.analytic_account_id = default_analytic_account_id

        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
