from odoo import models, fields, api, Command, _
import base64
from io import StringIO
from datetime import datetime

class AccountDDJJ(models.Model):
    _name = 'account.ddjj'
    _description = 'Modelo para DDJJ de cuentas'

    name = fields.Char(string='Nombre', required=True)
    date_start = fields.Date(string='Fecha Inicio', required=True,default=lambda self: fields.Date.to_string(datetime(datetime.now().year, datetime.now().month, 1)))
    date_end = fields.Date(string='Fecha Fin', required=True, default=lambda self: fields.Date.today())
    municipalidad = fields.Selection(
        selection=[
            ('sicore', 'SICORE'),
            ('caba', 'AGIP (Caba)'),
            ('jujuy', 'Jujuy'),
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
    
    
    @api.depends('date_start','date_end','municipalidad')
    def _compute_apunte_ids(self):
        for rec in self:
            account_code = False
            if self.municipalidad == 'sicore':
                account_code ='2.1.3.04.020'
            if self.municipalidad == 'jujuy':
                account_code = '2.1.3.02.150'
            elif self.municipalidad == 'caba':
                account_code = '2.1.3.02.030'
            elif self.municipalidad == 'tucuman':
                account_code = '2.1.3.02.310'
            
            if account_code:               
                rec.apunte_ids = [Command.clear(), Command.set(self.env['account.move.line'].search([('account_id.code', '=', account_code),('date', '>=', rec.date_start),('date', '<=', rec.date_end)] ).ids)] 
                # Asignar los apuntes contables encontrados al campo many2many
                

    def export_txt(self):
        # Crear un buffer en memoria para el contenido del archivo
        output = StringIO()
        
        # Escribir la cabecera del archivo (ajusta según sea necesario)
        output.write("Nombre\tFecha Inicio\tFecha Fin\tMunicipalidad\tCódigo de Cuenta\tFactura\tPago\n")

        for record in self:
            for line in record.apunte_ids:
                invoice = line.move_id.name if line.move_id else ''
                payments = line.payment_id.name if line.payment_id else ''
                output.write(f"{record.name}\t{record.date_start}\t{record.date_end}\t{record.municipalidad}\t{line.account_id.code}\t{invoice}\t{payments}\n")
        
        # Obtener el contenido del archivo
        #file_content = output.getvalue()
        #utput.close()
        self.ensure_one()  # Asegurarse de que la acción se ejecuta sobre un solo registro
        exporter = DDJJExport(self)
        txt_content = exporter.export_to_txt()

        # Codificar el contenido en base64
        file_content_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')

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
        
        
class DDJJExport:
    def __init__(self, record):
        self.record = record

    def format_line(self, record):
        for apunte in record.apunte_ids:
            formatted_line = '1'                          #Tipo de Operación 1:Retencion/2:Percepción
            formatted_line += '029'                        #Código de norma
            formatted_line += str(apunte.date).ljust(10)   #Fecha de Retención/Percepción
            formatted_line += 'A'                         #Tipo de operación
            formatted_line += apunte.account_id.code.ljust(20)  # Código de cuenta de longitud 20
            formatted_line += str(apunte.debit).rjust(15, '0')  # Débito de longitud 15, rellenado con ceros
            formatted_line += str(apunte.credit).rjust(15, '0')  # Crédito de longitud 15, rellenado con ceros
        return formatted_line
    
    def format_jujuy(self, record):
        return
    def format_sicore(seld, record):
        return
    def format_tucuman(self, record):
        return

    def export_to_txt(self):
        txt_content = self.format_line(self.record)
        return txt_content