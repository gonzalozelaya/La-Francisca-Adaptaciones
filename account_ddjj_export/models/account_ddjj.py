from odoo import models, fields, api
import base64
from io import StringIO

class AccountDDJJ(models.Model):
    _name = 'account.ddjj'
    _description = 'Modelo para DDJJ de cuentas'

    name = fields.Char(string='Nombre', required=True)
    date_start = fields.Date(string='Fecha Inicio', required=True)
    date_end = fields.Date(string='Fecha Fin', required=True)
    municipalidad = fields.Selection(
        selection=[
            ('jujuy', 'Jujuy'),
            ('salta', 'Salta'),
            ('caba', 'CABA'),
            ('tucuman', 'Tucumán')
        ],
        string='Municipalidad',
        required=True
    )
    apunte_ids = fields.Many2many(
        comodel_name='account.move.line',
        relation='account_ddjj_move_line_rel',
        column1='account_ddjj_id',
        column2='move_line_id',
        string='Apuntes Contables',
        compute='_compute_apunte_ids',
        store=True,)
    
    
    @api.depends('date_range', 'municipalidad')
    def _compute_apunte_ids(self):
        if self.municipalidad == 'Jujuy':
            account_code = '2.1.3.02.150'
        elif self.municipalidad == 'Caba':
            account_code = '2.1.3.02.030'
        elif self.municipalidad == 'Tucuman':
            account_code = '2.1.3.02.310'
        
        AccountMoveLine = self.env['account.move.line']
        # Buscar apuntes contables con el código de cuenta especificado
        account_move_lines = AccountMoveLine.search([('account_id.code', '=', account_code)])
        
        # Asignar los apuntes contables encontrados al campo many2many
        self.apunte_ids = [(6, 0, account_move_lines.ids)]

    def export_txt(self):
        # Crear un buffer en memoria para el contenido del archivo
        output = StringIO()
        
        # Escribir la cabecera del archivo (ajusta según sea necesario)
        output.write("Nombre\tFecha Inicio\tFecha Fin\tMunicipalidad\tCódigo de Cuenta\tFactura\tPago\n")

        for record in self:
            for line in record.apunte_ids:
                invoice = line.move_id.name if line.move_id else ''
                payments = line.payment_id.name if line.payment_id else ''
                output.write(f"{record.name}\t{record.date_range.start}\t{record.date_range.end}\t{record.municipalidad}\t{line.account_id.code}\t{invoice}\t{payments}\n")
        
        # Obtener el contenido del archivo
        file_content = output.getvalue()
        output.close()

        # Codificar el contenido en base64
        file_content_base64 = base64.b64encode(file_content.encode('utf-8')).decode('utf-8')

        # Crear un adjunto en Odoo
        attachment = self.env['ir.attachment'].create({
            'name': 'export_ddjj.txt',
            'type': 'binary',
            'datas': file_content_base64,
            'mimetype': 'text/plain',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
        