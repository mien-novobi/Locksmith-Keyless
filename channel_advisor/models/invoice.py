# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class AccountMove(models.Model):
    _inherit = "account.move"

    def pay_and_reconcile(self, default_journal):
        RegisterPayment = self.env['account.payment.register']
        for invoice in self:
            if invoice.state != 'posted':
                invoice.post()

            payment_journal = invoice.partner_id.ca_journal_id or default_journal
            if payment_journal:
                RegisterPayment.with_context(
                    active_ids=invoice.ids,
                    active_model="account.move",
                ).create({'journal_id': payment_journal.id}).create_payments()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
