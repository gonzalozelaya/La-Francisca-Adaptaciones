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
            account_code = []
            if self.municipalidad == 'sicore':
                account_code =['2.1.3.04.020']
            if self.municipalidad == 'jujuy':
                account_code = ['2.1.3.02.150']
            elif self.municipalidad == 'caba':
                account_code = ['2.1.3.02.030','2.1.3.02.040']
            elif self.municipalidad == 'tucuman':
                account_code = ['2.1.3.02.310']
            
            if account_code:               
                rec.apunte_ids = [Command.clear(), Command.set(self.env['account.move.line'].search([('account_id.code', 'in', account_code),('move_id.state', '!=', 'draft'),('date', '>=', rec.date_start),('date', '<=', rec.date_end)] ).ids)] 
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
        #self.ensure_one()  # Asegurarse de que la acción se ejecuta sobre un solo registro
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
        formatted_lines = []
        
        for apunte in record.apunte_ids:
            comprobante = apunte.move_id.payment_id
            formatted_line = '1'                                                #Tipo de Operación 1:Retencion/2:Percepción
            formatted_line += '029'                                             #Código de norma
            formatted_line += str(apunte.date.strftime('%d/%m/%Y')).rjust(10)   #Fecha de Retención/Percepción
            formatted_line += 'A'                                               #Tipo de operación
            formatted_line += str(comprobante.sequence_number).rjust(16,'0')    #Número de comprobante
            formatted_line += str(comprobante.date.strftime('%d/%m/%Y')).rjust(10,'0')           #Fecha de comprobante
            formatted_line += '{:.2f}'.format(comprobante.payment_total).replace('.', ',').rjust(16, '0')      #Monto de comprobante
            formatted_line += str(self.buscar_nro_certificado(comprobante,53)).split('-')[-1].rjust(16,' ')     #Nro de certificado propio
            formatted_line += str(self.tipo_de_identificacion(apunte.partner_id))   #Tipo de identificacion 1:CDI/2:CUIL/3:CUIT
            formatted_line += str(self.nro_de_identificacion(apunte.partner_id)).ljust(11,'0')
            #Nro de identificacion
            
            formatted_line += str(self.nro_de_identificacion(apunte.partner_id)).rjust(11,'0')    #Nro de identificacion
            formatted_line += str(self.situacion_ib(apunte.partner_id))         #Situacion IB
            formatted_line += str(self.nro_ib()(apunte.partner_id)).rjust(11,'0')  #Nro IB
            formatted_line += str(self.situacion_iva(apunte.partner_id))        #Situacion IVA
            formatted_line += str(self.razon_social(apunte.partner_id)).ljust(30,' ') #Razon social
            #formatted_line += '{:.2f}'.format(0).replace('.', ',').rjust(16, '0') #Importe otros conceptos
            #formatted_line += '{:.2f}'.format().replace('.', ',').rjust(16, '0') #Importe IVA            
            formatted_lines.append(formatted_line)
            
        return "\n".join(formatted_lines)
    
    def format_jujuy(self, record):
        return
    def format_sicore(seld, record):
        return
    def format_tucuman(self, record):
        return

    def export_to_txt(self):
        txt_content = self.format_line(self.record)
        return txt_content
    
    
    def buscar_nro_certificado(self,pago,taxgroup):
        cert = ''
        for line in pago.l10n_ar_withholding_line_ids:
            if line.tax_id.tax_group_id.id == taxgroup:
                cert = line.name
        return cert
    
    def tipo_de_identificacion(self,contacto):
        if contacto.l10n_latam_identification_type_id.name == 'CUIT':
            return 3
        elif contacto.l10n_latam_identification_type_id.name == 'CUIL':
            return 2
        else: 
            return 1
    def nro_de_identificacion(self,contacto):
        return contacto.vat
    def situacion_ib(self,contacto):
        if contacto.l10n_ar_gross_income_type == 'local':
            return 1
        if contacto.l10n_ar_gross_income_type == 'multilateral':
            return 2
        else :
            return 4
    def nro_ib(self,contacto):
        return contacto.l10n_ar_gross_income_number or '0'
    def situacion_iva(self,contacto):
        if contacto.l10n_ar_afip_responsibility_type_id.name == 'Responsable Monotributo':
            return 4
        elif contacto.l10n_ar_afip_responsibility_type_id.name == 'IVA Sujeto Exento':
            return 3
        else:
            return 1
    def razon_social(self,contacto):
        return contacto.name