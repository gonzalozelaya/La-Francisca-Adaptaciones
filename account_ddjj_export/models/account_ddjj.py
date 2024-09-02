from odoo import models, fields, api, Command, _
import base64
from io import StringIO,BytesIO
import io
import zipfile
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
import locale
import re
import unicodedata
import xlsxwriter
from odoo.exceptions import UserError

class AccountDDJJ(models.TransientModel):

    tax_group_id_ret_agip = fields.Many2one(
        'account.tax.group', 
        string='Grupo Retenciones AGIP',
        help="Grupo de impuestos de la retención AGIP"
    )
    
    account_id_ret_agip = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Retenciones AGIP',
        help="Plan de cuentas de la retención AGIP"
    )
    
    tax_group_id_perc_agip = fields.Many2one(
        'account.tax.group', 
        string='Grupo Percepciones AGIP',
        help="Grupo de impuestos de la percepción AGIP"
    )
    
    account_id_perc_agip = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Percepciones AGIP',
        help="Plan de cuentas de la percepción AGIP"
    )
    tax_group_id_ret_jujuy = fields.Many2one(
        'account.tax.group', 
        string='Grupo Retenciones AGIP',
        help="Grupo de impuestos de la retención AGIP"
    )
    
    account_id_ret_jujuy = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Retenciones AGIP',
        help="Plan de cuentas de la retención AGIP"
    )
    
    tax_group_id_perc_jujuy = fields.Many2one(
        'account.tax.group', 
        string='Grupo Percepciones AGIP',
        help="Grupo de impuestos de la percepción AGIP"
    )
    
    account_id_perc_jujuy = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Percepciones AGIP',
        help="Plan de cuentas de la percepción AGIP"
    )
    tax_group_id_ret_tucuman = fields.Many2one(
        'account.tax.group', 
        string='Grupo Retenciones AGIP',
        help="Grupo de impuestos de la retención AGIP"
    )
    
    account_id_ret_tucuman = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Retenciones AGIP',
        help="Plan de cuentas de la retención AGIP"
    )
    
    tax_group_id_perc_tucuman = fields.Many2one(
        'account.tax.group', 
        string='Grupo Percepciones AGIP',
        help="Grupo de impuestos de la percepción AGIP"
    )
    
    account_id_perc_tucuman = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Percepciones AGIP',
        help="Plan de cuentas de la percepción AGIP"
    )
    tax_group_id_ret_sicore = fields.Many2one(
        'account.tax.group', 
        string='Grupo Retenciones AGIP',
        help="Grupo de impuestos de la retención AGIP"
    )
    
    account_id_ret_sicore = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Retenciones AGIP',
        help="Plan de cuentas de la retención AGIP"
    )

    @api.model
    def default_get(self, fields):
        res = super(AccountDDJJ, self).default_get(fields)
        ICP = self.env['ir.config_parameter'].sudo()
        
        res.update({
            'tax_group_id_ret_agip': int(ICP.get_param('account_ddjj_settings.tax_group_id_ret_agip', default=0)),
            'account_id_ret_agip': int(ICP.get_param('account_ddjj_settings.account_id_ret_agip', default=0)),
            'tax_group_id_perc_agip': int(ICP.get_param('account_ddjj_settings.tax_group_id_perc_agip', default=0)),
            'account_id_perc_agip': int(ICP.get_param('account_ddjj_settings.account_id_perc_agip', default=0)),
            'tax_group_id_ret_jujuy': int(ICP.get_param('account_ddjj_settings.tax_group_id_ret_jujuy', default=0)),
            'account_id_ret_jujuy': int(ICP.get_param('account_ddjj_settings.account_id_ret_jujuy', default=0)),
            'tax_group_id_perc_jujuy': int(ICP.get_param('account_ddjj_settings.tax_group_id_perc_jujuy', default=0)),
            'account_id_perc_jujuy': int(ICP.get_param('account_ddjj_settings.account_id_perc_jujuy', default=0)),
            'tax_group_id_ret_tucuman': int(ICP.get_param('account_ddjj_settings.tax_group_id_ret_tucuman', default=0)),
            'account_id_ret_tucuman': int(ICP.get_param('account_ddjj_settings.account_id_ret_tucuman', default=0)),
            'tax_group_id_perc_tucuman': int(ICP.get_param('account_ddjj_settings.tax_group_id_perc_tucuman', default=0)),
            'account_id_perc_tucuman': int(ICP.get_param('account_ddjj_settings.account_id_perc_tucuman', default=0)),
            'tax_group_id_ret_sicore': int(ICP.get_param('account_ddjj_settings.tax_group_id_ret_sicore', default=0)),
            'account_id_ret_sicore': int(ICP.get_param('account_ddjj_settings.account_id_ret_sicore', default=0)),
        })
        
        return res
    
    
    _name = 'account.ddjj'
    _description = 'Modelo para DDJJ de cuentas'
    
    date_start = fields.Date(
        string='Fecha Inicio', 
        required=True,
        default=lambda self: fields.Date.to_string(
            datetime.now().replace(day=1) - relativedelta(months=1)
        )
    )
    
    date_end = fields.Date(
        string='Fecha Fin', 
        required=True,
        default=lambda self: fields.Date.to_string(
            datetime.now().replace(day=1) - timedelta(days=1)
        )
    )
    
    ignore_nc = fields.Boolean(string='Ignorar N/C',help='Marque esta casilla para ignorar las Notas de Crédito.')
    
    municipalidad = fields.Selection(
        selection=[
            ('todo', 'Salta'),
            ('iva', 'IVA'),
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
    ], default='1',required=True)

    apuntes_a_mostrar_iva = fields.Selection(string ='Tipo',selection =[
        ('1','Compras'),
        ('2','Ventas')], default = '1')
    
    apunte_ids = fields.Many2many(
        comodel_name='account.move.line',
        relation='account_ddjj_move_line_rel',
        column1='account_ddjj_id',
        column2='move_line_id',
        string='Apuntes Contables',
        compute='_compute_apunte_ids')
    
    move_ids = fields.Many2many(
        comodel_name='account.move',
        relation='account_ddjj_move_rel',
        column1='account_ddjj_id',
        column2='move_id', string='Facturas y Notas de Crédito',compute='_compute_apunte_ids')
    
    @api.depends('date_start','date_end','municipalidad','apuntes_a_mostrar','ignore_nc')
    def _compute_apunte_ids(self):
        for rec in self:
            account_code = []
            if self.municipalidad == 'sicore':
                account_code =[self.account_id_ret_sicore.code]
            if self.municipalidad == 'jujuy':
                account_code = [self.account_id_ret_jujuy.code,self.account_id_perc_jujuy.code]
            elif self.municipalidad == 'caba':
                account_code = [self.account_id_ret_agip.code,self.account_id_perc_agip.code]
            elif self.municipalidad == 'tucuman':
                account_code = [self.account_id_ret_tucuman.code,self.account_id_perc_tucuman.code]
            
            if account_code:               
                domain = [
                ('account_id.code', 'in', account_code),
                ('move_id.state', 'not in', ['draft', 'cancel']),
                ('date', '>=', rec.date_start),
                ('date', '<=', rec.date_end)
                ]
                
                if rec.ignore_nc:
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
                rec.move_ids = [Command.clear()]
                # Asignar los apuntes contables encontrados al campo many2many
            elif rec.municipalidad == 'todo':
                domain = [
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('state', 'not in', ['draft', 'cancel']),
                    ('date', '>=', rec.date_start),
                    ('date', '<=', rec.date_end),
                    ('l10n_latam_document_type_id', '!=', False)
                ]
                moves = self.env['account.move'].search(domain)
                rec.move_ids = [Command.clear(), Command.set(moves.ids)]
                rec.apunte_ids = [Command.clear()]
            elif rec.municipalidad == 'iva':
                domain = [
                    ('move_type', 'in', ['in_invoice', 'in_refund']),
                    ('state', 'not in', ['draft', 'cancel']),
                    ('date', '>=', rec.date_start),
                    ('date', '<=', rec.date_end),
                    ('l10n_latam_document_type_id', '!=', False)
                ]
                moves = self.env['account.move'].search(domain)
                rec.move_ids = [Command.clear(), Command.set(moves.ids)]
                rec.apunte_ids = [Command.clear()]

    def export_txt(self):
        # Crear un buffer en memoria para el contenido del archivo
        output = StringIO()
        
        # Obtener el contenido del archivo
        #file_content = output.getvalue()
        #utput.close()
        #self.ensure_one()  # Asegurarse de que la acción se ejecuta sobre un solo registro
        exporter = DDJJExport(self)
        return exporter.exportToTxt()

    
    def generate_excel(self):
        exporter = DDJJExport(self)
        return exporter.generate_excel_report()
        
    def get_month_name_or_date_range(self):
        self.ensure_one()
        if not self.date_start or not self.date_end:
            return ''

        # Convertir a objetos datetime para comparar
        start_date = fields.Date.from_string(self.date_start)
        end_date = fields.Date.from_string(self.date_end)

        # Guardar la localización actual
        current_locale = locale.getlocale(locale.LC_TIME)
        try:
            # Cambiar temporalmente la localización a español
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Ajusta según la localización disponible en tu servidor

            # Comparar si están en el mismo mes y año
            if start_date.month == end_date.month and start_date.year == end_date.year:
                # Devolver el nombre del mes en español
                result = start_date.strftime('%B %Y').capitalize()  # Ejemplo: 'Marzo 2024'
            else:
                # Devolver el rango de fechas en español
                result = f"{start_date.strftime('%d %b %Y')} - {end_date.strftime('%d %b %Y')}"
        finally:
            # Restaurar la localización original
            locale.setlocale(locale.LC_TIME, current_locale)

        return result
class DDJJExport:
    def __init__(self, record):
        self.record = record

    def format_iva_compras_cabecera(self,record):
        formatted_lines = []
        for apunte in record.move_ids:
            tipo_operacion = 2
            comprobante = apunte
            format_line = str(comprobante.date.strftime('%Y%m%d')).rjust(8,'0')           #Fecha de comprobante
            format_line += str(self.tipoDocumentoIVA(comprobante)).rjust(3,'0')
            format_line += str(self.puntoDeVentaFactura(comprobante)).rjust(5,'0')
            format_line += str(comprobante.sequence_number).rjust(20,'0')
            format_line += str(' ').rjust(16,' ')
            format_line +='80'
            format_line += str(self.nrodeIdentificacion(comprobante.partner_id)).rjust(20,'0')
            format_line += (str(self.razonSocial(comprobante.partner_id))[:30] if len(str(self.razonSocial(comprobante.partner_id))) > 30 else str(self.razonSocial(comprobante.partner_id))).ljust(30,' ')
            format_line += '{:.2f}'.format(self.montoComprobante(comprobante,2)).replace('.', '').rjust(15, '0')
            format_line += '{:.2f}'.format(self.IvaNoGravado(comprobante)).replace('.','').rjust(15,'0') #Conceptos que no integran el neto gravado - Pendiente
            format_line += '{:.2f}'.format(00000).replace('.','').rjust(15,'0') #Operaciones exentas
            format_line += '{:.2f}'.format(self.impuestoPercepcionesIVA(comprobante)).replace('.', '').rjust(15,'0')
            format_line += '{:.2f}'.format(00000).replace('.','').rjust(15,'0') #Percepciones a otros impuestos nacionales
            format_line += '{:.2f}'.format(self.IIBBIVA(comprobante)).replace('.', '').rjust(15,'0')
            format_line += '{:.2f}'.format(self.impuestosMunicipales(comprobante)).replace('.', '').rjust(15,'0')
            format_line += '{:.2f}'.format(self.impuestosInternos(comprobante)).replace('.', '').rjust(15,'0')
            format_line +='PES'
            format_line +='0001000000'
            format_line += str(self.cantidadAlicuotasIVA(comprobante)).rjust(1,'0')
            format_line += ' '
            format_line += '{:.2f}'.format(self.creditoFiscalComputable(comprobante)).replace('.', '').rjust(15,'0')
            format_line += '{:.2f}'.format(00000).replace('.','').rjust(15,'0') #Otros tributos
            format_line += '{:.2f}'.format(00000).replace('.','').rjust(11,'0') #CUIT del emisor
            format_line += str(' ').rjust(30,' ')
            format_line += '{:.2f}'.format(00000).replace('.','').rjust(15,'0')
            formatted_lines.append(format_line)
        formatted_lines.append('')
        return "\n".join(formatted_lines)

    def format_iva_compras_alicuota_(self,record):
        formatted_lines = []
        for apunte in record.move_ids:
            tipo_operacion = 2
            comprobante = apunte
            for line in apunte.line_ids:
                if line.tax_group_id.l10n_ar_vat_afip_code:
                    format_line = str(self.tipoDocumentoIVA(comprobante)).rjust(3,'0')
                    format_line += str(self.puntoDeVentaFactura(comprobante)).rjust(5,'0')
                    format_line += str(comprobante.sequence_number).rjust(20,'0')
                    format_line +='80'
                    format_line += str(self.nrodeIdentificacion(comprobante.partner_id)).rjust(20,'0')
                    format_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,6,tipo_operacion)).replace('.','').rjust(15,'0')
                    format_line += str(self.alicuotaDelIVA(line.tax_group_id)).rjust(4,'0')
                    format_line += '{:.2f}'.format(line.debit).replace('.','').rjust(15,'0')
                    formatted_lines.append(format_line)
        formatted_lines.append('')
        return "\r\n".join(formatted_lines)

    def alicuotaDelIVA(self, impuesto):
        return impuesto.l10n_ar_vat_afip_code

    def tipoDocumentoIVA(self,comprobante):
        return comprobante.l10n_latam_document_type_id.code
    def puntoDeVentaFactura(self,comprobante):
        return comprobante.l10n_latam_document_number[:5]
    def impuestoPercepcionesIVA(self,comprobante):
        sum = 0
        for line in comprobante.line_ids:
            if line.tax_group_id.l10n_ar_tribute_afip_code =='06':
                sum += line.debit
        return sum

    def IvaNoGravado(self,comprobante):
        sum = 0
        for line in comprobante.line_ids:
            if line.tax_group_id.id == 7:
                sum += line.debit
                sum += line.credit
        return sum
    def IIBBIVA(self, comprobante):
        sum = 0
        for line in comprobante.line_ids:
            if line.tax_group_id.l10n_ar_tribute_afip_code == '07':
                sum += line.debit
        return sum
    def impuestosInternos(self,comprobante):
        sum = 0
        for line in comprobante.line_ids:
            if line.tax_group_id.l10n_ar_tribute_afip_code == '04':
                sum += line.debit
        return sum

    def impuestosMunicipales(self,comprobante):
        sum = 0
        for line in comprobante.line_ids:
            if line.tax_group_id.l10n_ar_tribute_afip_code == '08':
                sum += line.debit
        return sum
    def cantidadAlicuotasIVA(self,comprobante):
        sum=0
        for line in comprobante.line_ids:
            if line.tax_group_id.l10n_ar_vat_afip_code in ['3','4','5','6','7','8','9']:
                sum += 1
        return sum
    def creditoFiscalComputable(self,comprobante):
        sum=0
        for line in comprobante.line_ids:
            if line.tax_group_id.l10n_ar_vat_afip_code in ['3','4','5','6','7','8','9']:
                sum += line.debit
        return sum

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
            formatted_line += self.AgipSequenceNumber(comprobante,tipo_operacion)
            #formatted_line += str(comprobante.sequence_number).rjust(16,'0')    #Número de comprobante
            formatted_line += str(comprobante.date.strftime('%d/%m/%Y')).rjust(10,'0')           #Fecha de comprobante
            formatted_line += '{:.2f}'.format(self.montoComprobante(comprobante,tipo_operacion)).replace('.', ',').rjust(16, '0')      #Monto de comprobante
            formatted_line += str(self.buscarNroCertificado(comprobante,record.tax_group_id_ret_agip,tipo_operacion)).split('-')[-1].ljust(16,' ')     #Nro de certificado propio
            formatted_line += str(self.tipodeIdentificacion(apunte.partner_id))   #Tipo de identificacion 1:CDI/2:CUIL/3:CUIT
            formatted_line += str(self.nrodeIdentificacion(apunte.partner_id)).rjust(11,'0')    #Nro de identificacion
            formatted_line += str(self.situacionIb(apunte.partner_id))         #Situacion IB
            formatted_line += str(self.nroIb(apunte.partner_id)).rjust(11,'0')  #Nro IB
            formatted_line += str(self.situacionIva(apunte.partner_id))        #Situacion IVA
            formatted_line += (str(self.razonSocial(apunte.partner_id))[:30] if len(str(self.razonSocial(apunte.partner_id))) > 30 else str(self.razonSocial(apunte.partner_id))).ljust(30, ' ') #Razon social
            formatted_line += '{:.2f}'.format(self.importeOtrosConceptos(apunte,tipo_operacion,comprobante,self.record.tax_group_id_ret_agip)).replace('.', ',').rjust(16,'0') #Importe otros conceptos 
            formatted_line += '{:.2f}'.format(self.ImporteIva(apunte,comprobante,tipo_operacion,self.record.tax_group_id_ret_agip)).replace('.', ',').rjust(16,'0') #Importe IVA 
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,self.record.tax_group_id_ret_agip,tipo_operacion)).replace('.', ',').rjust(16, '0') #Monto sujeto a retención (Neto) 
            formatted_line += '{:.2f}'.format(self.porcentajeAlicuota(comprobante,self.record.tax_group_id_ret_agip,self.record.tax_group_id_perc_agip,tipo_operacion)).replace('.', ',').rjust(5, '0') #Alicuota
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,self.record.tax_group_id_ret_agip,tipo_operacion)).replace('.', ',').rjust(16, '0')
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,self.record.tax_group_id_ret_agip,tipo_operacion)).replace('.', ',').rjust(16, '0')
             
            formatted_lines.append(formatted_line)
            formatted_lines_reversed = list(reversed(formatted_lines))
        formatted_lines.append('')
        return "\n".join(formatted_lines_reversed)



    def format_line_credit(self, record):
        formatted_lines = []
        for apunte in record.apunte_ids:
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            formatted_line = str(tipo_operacion)                                                #Tipo de Operación 1:Retencion/2:Percepción
            formatted_line += '0060'
            formatted_line += str(comprobante.sequence_number).rjust(8,'0')    #Número de comprobante
            formatted_line += str(apunte.date.strftime('%d/%m/%Y')).rjust(10)   #Fecha de Retención/Percepción
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,self.record.tax_group_id_ret_agip,tipo_operacion)).replace('.', ',').rjust(16, '0') #Monto sujeto a retención (Neto) 
            formatted_line += '                '
            formatted_line += str(self.tipoComprobanteOrigen(tipo_operacion,apunte)).rjust(2,'0')
            formatted_line += str(self.tipoFactura(apunte,tipo_operacion)).rjust(1) #Tipo de operación
            formatted_line += '00000060'
            formatted_line += str(comprobante.reversed_entry_id.sequence_number).rjust(8,'0')    #Número de comprobante
            formatted_line += str(comprobante.partner_id.vat).rjust(11,'0')
            formatted_line += '029'
            formatted_line += str(comprobante.reversed_entry_id.date.strftime('%d/%m/%Y')).rjust(10)
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante.reversed_entry_id,self.record.tax_group_id_ret_agip,tipo_operacion)).replace('.', ',').rjust(16, '0')
            formatted_line += '{:.2f}'.format(self.porcentajeAlicuota(comprobante.reversed_entry_id,self.record.tax_group_id_ret_agip,self.record.tax_group_id_perc_agip,tipo_operacion)).replace('.', ',').rjust(5, '0') #Alicuota
             
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
            formatted_line += str(self.extract_last_four_digits(self.buscarNroCertificado(comprobante,self.record.tax_group_id_ret_jujuy,tipo_operacion))).rjust(6,' ')
            formatted_line += str(apunte.date.strftime('%Y')).ljust(4,' ')
            formatted_line += str(comprobante.date.strftime('%Y%m%d')).ljust(8,' ')
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,self.record.tax_group_id_ret_jujuy,tipo_operacion)).replace('.','').rjust(12, ' ')
            formatted_line += '{:.2f}'.format(self.porcentajeAlicuota(comprobante,self.record.tax_group_id_ret_jujuy,self.record.tax_group_id_perc_jujuy,tipo_operacion)).replace('.','').rjust(4,' ') #Alicuota
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,self.record.tax_group_id_ret_jujuy,tipo_operacion)).replace('.','').rjust(10, ' ')
            formatted_line += str('0')
            formatted_line += str(self.cantidadFacturas(comprobante)).rjust(4,' ')
            formatted_line += str(self.nroSucursalProveedor(comprobante)).rjust(2,' ')
            formatted_line += str(' ')
            formatted_line += str(self.nroIb(apunte.partner_id)).rjust(11,' ')
            #formatted_line += str('')
            formatted_line += str(apunte.date.strftime('%Y%m')).ljust(6,' ')
            formatted_line += str('0')
            formatted_lines.append(formatted_line)
        return "\n".join(formatted_lines)
    
    def format_jujuy_ret_detalle(self, record):
        formatted_lines = []
        for apunte in record.apunte_ids:
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            reconcile_id = False
            for line in comprobante.matched_move_line_ids:
                factura = line
                comprobante_factura = self.obtenerComprobante(factura,2)
                tipo_operacion = self.tipoOperacion(factura)
                formatted_line = str(self.extract_last_four_digits(self.buscarNroCertificado(comprobante,record.tax_group_id_ret_jujuy,1))).rjust(6,' ')
                formatted_line += str(factura.date.strftime('%Y')).ljust(4,' ')
                formatted_line +=' 1' #Letra de factura(pendiente)
                formatted_line += str(self.nroSucursalProveedor(comprobante)).rjust(4,' ')
                formatted_line += str(comprobante_factura.sequence_number).rjust(8,' ')
                formatted_line += str(comprobante_factura.date.strftime('%Y%m%d')).rjust(8,'0')           #Fecha de comprobante
                formatted_line += '{:.2f}'.format(self.montoComprobante(comprobante_factura,2)).replace('.', '').rjust(12,'0')
                formatted_line += str(self.nroSucursalProveedor(comprobante)).rjust(3,'0')
                formatted_line += str(comprobante_factura.date.strftime('%Y%m')).rjust(6,'0')
                formatted_line += '0'
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
            formatted_line += str('0060').ljust(4,'0')
            formatted_line += str('   ')
            formatted_line += str(comprobante.sequence_number).rjust(8,'0')
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,self.record.tax_group_id_ret_jujuy,tipo_operacion)).replace('.','').rjust(12, ' ')
            formatted_line += '{:.2f}'.format(self.porcentajeAlicuota(comprobante,self.record.tax_group_id_ret_jujuy,self.record.tax_group_id_perc_jujuy,tipo_operacion)).replace('.','').rjust(4,'0') #Alicuota
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,self.record.tax_group_id_ret_jujuy,tipo_operacion)).replace('.','').rjust(10, ' ')
            formatted_line += str('    ')
            formatted_line += str('0').ljust(11,'0')
            formatted_lines.append(formatted_line)
        formatted_lines_reversed = list(reversed(formatted_lines))
        return "\n".join(formatted_lines_reversed)
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
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,self.record.tax_group_id_ret_sicore,tipo_operacion)).replace('.', ',').rjust(14, '0')
            formatted_line += str(comprobante.date.strftime('%d/%m/%Y')).rjust(10,'0')
            formatted_line += '01 '
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,self.record.tax_group_id_ret_sicore,tipo_operacion)).replace('.', ',').rjust(14, '0')
            formatted_line += '000,00'
            formatted_line += str(' ').rjust(10,' ')
            formatted_line += str(self.tipodeIdentificacionSicore(apunte.partner_id)).rjust(2,'0')
            formatted_line += str(self.nrodeIdentificacion(apunte.partner_id)).rjust(11,'0')    #Nro de identificacion
            formatted_line += str(' ').rjust(9,' ')
            formatted_line += str('0').rjust(14,'0')
            formatted_line += str(' ').rjust(30,' ')
            formatted_line += '00000000000000000000000 '
            formatted_lines.append(formatted_line)
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
            formatted_line += (str(self.localidadPartner(apunte.partner_id))[:15] if len(str(self.localidadPartner(apunte.partner_id))) > 15 else str(self.eliminar_tildes(self.localidadPartner(apunte.partner_id),apunte.partner_id))).ljust(15,' ')
            formatted_line += (str(self.provinciaPartner(apunte.partner_id))[:15] if len(str(self.provinciaPartner(apunte.partner_id))) > 15 else str(self.eliminar_tildes(self.provinciaPartner(apunte.partner_id),apunte.partner_id))).ljust(15,' ')
            formatted_line += str('').ljust(11,' ')
            formatted_line += (str(self.codigoPostalPartner(apunte.partner_id))[:8] if len(str(self.codigoPostalPartner(apunte.partner_id))) > 8 else str(self.codigoPostalPartner(apunte.partner_id))).rjust(8,' ')

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
            formatted_line += str(60).rjust(4,'0')  
            formatted_line += str(comprobante.sequence_number).rjust(8,'0')
            formatted_line += '{:.2f}'.format(self.montoSujetoARetencion(comprobante,self.record.tax_group_id_ret_tucuman,tipo_operacion)).rjust(15, '0')
            formatted_line += '{:.2f}'.format(self.porcentajeAlicuota(comprobante,self.record.tax_group_id_ret_tucuman,self.record.tax_group_id_perc_tucuman,tipo_operacion)).rjust(6, '0') #Alicuota
            formatted_line += '{:.2f}'.format(self.montoRetenido(apunte,comprobante,self.record.tax_group_id_ret_tucuman,tipo_operacion)).rjust(15, '0')
            formatted_lines.append(formatted_line)
        return "\n".join(formatted_lines)
     
    def format_tucuman_nc(self, record):
        formatted_lines = []
        for apunte in record.apunte_ids:
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            if comprobante.move_type == 'out_refund' or comprobante.move_type == 'in_refund':
                facturas = self.FacturasRelacionadas(comprobante)
                for factura in facturas:
                    formatted_line = str(60).rjust(4,'0')
                    formatted_line += str(comprobante.sequence_number).rjust(8,'0')
                    formatted_line += str(60).rjust(4,'0')
                    formatted_line += str(factura.sequence_number).rjust(8,'0')
                    formatted_line += str(self.tipoComprobanteTucuman(comprobante,tipo_operacion)).rjust(1)
                    formatted_lines.append(formatted_line)
        return "\n".join(formatted_lines)

    def format_salta_excel(self,record):
        formatted_lines = []
        for apunte in record.move_ids:
            line = []
            line.append(str(apunte.date.strftime('%Y%m%d')))
            line.append(str(self.tipoFacturaSalta(apunte)))
            line.append(self.clean_string(str(apunte.l10n_latam_document_number)))
            line.append(str(self.razonSocial(apunte.partner_id)))
            line.append(str(self.nrodeIdentificacion(apunte.partner_id)))
            line.append(float('{:.2f}'.format(self.montoSujetoARetencion(apunte,self.record.tax_group_id_ret_tucuman,2))))
            formatted_lines.append(line)
        head = ['fecha', 'tipo', 'comprobant','razon','cuit','neto']
        formatted_lines.append(head)
        reversed_data = list(reversed(formatted_lines))
        return reversed_data

    def format_Excel_generico(self,record,taxgroup_ret,tax_group_perc):
        formatted_lines = []
        
        for apunte in record.apunte_ids:
            line = []
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            line.append(str(apunte.date.strftime('%Y%m%d')))
            line.append(apunte.move_name)
            line.append(self.razonSocial(apunte.partner_id))
            line.append(apunte.name)
            line.append(float('{:.2f}'.format(apunte.debit)))
            line.append(float('{:.2f}'.format(apunte.credit)))
            line.append(float('{:.2f}'.format(self.porcentajeAlicuota(comprobante,taxgroup_ret,tax_group_perc,tipo_operacion))))
            line.append(float('{:.2f}'.format(self.montoSujetoARetencion(comprobante,taxgroup_ret,tipo_operacion))))
            line.append(float('{:.2f}'.format(float(self.montoComprobante(comprobante,tipo_operacion)))))                             
            formatted_lines.append(line)
        fecha = ['Periodo', record.date_start.strftime('%Y/%m/%d'), record.date_end.strftime('%Y/%m/%d')]
        head = ['Fecha', 'Asiento contable', 'Razon','Nro. Cert/Perc','Ret/Per Debito','Ret/Per Credito','Porcentaje Ret/Per','Neto','Total Factura/Pago']
        formatted_lines.append(head)
        formatted_lines.append(fecha)
        reversed_data = list(reversed(formatted_lines))
        return reversed_data
    
    def exportToTxt(self):
        if self.record.municipalidad == 'iva':
            txt_content = self.format_iva_compras_cabecera(self.record)
            detalle_content = self.format_iva_compras_alicuota_(self.record)
            # Codificar el contenido en base64
            file_content_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
            detalle_content_base64 = base64.b64encode(detalle_content.encode('utf-8')).decode('utf-8')
            attachment = self.record.env['ir.attachment'].create({
                'name': 'IVA_Compras_Cabecera.txt',
                'type': 'binary',
                'datas': file_content_base64,
                'mimetype': 'text/plain',
            })
            attachment2 = self.record.env['ir.attachment'].create({
                'name': 'IVA_Compras_Alicuota.txt',
                'type': 'binary',
                'datas': detalle_content_base64,
                'mimetype': 'text/plain',
            })
            return self.download_zip(self.record,[attachment.id,attachment2.id])
        if self.record.municipalidad == 'caba':
            if self.record.apuntes_a_mostrar == '4':
                txt_content = self.format_line_credit(self.record)
                # Codificar el contenido en base64
                file_content_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
                
                # Crear un adjunto en Odoo
                attachment = self.record.env['ir.attachment'].create({
                    'name': f"Nota_Credito_AGIP_{self.record.get_month_name_or_date_range()}.txt",
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
                txt_content = self.format_line(self.record)
                # Codificar el contenido en base64
                file_content_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
                
                # Crear un adjunto en Odoo
                attachment = self.record.env['ir.attachment'].create({
                    'name': f"RetPer_AGIP_{self.record.get_month_name_or_date_range()}.txt",
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
            nc_content = self.format_tucuman_nc(self.record)
            # Codificar el contenido en base64
            txt_content_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
            datos_content_base64 = base64.b64encode(datos_content.encode('utf-8')).decode('utf-8')
            nc_content_base64 = base64.b64encode(nc_content.encode('utf-8')).decode('utf-8')
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
            attachment3 = self.record.env['ir.attachment'].create({
                'name': 'NCFACT.txt',
                'type': 'binary',
                'datas': nc_content_base64,
                'mimetype': 'text/plain',
            })
            if self.record.apuntes_a_mostrar == '3':
                return self.download_zip(self.record,[attachment.id,attachment2.id,attachment3.id])
            else:
                return self.download_zip(self.record,[attachment.id,attachment2.id])
        elif self.record.municipalidad == 'sicore':
            txt_content = self.format_sicore(self.record)
            txt_content = txt_content.replace('\n', '\r\n')
            # Codificar el contenido en base64
            file_content_base64 = base64.b64encode(txt_content.encode('utf-8')).decode('utf-8')
            # Crear un adjunto en Odoo
            attachment = self.record.env['ir.attachment'].create({
                'name': f"Sicore_{self.record.get_month_name_or_date_range()}.txt",
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
                    'name': f"Perc_Jujuy_{self.record.get_month_name_or_date_range()}.txt",
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
                datos_content = self.format_jujuy_ret_detalle(self.record)
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

    def generate_excel_report(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        if self.record.municipalidad == 'todo':
            dataExcel= self.format_salta_excel(self.record)
        else:
            taxgroup = False
            taxgroup_perc = False
            if self.record.municipalidad == 'jujuy':
                taxgroup = self.record.tax_group_id_ret_jujuy
                taxgroup_perc = self.record.tax_group_id_perc_jujuy
            if self.record.municipalidad == 'sicore':
                taxgroup = self.record.tax_group_id_ret_sicore
            if self.record.municipalidad == 'caba':
                taxgroup = self.record.tax_group_id_ret_agip
                taxgroup_perc = self.record.tax_group_id_perc_agip
            if self.record.municipalidad == 'tucuman':
                taxgroup = self.record.tax_group_id_ret_tucuman
                taxgroup_perc = self.record.tax_group_id_perc_tucuman
            dataExcel = self.format_Excel_generico(self.record,taxgroup,taxgroup_perc)
        # Ejemplo de datos
        # Escribir datos en el archivo Excel
        row = 0
        for line in dataExcel:
            col = 0
            for item in line:
                worksheet.write(row, col, item)
                col += 1
            row += 1
        #worksheet.write_formula(row, 4, f'=SUM(E3:E{row})', None, {'calculate_on_open': True})
        #worksheet.write_formula(row, 5, f'=SUM(F3:F{row})', None, {'calculate_on_open': True})
        worksheet.set_column('A:A', 15)  # Ancho de la columna E
        worksheet.set_column('B:B', 20)  # Ancho de la columna F
        worksheet.set_column('C:C', 25)  # Ancho de la columna G
        worksheet.set_column('D:D', 25)  # Ancho de la columna G
        worksheet.set_column('E:E', 15)  # Ancho de la columna E
        worksheet.set_column('F:F', 15)  # Ancho de la columna F
        worksheet.set_column('G:G', 15)  # Ancho de la columna G
        workbook.close()
        output.seek(0)
        file_data = base64.b64encode(output.read())
        output.close()

        attachment = self.record.env['ir.attachment'].create({
            'name': f"informe_{self.record.municipalidad}_{self.record.get_month_name_or_date_range()}.xlsx",
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
    def documentoAfecadoporNotaCredito(self,nc):
        return nc.reversed_entry_id.sequence_number
        
    def AgipSequenceNumber(self,comprobante,tipo_operacion):
        if tipo_operacion == 2:
            return '00000060'+ str(comprobante.sequence_number).rjust(8,'0')
        else:
            return str(comprobante.sequence_number).rjust(16,'0')
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
                        return '-'+str(comprobante.amount_total)
                    else:
                        return comprobante.amount_total
                else:
                    return comprobante.amount_total


    def tipoFacturaSalta(self,comprobante):
            front = 'FA'
            if comprobante.move_type == 'out_invoice' or comprobante.move_type == 'in_invoice':
                front = 'FA'
            if comprobante.move_type == 'out_refund' or comprobante.move_type == 'in_refund':
                front = 'NC'
            if comprobante.move_type == 'out_receipt' or comprobante.move_type == 'in_receipt':
                front = 'ND'
            return front +'_'+str(comprobante.l10n_latam_document_type_id.l10n_ar_letter)
            
    def clean_string(self, input_string):
        # Usar expresiones regulares para eliminar ceros iniciales y el guion
        cleaned_string = re.sub(r'^0+', '', input_string)  # Eliminar ceros iniciales
        cleaned_string = cleaned_string.replace('-', '')   # Eliminar el guion
        return cleaned_string
    
    def tipoFactura(self,apunte,tipo_operacion):
        if tipo_operacion ==1:
            return ' '
        else:
            factura = apunte.move_id
            return factura.l10n_latam_document_type_id.l10n_ar_letter
    def tipoComprobanteTucuman(self,comprobante,tipo_operacion):
        if tipo_operacion == 1:
            return 99
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
                if line.tax_id.tax_group_id.id == taxgroup.id:
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
        if contacto.parent_id:
            return contacto.parent_id.name
        return contacto.name   
    def domicilioPartner(self,contacto):
        return contacto.street
    def localidadPartner(self,contacto):
        return contacto.city
    def provinciaPartner(self,contacto):
        return contacto.state_id.name
    def codigoPostalPartner(self, contacto):
        if contacto.zip:
            return contacto.zip
        else:
            raise UserError(f"No se encontró el código postal en el contacto: {contacto.name}")
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
                if retencion.tax_id.tax_group_id.id == taxgroup.id:
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
                if line.tax_id.tax_group_id.id == taxgroup.id:
                    retenido = line.base_amount
            return retenido
        else:
            if (self.record.municipalidad == 'jujuy'):
                if comprobante.move_type == 'out_refund' or comprobante.move_type == 'in_refund':
                    return -comprobante.amount_untaxed
                else:
                    return comprobante.amount_untaxed
            return comprobante.amount_untaxed

    def porcentajeAlicuota(self,comprobante,taxgroup,taxgroup_perc,tipo_operacion):
        if tipo_operacion == 1:
            retenido = 0
            base = 0
            perc_group = 1
            for line in comprobante.l10n_ar_withholding_line_ids:
                if line.tax_id.tax_group_id.id == taxgroup.id:
                    retenido = line.amount
                    base = line.base_amount
            return (retenido / base) * 100
        else:
            monto_alicuota = 0
            for line in comprobante.invoice_line_ids:
                for tax in line.tax_ids:
                    if tax.tax_group_id.id == taxgroup_perc.id:
                        monto_alicuota = tax.amount  
            return monto_alicuota
            #return (comprobante.amount_tax / comprobante.amount_untaxed) * 100 #28
        
    def montoRetenido(self,apunte,comprobante,taxgroup,tipo_operacion):
        if tipo_operacion == 1:
            retenido = 0
            for line in comprobante.l10n_ar_withholding_line_ids:
                if line.tax_id.tax_group_id.id == taxgroup.id:
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
    def cantidadFacturas(self,comprobante):
        return len(comprobante.matched_move_line_ids)
    def nroSucursalProveedor(self,comprobante):
        for line in comprobante.matched_move_line_ids:
            return self.extract_number_proveedor(line.move_id.sequence_prefix)
        return 0

    def FacturasRelacionadas(self,comprobante):
        # Suponiendo que tienes el record de la nota de crédito
        credit_note = self.record.env['account.move'].browse(comprobante.id)
        
        # Obtén las líneas de la nota de crédito
        credit_note_lines = credit_note.line_ids
        
        # Encuentra las líneas reconciliadas parcialmente
        partial_reconciles = credit_note_lines.mapped('matched_debit_ids') | credit_note_lines.mapped('matched_credit_ids')
        
        # Encuentra las líneas reconciliadas completamente
        full_reconciles = credit_note_lines.mapped('full_reconcile_id')
        
        # Inicializa una lista para almacenar las facturas encontradas
        invoices = self.record.env['account.move']
        
        for partial in partial_reconciles:
            if partial.debit_move_id.move_id.move_type in ['out_invoice', 'in_invoice']:
                invoices |= partial.debit_move_id.move_id
            if partial.credit_move_id.move_id.move_type in ['out_invoice', 'in_invoice']:
                invoices |= partial.credit_move_id.move_id
        
        # Recorre las reconciliaciones completas y añade las facturas asociadas a la lista
        for full in full_reconciles:
            for line in full.reconciled_line_ids:
                if line.move_id.move_type in ['out_invoice', 'in_invoice']:
                    invoices |= line.move_id

        # Filtra las facturas para eliminar la propia nota de crédito de la lista
        invoices = invoices.filtered(lambda inv: inv.id != credit_note.id)
        
        # Ahora la variable `invoices` contiene todas las facturas asociadas con la nota de crédito
        return invoices
            
    def extract_number(self,sequence_prefix):
        # Usamos una expresión regular para encontrar el número en la cadena
        return sequence_prefix[6:8]
        
    def extract_number_proveedor(self,sequence_prefix):
         # Usamos una expresión regular para buscar el número después de los ceros iniciales
        match = re.search(r'0*(\d+)-$', sequence_prefix)
        if match:
            # Tomamos el número capturado
            number = match.group(1)
            # Si el número tiene más de 2 dígitos, devolvemos los últimos 2
            return number[-2:] if len(number) > 2 else number
        else:
            return None
    
        
    def extract_last_four_digits(self,input_string):
        # Extraer los últimos 6 caracteres de la cadena
        last_six_digits = input_string[-6:]
        
        # Filtrar solo los dígitos de los últimos 6 caracteres
        last_six_digits = ''.join(filter(str.isdigit, last_six_digits))
        
        # Tomar solo los últimos 4 dígitos
        last_four_digits = last_six_digits[-3:]
        
        return last_four_digits

    def eliminar_tildes(self,texto,partner):
        # Normalizar el texto en forma NFC
        if texto:
            texto_normalizado = unicodedata.normalize('NFD', texto)
            # Filtrar los caracteres diacríticos
            texto_sin_tildes = ''.join(c for c in texto_normalizado if unicodedata.category(c) != 'Mn')
            # Normalizar el texto en forma NFC
        else:
            raise UserError(f"No se encontró el dato necesario en el contacto: {partner.name}")
        return unicodedata.normalize('NFC', texto_sin_tildes)
    
    def download_zip(self,record, attachment_ids):
            # Obtener los archivos adjuntos
            attachments = record.env['ir.attachment'].sudo().browse(attachment_ids)
            name = 'RetPer_Tucuman ' + record.get_month_name_or_date_range()
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

            if self.record.municipalidad == 'jujuy':
                name = 'Ret_Jujuy' + record.get_month_name_or_date_range()
            if self.record.municipalidad == 'iva':
                name = 'IVA_COMPRAS' + record.get_month_name_or_date_range()
            # Crear un archivo adjunto en Odoo
            attachment = self.record.env['ir.attachment'].create({
                'name': name,
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
   