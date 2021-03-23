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


    def process_ftp_file(self):  # , automatic=False, use_new_cursor=False
        try:
            context = dict(self._context or {})
            FtpConfig = self.env['ftp.configuration'].search([])#.browse([1])#
            if not FtpConfig:
                return False
            for config in FtpConfig:
                try:
                    files = []
                    if  config.protocol == 'sftp':
                        pass
                    elif config.protocol == 'ftp'  :
                        ftp = FTP(config.host)
                        login_status = ftp.login(config.username, config.password)
                        ftp.cwd(config.dest_file_location)
                        processed_file_list = ftp.nlst()
                        ftp.cwd('/')
                        ftp.cwd(config.file_location)
                        file_list = ftp.nlst()
                        for filename in file_list :
                            if filename not in processed_file_list:
                                excel = io.BytesIO()
                                ftp.retrbinary('RETR %s' % filename, excel.write)
                                wb = xlrd.open_workbook(file_contents=excel.getvalue())
                                sheet = wb.sheet_by_index(0)
                                header = sheet.row_values(0)
                                header_ref = header.index('Order ID')
                                header_fees = header.index('Total Fees')
                                SaleOrder = self.env['sale.order']
                                for i in range(1, sheet.nrows):
                                    row = sheet.row_values(i)
                                    order_id = row[header_ref]
                                    if type(order_id) is float:
                                        order_id = int(row[header_ref])
                                    saleorder = SaleOrder.search([
                                        ('client_order_ref', '=', str(order_id)),
                                        ('state', 'not in', ['cancel']),
                                        ('is_commission_updated', '=', False),
                                    ], limit=1)
                                    fee = row[header_fees]
                                    if saleorder and fee != 0.0:
                                        saleorder.write({
                                            'total_fees': fee,
                                            'is_commission_updated': True,
                                        })
                                        self.env.cr.commit()

                                # config.move_file(ftp, config.dest_file_location, file)
                except Exception as e:
                    self.env.cr.rollback()
                    logging.error(e)
                    pass
                finally:
                    if ftp:
                        ftp.quit()

        except Exception as e:
            logging.error(e)
            pass
        return True


    @api.model
    def move_file(self, ftp, moveto_dir, file_tomove):
        """
        param@ ftp: ftp object
        param@ moveto_dir: the dir to move(inside current dir)
        param@ file_tomove: the file which is needed to move
        """
        r = BytesIO()
        ftp.retrbinary('RETR %s'%(file_tomove), r.write)
        file_data =  r.getvalue()
        r.close()
        ftp.cwd('/')
        file_list = ftp.nlst()
        if str(moveto_dir).replace('/','') not in file_list :
            ftp.mkd(moveto_dir)
        ftp.cwd(moveto_dir)
        if file_tomove not in ftp.nlst():
            data = io.BytesIO(file_data)
            ftp.storbinary('STOR %s'%(file_tomove), data)
            # ftp.cwd(config.file_location)
            # ftp.delete(file_tomove)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

