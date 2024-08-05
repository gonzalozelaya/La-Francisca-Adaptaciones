from odoo import models, fields, api, Command, _
import base64
from io import StringIO
import io
import zipfile
from datetime import datetime, date, timedelta
class AccountDDJJ(models.TransientModel):
    _name = 'account.ddjj'
    _description = 'Modelo para DDJJ de cuentas'
    
    date_start = fields.Date(string='Fecha Inicio', required=True,default=lambda self: fields.Date.to_string(datetime(datetime.now().year, datetime.now().month, 1)))
    date_end = fields.Date(string='Fecha Fin', required=True, default=lambda self: fields.Date.today())
    
    ignore_nc = fields.Boolean(string='Ignorar N/C',help='Marque esta casilla para ignorar las Notas de Crédito.')
    
    municipalidad = fields.Selection(
        selection=[
            ('sicore', 'SICORE'),
            ('caba', 'AGIP (Caba)'),
            ('jujuy', 'Jujuy'),
            ('tucuman', 'Tucumán')
        ],
        string='Municipalidad',
        required=True,
        default='caba'
    )
    apuntes_a_mostrar =  fields.Selection(string='Apuntes a exportar', selection=[
    ('1', 'Retenciones y Percepciones'),
       ('2', 'Retenciones'),
        ('3', 'Percepciones'),
        ('4', 'Notas de credito')
    ], default='1')
    
    apunte_ids = fields.Many2many(
        comodel_name='account.move.line',
        relation='account_ddjj_move_line_rel',
        column1='account_ddjj_id',
        column2='move_line_id',
        string='Apuntes Contables',
        compute='_compute_apunte_ids',
        store=True,)
    
    @api.depends('date_start','date_end','municipalidad','apuntes_a_mostrar')
    def _compute_apunte_ids(self):
        for rec in self:
            account_code = []
            if self.municipalidad == 'sicore':
                account_code =['2.1.3.04.020']
            if self.municipalidad == 'jujuy':
                account_code = ['2.1.3.02.150','2.1.3.02.160']
            elif self.municipalidad == 'caba':
                account_code = ['2.1.3.02.030','2.1.3.02.040']
            elif self.municipalidad == 'tucuman':
                account_code = ['2.1.3.02.310','2.1.3.02.320']
            
            if account_code:               
                domain = [
                ('account_id.code', 'in', account_code),
                ('move_id.state', 'not in', ['draft', 'cancel']),
                ('date', '>=', rec.date_start),
                ('date', '<=', rec.date_end)
                ]
                
                if rec.apuntes_a_mostrar == '1':
                    domain.append(('move_id.move_type', '!=', 'out_refund'))
                elif rec.apuntes_a_mostrar == '2':
                    domain.append(('tax_line_id.type_tax_use', '=', 'none'))
                elif rec.apuntes_a_mostrar == '3':
                    domain.append(('tax_line_id.type_tax_use', '=', 'sale'))
                elif rec.apuntes_a_mostrar == '4':
                    # Buscar las notas de crédito primero en el modelo 'account.move'
                    credit_note_moves = self.env['account.move'].search([('move_type', '=', 'out_refund')])
                    # Filtrar las líneas de apuntes contables que pertenecen a las notas de crédito encontradas
                    domain.append(('move_id', 'in', credit_note_moves.ids))

                account_move_lines = self.env['account.move.line'].search(domain)
                rec.apunte_ids = [Command.clear(), Command.set(account_move_lines.ids)]
                # Asignar los apuntes contables encontrados al campo many2many

    def export_txt(self):
        # Crear un buffer en memoria para el contenido del archivo
        output = StringIO()
        
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
            formatted_line += str(self.buscarNroCertificado(comprobante,53,tipo_operacion)).split('-')[-1].ljust(16,' ')     #Nro de certificado propio
            formatted_line += str(self.tipodeIdentificacion(apunte.partner_id))   #Tipo de identificacion 1:CDI/2:CUIL/3:CUIT
            formatted_line += str(self.nrodeIdentificacion(apunte.partner_id)).rjust(11,'0')    #Nro de identificacion
            formatted_line += str(self.situacionIb(apunte.partner_id))         #Situacion IB
            formatted_line += str(self.nroIb(apunte.partner_id)).rjust(11,'0')  #Nro IB
            formatted_line += str(self.situacionIva(apunte.partner_id))        #Situacion IVA
            formatted_line += (str(self.razonSocial(apunte.partner_id))[:30] if len(str(self.razonSocial(apunte.partner_id))) > 30 else str(self.razonSocial(apunte.partner_id))).ljust(30, ' ') #Razon social
            formatted_line += '{:.2f}'.format(self.importeOtrosConceptos(apunte,tipo_operacion,comprobante,53)).replace('.', ',').rjust(16,'0') #Importe otros conceptos 
            formatted_line += '{:.2f}'.format(self.ImporteIva(apunte,comprobante,tipo_operacion,53)).replace('.', ',').rjust(16,'0') #Importe IVA 
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,53,tipo_operacion)).replace('.', ',').rjust(16, '0') #Monto sujeto a retención (Neto) 
            formatted_line += '{:.2f}'.format(self.porcentajeAlicuota(comprobante,53,tipo_operacion)).replace('.', ',').rjust(5, '0') #Alicuota
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,53,tipo_operacion)).replace('.', ',').rjust(16, '0')
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,53,tipo_operacion)).replace('.', ',').rjust(16, '0')
             
            formatted_lines.append(formatted_line)
            formatted_lines_reversed = list(reversed(formatted_lines))
        formatted_lines.append('')
        return "\n".join(formatted_lines_reversed)
    #Pendiente
    def format_jujuy_ret_dat(self, record):
        formatted_lines = []
        for apunte in record.apunte_ids:
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            formatted_line = str('R-1483').ljust(10,' ')
            formatted_line += str(self.nrodeIdentificacion(apunte.partner_id)).ljust(11,' ')
            formatted_line += str(self.razonSocial(apunte.partner_id)).ljust(60,' ')
            formatted_line += 'S'
            #formatted_line += str(self.localidadPartner(apunte.partner_id)).ljust(20,' ')
            #formatted_line += str(self.domicilioPartner(apunte.partner_id)).ljust(60, ' ')
            #formatted_line += str(self.codigoPostalPartner(apunte.partner_id)).ljust(10, ' ')
            #formatted_line += str(apunte.date.strftime('%Y%m%d')).ljust(8,' ')
            formatted_line += str('2272').ljust(6,' ')
            formatted_line += str(apunte.date.strftime('%Y')).ljust(4,' ')
            formatted_line += str(apunte.date.strftime('%Y%m%d')).ljust(4,' ')
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,54,tipo_operacion)).replace('.','').rjust(12, ' ')
            formatted_line += '{:.2f}'.format(self.porcentajeAlicuota(comprobante,54,tipo_operacion)).replace('.','').rjust(4,'0') #Alicuota
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,54,tipo_operacion)).replace('.','').rjust(10, ' ')
            formatted_line += str('  ')
            formatted_line += str('0').ljust(11,'0')
            formatted_lines.append(formatted_line)
            
        return "\n".join(formatted_lines)
    def format_jujuy_ret_enc(self, record):
        formatted_lines = []
        for apunte in record.apunte_ids:
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            formatted_line = str('NCON').rjust(6,' ')
            formatted_line += str(apunte.date.strftime('%Y')).ljust(4,' ')
            formatted_line += str(self.tipoComprobanteOrigen(tipo_operacion,apunte)).rjust(2,' ')
            formatted_line = str('NSUF').rjust(4,'0')
            formatted_line += str(comprobante.sequence_number).rjust(8,' ')
            formatted_line += str(comprobante.date.strftime('%Y%m%d')).rjust(8,'0')           #Fecha de comprobante
            formatted_line += '{:.2f}'.format(self.montoComprobante(comprobante,tipo_operacion)).replace('.', '').rjust(12,'0')
            formatted_line = str('NSU').rjust(3,'0')
            formatted_line += str(comprobante.date.strftime('%Y%m')).rjust(6,'0')
            formatted_line = str('NSU').rjust(1,'0')
            #formatted_line += str(self.localidadPartner(apunte.partner_id)).ljust(20,' ')
            #formatted_line += str(self.domicilioPartner(apunte.partner_id)).ljust(60, ' ')
            #formatted_line += str(self.codigoPostalPartner(apunte.partner_id)).ljust(10, ' ')
            #formatted_line += str(apunte.date.strftime('%Y%m%d')).ljust(8,' ')
            formatted_lines.append(formatted_line)
            
        return "\n".join(formatted_lines)
    def format_jujuy_perc(self, record):
        formatted_lines = []
        for apunte in record.apunte_ids:
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            formatted_line = str('P-475').ljust(10,' ')
            formatted_line += str(self.nrodeIdentificacion(apunte.partner_id)).ljust(11,' ')
            formatted_line += str(self.razonSocial(apunte.partner_id)).ljust(60,' ')
            formatted_line += 'S'
            formatted_line += ' 6'
            formatted_line += str(self.localidadPartner(apunte.partner_id)).ljust(20,' ')
            formatted_line += str(self.domicilioPartner(apunte.partner_id)).ljust(60, ' ')
            formatted_line += str(self.codigoPostalPartner(apunte.partner_id)).ljust(10, ' ')
            formatted_line += str(apunte.date.strftime('%Y%m%d')).ljust(8,' ')
            formatted_line += str(' ').rjust(6,' ')
            formatted_line += str(apunte.date.strftime('%Y')).ljust(4,' ')
            formatted_line += str(self.tipoComprobanteJujuy(comprobante,tipo_operacion)).rjust(2,'0')
            formatted_line += str('0032').ljust(4,'0')
            formatted_line += str('   ')
            formatted_line += str(comprobante.sequence_number).rjust(8,'0')
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,56,tipo_operacion)).replace('.','').rjust(12, ' ')
            formatted_line += '{:.2f}'.format(self.porcentajeAlicuota(comprobante,56,tipo_operacion)).replace('.','').rjust(4,'0') #Alicuota
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,56,tipo_operacion)).replace('.','').rjust(10, ' ')
            formatted_line += str('  ')
            formatted_line += str('0').ljust(11,'0')
            formatted_lines.append(formatted_line)
            
        return "\n".join(formatted_lines)
    #Pendiente
    def format_sicore(self, record):
        formatted_lines = []
        for apunte in record.apunte_ids:
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            formatted_line = str(self.tipoComprobanteSicore(comprobante,tipo_operacion)).rjust(2,'0')
            formatted_line += str(comprobante.date.strftime('%d/%m/%Y')).ljust(13,' ')
            formatted_line += str(comprobante.sequence_number).rjust(13,'0')
            formatted_line += '{:.2f}'.format(self.montoComprobante(comprobante,tipo_operacion)).replace('.', ',').rjust(16, '0') 
            formatted_line += ' 217'
            formatted_line += str(self.regimenGanancia(comprobante)).rjust(3,' ')
            formatted_line += '1'
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,52,tipo_operacion)).replace('.', ',').rjust(14, '0')
            formatted_line += str(comprobante.date.strftime('%d/%m/%Y')).rjust(10,'0')
            formatted_line += '01 '
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,52,tipo_operacion)).replace('.', ',').rjust(14, '0')
            formatted_line += '000,00'
            formatted_line += str(' ').rjust(10,' ')
            formatted_line += str(self.tipodeIdentificacionSicore(apunte.partner_id)).rjust(2,'0')
            formatted_line += str(self.nrodeIdentificacion(apunte.partner_id)).rjust(11,'0')    #Nro de identificacion
            formatted_line += str(' ').rjust(9,' ')
            formatted_line += str('0').rjust(14,'0')
            formatted_line += str(' ').rjust(30,' ')
            formatted_line += str('0').rjust(24,'0')
            formatted_lines.append(formatted_line)
        formatted_lines.append('')
        return "\n".join(formatted_lines)
    
    #Pendiente
    def format_tucuman_datos(self, record):
        formatted_lines = []
        for apunte in record.apunte_ids:
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
            formatted_line = str(comprobante.date.strftime('%Y%m%d')).rjust(8,'0')           #Fecha de comprobante
            formatted_line += str(self.tipodeIdentificacionTucuman(apunte.partner_id)).ljust(2,'0')
            formatted_line += str(self.nrodeIdentificacion(apunte.partner_id)).rjust(11,'0')
            formatted_line += str(self.tipoComprobanteTucuman(comprobante,tipo_operacion)).rjust(1)
            formatted_line += str(self.tipoFactura(apunte,tipo_operacion)).rjust(2,'0')
            formatted_line += str(1).rjust(4,'0')  
            formatted_line += str(comprobante.sequence_number).rjust(8,'0')
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,55,tipo_operacion)).rjust(15, '0')
            formatted_line += '{:.2f}'.format(self.porcentajeAlicuota(comprobante,55,tipo_operacion)).rjust(6, '0') #Alicuota
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,55,tipo_operacion)).rjust(15, '0')
            
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
            datos_content_base64 = base64.b64encode(datos_content.encode('utf-8')).decode('utf-8')
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
            return self.download_zip(self.record,[attachment.id,attachment2.id])
        elif self.record.municipalidad == 'sicore':
            txt_content = self.format_sicore(self.record)
            # Codificar el contenido en base64
            file_content_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
            # Crear un adjunto en Odoo
            attachment = self.record.env['ir.attachment'].create({
                'name': 'Sicore.txt',
                'type': 'binary',
                'datas': file_content_base64,
                'mimetype': 'text/plain',
            })
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id,
                'target': 'self',
            }
        if self.record.municipalidad == 'jujuy':
            if self.record.apuntes_a_mostrar == '3':
                txt_content = self.format_jujuy_perc(self.record)
                
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
            else:
                txt_content = self.format_jujuy_ret_dat(self.record)
                datos_content = self.format_jujuy_ret_enc(self.record)
                # Codificar el contenido en base64
                txt_content_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
                datos_content_base64 = base64.b64encode(datos_content.encode('utf-8')).decode('utf-8')
                # Crear un adjunto en Odoo
                attachment = self.record.env['ir.attachment'].create({
                    'name': 'JujuyDatos.txt',
                    'type': 'binary',
                    'datas': txt_content_base64,
                    'mimetype': 'text/plain',
                })
                attachment2 = self.record.env['ir.attachment'].create({
                    'name': 'JujuyEnc.txt',
                    'type': 'binary',
                    'datas': datos_content_base64,
                    'mimetype': 'text/plain',
                })
                return self.download_zip(self.record,[attachment.id,attachment2.id])
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
                suma_factura = 0
                for line in comprobante.matched_move_line_ids:
                    if line.full_reconcile_id:
                        related_movements = self.record.env['account.move.line'].search([
                        ('full_reconcile_id', '=', line.full_reconcile_id.id)])
                        credit_sum = sum(line.credit for line in related_movements if line.credit > 0)
                        # Puedes almacenar o usar 'credit_sum' según sea necesario
                        suma_factura += credit_sum
                    elif not line.full_reconcile_id:
                        suma_factura += line.credit
                return suma_factura
            else:
                if (self.record.municipalidad == 'jujuy'):
                    if comprobante.move_type == 'out_refund' or comprobante.move_type == 'in_refund':
                        return -comprobante.amount_total
                    else:
                        return comprobante.amount_total
                else:
                    return comprobante.amount_total
    
    def tipoFactura(self,apunte,tipo_operacion):
        if tipo_operacion ==1:
            return ' '
        else:
            factura = apunte.move_id
            return factura.l10n_latam_document_type_id.l10n_ar_letter
    def tipoComprobanteTucuman(self,comprobante,tipo_operacion):
        if tipo_operacion == 1:
            return 98
        else:
            comp = 1
            if comprobante.move_type == 'out_invoice' or comprobante.move_type == 'in_invoice':
                comp = 1
            if comprobante.move_type == 'out_refund' or comprobante.move_type == 'in_refund':
                comp = 3
            if comprobante.move_type == 'out_receipt' or comprobante.move_type == 'in_receipt':
                comp = 4
            return comp
    def tipoComprobanteJujuy(self,comprobante,tipo_operacion):
        if tipo_operacion == 1:
            return 0
        else:
            comp = 0
            if comprobante.move_type == 'out_invoice' or comprobante.move_type == 'in_invoice':
                comp = 1
            if comprobante.move_type == 'out_refund' or comprobante.move_type == 'in_refund':
                comp = 20
            if comprobante.move_type == 'out_receipt' or comprobante.move_type == 'in_receipt':
                comp = 5
            return comp
    def tipoComprobanteSicore(self,comprobante,tipo_operacion):
        if tipo_operacion == 1:
            return 6
        else:
            comp = 1
            if comprobante.move_type == 'out_invoice' or comprobante.move_type == 'in_invoice':
                comp = 1
            if comprobante.move_type == 'out_refund' or comprobante.move_type == 'in_refund':
                comp = 3
            if comprobante.move_type == 'out_receipt' or comprobante.move_type == 'in_receipt':
                comp = 2
            return comp
    def regimenGanancia(self,comprobante):
        return comprobante.regimen_ganancias_id.codigo_de_regimen
    def tipoOperacion(self,apunte):
        if apunte.tax_line_id.type_tax_use == 'sale':
            return 2
        else:
            return 1
    def tipoComprobanteOrigen(self,tipo_operacion, apunte):
        if tipo_operacion == 1:
            return '3'
        else:
            factura = apunte.move_id
            if factura.l10n_latam_document_type_id.internal_type == 'Invoice':
                return '1'
            elif factura.l10n_latam_document_type_id.internal_type == 'Debit Notes':
                return '2'
            elif factura.l10n_latam_document_type_id.internal_type == 'Credit Notes':
                return '9'
            else:
                return '1'   
    
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

    def tipodeIdentificacionSicore(self, contacto):
        ident = 80
        if contacto.l10n_latam_identification_type_id.name == 'CUIT':
            ident = 80
        elif contacto.l10n_latam_identification_type_id.name == 'CUIL':
            ident = 86
        return ident
    
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
    def ImporteIva(self,apunte,comprobante,tipo_operacion,taxgroup):
        if tipo_operacion == 1:
            return 0
        else:
           iva_amount = self.montoComprobante(comprobante,tipo_operacion)-self.montoSujetoARetencion(comprobante,taxgroup,tipo_operacion) -self.montoRetenido(apunte,comprobante,taxgroup,tipo_operacion)
           return iva_amount
    def importeOtrosConceptos(self,apunte,tipo_operacion,comprobante,taxgroup):
        if tipo_operacion == 1:
            base_retencion = 0
            monto_retencion = 0
            suma_factura = 0
            for retencion in comprobante.l10n_ar_withholding_line_ids:
                if retencion.tax_id.tax_group_id.id == taxgroup:
                    base_retencion= retencion.base_amount
                    monto_retencion += retencion.amount
            for line in comprobante.matched_move_line_ids:
                if line.full_reconcile_id:
                    related_movements = self.record.env['account.move.line'].search([
                    ('full_reconcile_id', '=', line.full_reconcile_id.id)])
                    credit_sum = sum(move.credit for move in related_movements if move.credit > 0)
                    suma_factura += credit_sum
                elif not line.full_reconcile_id:
                    suma_factura += line.credit
            return (suma_factura - base_retencion)
        else:
            return self.montoRetenido(apunte,comprobante,taxgroup,tipo_operacion)
        
            
    def montoSujetoARetencion(self,comprobante,taxgroup,tipo_operacion):
        if tipo_operacion == 1:
            retenido = 0
            for line in comprobante.l10n_ar_withholding_line_ids:
                if line.tax_id.tax_group_id.id == taxgroup:
                    retenido = line.base_amount
            return retenido
        else:
            return comprobante.amount_untaxed

    def porcentajeAlicuota(self,comprobante,taxgroup,tipo_operacion):
        if tipo_operacion == 1:
            retenido = 0
            base = 0
            perc_group = 1
            for line in comprobante.l10n_ar_withholding_line_ids:
                if line.tax_id.tax_group_id.id == taxgroup:
                    retenido = line.amount
                    base = line.base_amount
            return (retenido / base) * 100
        else:
            monto_alicuota = 0
            perc_group = 1
            if taxgroup == 53:
                perc_group = 14
            if taxgroup == 54:
                perc_group = 20
            if taxgroup == 55:
                perc_group = 28
            for line in comprobante.invoice_line_ids:
                for tax in line.tax_ids:
                    if tax.tax_group_id.id == perc_group:
                        monto_alicuota = tax.amount  
            return monto_alicuota
            #return (comprobante.amount_tax / comprobante.amount_untaxed) * 100 #28
        
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
            elif apunte.debit > 0:
                if self.record.municipalidad == 'jujuy':
                    return -apunte.debit
                else: 
                    return apunte.debit
            
            
    def download_zip(self,record, attachment_ids):
            # Obtener los archivos adjuntos
            attachments = record.env['ir.attachment'].sudo().browse(attachment_ids)

            # Crear un buffer en memoria para el archivo ZIP
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as zip_file:
                for attachment in attachments:
                    file_content = base64.b64decode(attachment.datas)
                    zip_file.writestr(attachment.name, file_content)

            # Obtener el contenido del buffer
            buffer.seek(0)
            zip_content = buffer.read()

            zip_content_base64 = base64.b64encode(zip_content).decode('utf-8')

            # Crear un archivo adjunto en Odoo
            attachment = self.record.env['ir.attachment'].create({
                'name': 'DDJJ_Tucuman.zip',
                'type': 'binary',
                'datas': zip_content_base64,
                'mimetype': 'application/zip',
            })

            # Generar una URL para descargar el archivo
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s?download=true' % attachment.id,
                'target': 'self',
            }