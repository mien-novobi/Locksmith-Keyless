# -*- coding: utf-8 -*-

from odoo import api, fields, models, registry, _


class ShipstationLog(models.Model):
    _name = "shipstation.log"
    _order = "id desc"
    _description = "To log Shipstation import/export fails"

    date = fields.Datetime(string="Captured On", index=True, copy=False, default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='User')
    res_model = fields.Char(string='Model')
    res_id = fields.Integer('ERP ID')
    shipstation_id = fields.Integer('Shipstation ID')
    shipstation_account_id = fields.Many2one('shipstation.accounts', string='Shipstation Account')
    message = fields.Text(string='Error Message')
    request = fields.Text(string='Request/Response')
    operation = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('other', 'Other'),
    ], string="Operation", required=True)
    company_id = fields.Many2one('res.company', string="Company")

    @api.model
    def register_log(self, res_model='', res_id=0, shipstation_id=0, operation='import', message='', request='', shipstation_account_id=False):
        new_cr = registry(self.env.cr.dbname).cursor()
        with api.Environment.manage():
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            self = self.with_env(new_env)
            try:
                res = self.create({
                    'user_id': self.env.uid,
                    'res_model': res_model,
                    'res_id': res_id,
                    'shipstation_id': shipstation_id,
                    'operation': operation,
                    'message': message,
                    'request': request,
                })
                store_email = self.env["shipstation.logger.email"].search([
                    ('res_model','=',res_model),('operation','=',operation), ('shipstation_account_id','=',shipstation_account_id)],limit=1)
                if store_email:
                    store_email.template_id.send_mail(res.id)
                else:
                    email = self.env["shipstation.logger.email"].search([('res_model','=',res_model),('operation','=',operation)],limit=1)
                    if email:
                        email.template_id.send_mail(res.id)
            finally:
                self.env.cr.commit()
        return True


class ShipstationLoggerEmail(models.Model):
    _name = "shipstation.logger.email"
    _description = "Email shipstation Log Details"

    shipstation_account_id = fields.Many2one('shipstation.accounts', string='Shipstation Account')
    res_model = fields.Char(string='Model', required= True)
    operation = fields.Selection([
        ('import', 'Import'),
        ('export', 'Export'),
        ('delete', 'Delete'),
        ('other', 'Other'),
    ], string="Operation", required=True)
    template_id = fields.Many2one('mail.template', string='Email Template', domain=[('model_id.model', '=', 'shipstation.log')])


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
