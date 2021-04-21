# -*- coding: utf-8 -*-

from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from ftplib import FTP
import odoo
import logging
import xlrd
from io import BytesIO
import io



class FtpConfig(models.Model):
    _name = 'ftp.configuration'
    _description = 'FTP Configuration module'

    name = fields.Char(string='Site Name',required=True)
    host = fields.Char(string='Host', required=True)
    username = fields.Char(string='User Name')
    password = fields.Char(string='Password')
    file_location = fields.Char(string='File Location')
    dest_file_location = fields.Char(string='Processed File Location')
    protocol = fields.Selection([('ftp','FTP'), ('sftp','SFTP')], string='Protocol')
    last_imported_date = fields.Datetime(string=" Last Imported Date")


    def check_connection(self):
        login = False
        try:
            result = {}
            login_status = ''
            if self.protocol == 'sftp':
                pass
            else:
                ftp = FTP(self.host)# connect to host, default port on success ->>  <ftplib.FTP instance at 0x02A9B828>
                login_status = ftp.login(self.username, self.password)# user anonymous, passwd anonymous@
                ftp.close()
                if "230" in login_status:
                    login = True
        except Exception as e:  #you can specify type of Exception also
            login = False
        if login:
            raise UserError(_('Login successful!'))
        else:
            raise UserError(_('Login Unsuccessful! May Be Incorrect Settings!'))

    def process_ftp_file(self):
        cr = self.env.cr
        SaleOrder = self.env['sale.order'].sudo()
        ftp_configs = self.search([])

        for config in ftp_configs:
            if config.protocol == 'ftp':
                ftp = False
                try:
                    ftp = FTP(config.host)
                    if ftp.login(config.username, config.password):
                        ftp.cwd(config.file_location)
                        file_list = ftp.nlst()
                        for filename in file_list:
                            try:
                                excel = io.BytesIO()
                                ftp.retrbinary('RETR %s' % filename, excel.write)
                                wb = xlrd.open_workbook(file_contents=excel.getvalue())
                                sheet = wb.sheet_by_index(0)
                                header = sheet.row_values(0)
                                header_ref = header.index('Order ID')
                                header_fees = header.index('Total Fees')
                                for i in range(1, sheet.nrows):
                                    try:
                                        row = sheet.row_values(i)
                                        fee = row[header_fees]
                                        if fee != 0.0:
                                            order_id = row[header_ref]
                                            if type(order_id) is float:
                                                order_id = int(row[header_ref])
                                            saleorder = SaleOrder.search([
                                                ('client_order_ref', '=', str(order_id)),
                                                ('state', 'not in', ['cancel']),
                                                ('is_commission_updated', '=', False),
                                            ], limit=1)
                                            if saleorder:
                                                saleorder.write({
                                                    'total_fees': fee,
                                                    'is_commission_updated': True,
                                                })
                                                cr.commit()
                                    except Exception as e:
                                        cr.rollback()
                                        logging.error(e)

                                # Moving processed files
                                self.move_file(ftp, filename, config.dest_file_location)

                            except Exception as e:
                                logging.error(e)

                except Exception as e:
                    logging.error(e)

                finally:
                    if ftp:
                        ftp.close()

            elif config.protocol == 'sftp':
                pass

        return True

    @api.model
    def move_file(self, ftp, filename, destination):
        try:
            dest_file_path = '%s/%s' % (destination or '', filename)
            if not dest_file_path.startswith('/'):
                dest_file_path = '/' + dest_file_path
            ftp.rename(filename, dest_file_path)
        except Exception as e:
            logging.error(e)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

