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
    apuntes_a_mostrar =  fields.Selection(string='Apuntes a mostrar', selection='_compute_apuntes_a_mostrar')
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
                account_code = ['2.1.3.02.310','2.1.3.02.320']
            
            if account_code:               
                rec.apunte_ids = [Command.clear(), Command.set(self.env['account.move.line'].search([('account_id.code', 'in', account_code),('move_id.state', 'not in', ['draft', 'cancel']),('date', '>=', rec.date_start),('date', '<=', rec.date_end)] ).ids)] 
                # Asignar los apuntes contables encontrados al campo many2many
    
    @api.depends('municipalidad')
    def _compute_apuntes_a_mostrar(self):
        selection = []
        for record in self:
            if record.municipalidad == 'jujuy':
                selection = [('1', 'Todo'),('2', 'Retenciones'), ('3', 'Percepciones')]
            elif record.municipalidad == 'salta':
                selection = [('1', 'Todo'),('2', 'Retenciones'), ('3', 'Percepciones')]
            elif record.municipalidad == 'caba':
                selection =[('1', 'Todo'),('4', 'Retenciones y Percepciones'),('5', 'Notas de crédito')]
            elif record.municipalidad == 'tucuman':
                selection = [('1', 'Todo'),('2', 'Retenciones'), ('3', 'Percepciones')]
        return selection

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
        return exporter.exportToTxt()

        
        
        
class DDJJExport:
    def __init__(self, record):
        self.record = record
    
    def format_line(self, record):
        formatted_lines = []
        
        for apunte in record.apunte_ids:
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            formatted_line = str(tipo_operacion)                                                #Tipo de Operación 1:Retencion/2:Percepción
            formatted_line += '029'                                             #Código de norma
            formatted_line += str(apunte.date.strftime('%d/%m/%Y')).rjust(10)   #Fecha de Retención/Percepción
            formatted_line += str(self.tipoComprobanteOrigen(tipo_operacion,apunte)).rjust(2,'0') #Tipo comprobante de Origen
            formatted_line += str(self.tipoFactura(apunte,tipo_operacion)).rjust(1)                                               #Tipo de operación
            formatted_line += str(comprobante.sequence_number).rjust(16,'0')    #Número de comprobante
            formatted_line += str(comprobante.date.strftime('%d/%m/%Y')).rjust(10,'0')           #Fecha de comprobante
            formatted_line += '{:.2f}'.format(self.montoComprobante(comprobante,tipo_operacion)).replace('.', ',').rjust(16, '0')      #Monto de comprobante
            formatted_line += str(self.buscarNroCertificado(comprobante,53,tipo_operacion)).split('-')[-1].rjust(16,' ')     #Nro de certificado propio
            formatted_line += str(self.tipodeIdentificacion(apunte.partner_id))   #Tipo de identificacion 1:CDI/2:CUIL/3:CUIT
            formatted_line += str(self.nrodeIdentificacion(apunte.partner_id)).ljust(11,'0')
            #Nro de identificacion
            
            formatted_line += str(self.nrodeIdentificacion(apunte.partner_id)).rjust(11,'0')    #Nro de identificacion
            formatted_line += str(self.situacionIb(apunte.partner_id))         #Situacion IB
            formatted_line += str(self.nroIb(apunte.partner_id)).rjust(11,'0')  #Nro IB
            formatted_line += str(self.situacionIva(apunte.partner_id))        #Situacion IVA
            formatted_line += (str(self.razonSocial(apunte.partner_id))[:30] if len(str(self.razonSocial(apunte.partner_id))) > 30 else str(self.razonSocial(apunte.partner_id))).ljust(30, ' ') #Razon social
            formatted_line += '{:.2f}'.format(0).replace('.', ',').rjust(16, '0') #Importe otros conceptos 
            formatted_line += '{:.2f}'.format(self.ImporteIva(apunte,tipo_operacion)).replace('.', ',').rjust(16, '0') #Importe IVA 
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,53,tipo_operacion)).replace('.', ',').rjust(16, '0') #Monto sujeto a retención (Neto) 
            formatted_line += '{:.2f}'.format(self.porcentajeAlicuota(comprobante,53,tipo_operacion)).replace('.', ',').rjust(16, '0') #Alicuota
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,53,tipo_operacion)).replace('.', ',').rjust(16, '0')
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,53,tipo_operacion)).replace('.', ',').rjust(16, '0')
             
            formatted_lines.append(formatted_line)
            
        return "\n".join(formatted_lines)
    #Pendiente
    def format_jujuy(self, record):
        
        return
    #Pendiente
    def format_sicore(seld, record):
        return
    #Pendiente
    def format_tucuman_datos(self, record):
        formatted_lines = []
        for apunte in record.apunte_ids:
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            formatted_line = str(self.tipodeIdentificacionTucuman(apunte.partner_id)).ljust(2,'0')
            formatted_line += str(self.nrodeIdentificacion(apunte.partner_id)).rjust(11,'0')
            formatted_line += (str(self.razonSocial(apunte.partner_id))[:40] if len(str(self.razonSocial(apunte.partner_id))) > 40 else str(self.razonSocial(apunte.partner_id))).ljust(40,' ')
            formatted_line += (str(self.domicilioPartner(apunte.partner_id))[:40] if len(str(self.domicilioPartner(apunte.partner_id))) > 40 else str(self.domicilioPartner(apunte.partner_id))).ljust(40,' ')
            formatted_line += str(00000).ljust(5,'0')
            formatted_line += (str(self.localidadPartner(apunte.partner_id))[:15] if len(str(self.localidadPartner(apunte.partner_id))) > 15 else str(self.localidadPartner(apunte.partner_id))).ljust(15,' ')
            formatted_line += (str(self.provinciaPartner(apunte.partner_id))[:15] if len(str(self.provinciaPartner(apunte.partner_id))) > 15 else str(self.provinciaPartner(apunte.partner_id))).ljust(15,' ')
            formatted_line += str('').ljust(15,' ')
            formatted_line += (str(self.codigoPostalPartner(apunte.partner_id))[:8] if len(str(self.codigoPostalPartner(apunte.partner_id))) > 8 else str(self.codigoPostalPartner(apunte.partner_id))).ljust(8,' ')
            
            formatted_lines.append(formatted_line)
        return "\n".join(formatted_lines)
    
    def format_tucuman_detalle(self, record):
        formatted_lines = []
        for apunte in record.apunte_ids:
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            formatted_line = str(comprobante.date.strftime('%Y/%m/%d')).rjust(10,'0')           #Fecha de comprobante
            formatted_line += str(self.tipodeIdentificacion(apunte.partner_id)).rjust(2,'0')
            formatted_line += str(self.nrodeIdentificacion(apunte.partner_id))[2:10].rjust(11,'0')
            formatted_line += str(self.tipoFactura(apunte,tipo_operacion)).rjust(1)                                               #Tipo de operación
            formatted_line += str(comprobante.sequence_number).rjust(8,'0')
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,54,tipo_operacion)).replace('.', ',').rjust(15, '0')
            formatted_line += '{:.2f}'.format(self.porcentajeAlicuota(comprobante,54,tipo_operacion)).replace('.', ',').rjust(6, '0') #Alicuota
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,54,tipo_operacion)).replace('.', ',').rjust(15, '0')
            
            formatted_lines.append(formatted_line)
        return "\n".join(formatted_lines)
    def exportToTxt(self):
        if self.record.municipalidad == 'caba':
            txt_content = self.format_line(self.record)
                # Codificar el contenido en base64
            file_content_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')

            # Crear un adjunto en Odoo
            attachment = self.record.env['ir.attachment'].create({
                'name': 'RetPer_AGIP.txt',
                'type': 'binary',
                'datas': file_content_base64,
                'mimetype': 'text/plain',
            })
            
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id,
                'target': 'self',
            }
        elif self.record.municipalidad == 'tucuman':
            txt_content = self.format_tucuman_datos(self.record)
            datos_content = self.format_tucuman_detalle(self.record)
            # Codificar el contenido en base64
            txt_content_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
            datos_content_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
            # Crear un adjunto en Odoo
            attachment = self.record.env['ir.attachment'].create({
                'name': 'RETPER.txt',
                'type': 'binary',
                'datas': txt_content_base64,
                'mimetype': 'text/plain',
            })
            attachment2 = self.record.env['ir.attachment'].create({
                'name': 'DATOS.txt',
                'type': 'binary',
                'datas': datos_content_base64,
                'mimetype': 'text/plain',
            })
            return {
                'type': 'ir.actions.act_url',
                'url': '/ddjj/download_files?attachment_id=%s&attachment2_id=%s' % (attachment.id, attachment2.id),
                'target': 'self',
            }
        else: 
            return
    
    def obtenerComprobante(self,apunte,tipo_operacion):
        if tipo_operacion == 1:
            return apunte.move_id.payment_id
        else:
            return apunte.move_id
    
    def fechaComprobante(self,comprobante,tipo_operacion):
        if tipo_operacion == 1:
            return comprobante.date
        else:
            return comprobante.invoice_date
    def montoComprobante(self,comprobante,tipo_operacion):
            if tipo_operacion == 1:
                return comprobante.matched_amount
            else:
                return comprobante.amount_total
    
    def tipoFactura(self,apunte,tipo_operacion):
        if tipo_operacion ==1:
            return ' '
        else:
            factura = apunte.move_id
            return factura.l10n_latam_document_type_id.l10n_ar_letter
    
    def tipoOperacion(self,apunte):
        if apunte.tax_line_id.type_tax_use == 'sale':
            return 2
        else:
            return 1
    def tipoComprobanteOrigen(self,tipo_operacion, apunte):
        if tipo_operacion == 1:
            return '01'
        else:
            factura = apunte.move_id
            if factura.l10n_latam_document_type_id.internal_type == 'Invoice':
                return '01'
            elif factura.l10n_latam_document_type_id.internal_type == 'Debit Notes':
                return '02'
            elif factura.l10n_latam_document_type_id.internal_type == 'Credit Notes':
                return '09'
            else:
                return '00'   
    
    def buscarNroCertificado(self,pago,taxgroup,tipo_operacion):
        cert = ''
        if tipo_operacion == 1:  
            for line in pago.l10n_ar_withholding_line_ids:
                if line.tax_id.tax_group_id.id == taxgroup:
                    cert = line.name
        return cert
    
    def tipodeIdentificacion(self,contacto):
        if contacto.l10n_latam_identification_type_id.name == 'CUIT':
            return 3
        elif contacto.l10n_latam_identification_type_id.name == 'CUIL':
            return 2
        else: 
            return 1
    
    def tipodeIdentificacionTucuman(self, contacto):
        return 80 if contacto.l10n_latam_identification_type_id.name == 'CUIT' else 96    

    def nrodeIdentificacion(self,contacto):
        return contacto.vat
    def situacionIb(self,contacto):
        if contacto.l10n_ar_gross_income_type == 'local':
            return 1
        if contacto.l10n_ar_gross_income_type == 'multilateral':
            return 2
        else :
            return 4
    def nroIb(self,contacto):
        return contacto.l10n_ar_gross_income_number or '0'
    def situacionIva(self,contacto):
        if contacto.l10n_ar_afip_responsibility_type_id.name == 'Responsable Monotributo':
            return 4
        elif contacto.l10n_ar_afip_responsibility_type_id.name == 'IVA Sujeto Exento':
            return 3
        else:
            return 1
    def razonSocial(self,contacto):
        return contacto.name   
    def domicilioPartner(self,contacto):
        return contacto.street
    def localidadPartner(self,contacto):
        return contacto.city
    def provinciaPartner(self,contacto):
        return contacto.state_id.name
    def codigoPostalPartner(self, contacto):
        return contacto.zip
    def ImporteIva(self,apunte,tipo_operacion):
        if tipo_operacion == 1:
            return 0
        else:
            iva_amount = 0.0
            for line in apunte.move_id.line_ids:
                for tax in line.tax_ids:
                    if 'IVA' in tax.name:
                        iva_amount += line.debit - line.credit
            return iva_amount
    def montoSujetoARetencion(self,comprobante,taxgroup,tipo_operacion):
        if tipo_operacion == 1:
            retenido = 0
            for line in comprobante.l10n_ar_withholding_line_ids:
                if line.tax_id.tax_group_id.id == taxgroup:
                    retenido = line.amount
            return retenido
        else:
            return comprobante.amount_untaxed


    def porcentajeAlicuota(self,comprobante,taxgroup,tipo_operacion):
        if tipo_operacion == 1:
            retenido = 0
            base = 0
            for line in comprobante.l10n_ar_withholding_line_ids:
                if line.tax_id.tax_group_id.id == taxgroup:
                    retenido = line.amount
                    base = line.base_amount
            return (retenido / base) * 100
        else:
            return (comprobante.amount_tax / comprobante.amount_untaxed) * 100
        
    def montoRetenido(self,apunte,comprobante,taxgroup,tipo_operacion):
        if tipo_operacion == 1:
            retenido = 0
            for line in comprobante.l10n_ar_withholding_line_ids:
                if line.tax_id.tax_group_id.id == taxgroup:
                    retenido = line.amount
            return retenido
        else:
            if apunte.credit > 0:
                return apunte.credit
            else:
                return apunte.debit