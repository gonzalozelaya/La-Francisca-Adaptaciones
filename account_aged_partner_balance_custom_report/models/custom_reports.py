from odoo import models, fields, api, Command, _
import base64
from io import StringIO,BytesIO
import io
import zipfile
from datetime import datetime, date, timedelta
import re
import unicodedata
import xlsxwriter

class AccountDDJJ(models.TransientModel):
    
    _name = 'account.custom.report.aged'
    _description = 'Modelo para DDJJ de cuentas'
    
    date_start = fields.Date(string='Fecha Inicio', required=True,default=lambda self: fields.Date.to_string(datetime(datetime.now().year, datetime.now().month, 1)))
    date_end = fields.Date(string='Fecha Fin', required=True, default=lambda self: fields.Date.today())
    
    area = fields.Many2one(
        comodel_name='res.partner.category',  # Modelo relacionado
        string='Zona',        # Nombre del campo
        help='Selecciona una zona'
    )
    type = fields.Selection(
        selection=[
            ('cobrar','Por cobrar'),
            ('pagar','Por Pagar'),
        ],
        string='Tipo',
        required=True,
        default='cobrar'
    )
    
    partner_id = fields.Many2one(
        comodel_name='res.partner',  # Modelo relacionado
        string='Contacto',        # Nombre del campo
        help='Selecciona un contacto'
    )
    
    apunte_ids = fields.Many2many(
        comodel_name='account.move.line',
        relation='account_custom_report_move_line_rel',
        column1='account_custom_report_id',
        column2='move_line_id',
        string='Apuntes Contables',
        compute='_compute_apunte_ids')
    
    move_ids = fields.Many2many(
        comodel_name='account.move',
        relation='account_custom_report_move_rel',
        column1='account_custom_report_id',
        column2='move_id', string='Facturas y Notas de Crédito',compute='_compute_apunte_ids')
    
    @api.depends('date_start','date_end','tipo','area','partner_id')
    def _compute_apunte_ids(self):
        for rec in self:
                    # Primero, define el dominio inicial para los saldos a cobrar
            domain = [
                ('account_id.user_type_id.type', '=', 'receivable'),
                ('reconciled', '=', False),
                ('move_id.state', '=', 'posted')
            ]
            # Filtrar por área si se seleccionó una
            if self.area:
                domain.append(('partner_id.category_id', 'child_of', self.area.id))

            # Filtrar por contacto específico si se seleccionó
            if self.partner_id:
                domain.append(('partner_id', '=', self.partner_id.id))
            
            saldos  = self.env['account.move.line'].search(domain)
            rec.apunte_ids = [Command.clear(), Command.set(saldos.ids)]
            rec.move_ids = [Command.clear()]

    
    def generate_excel(self):
        exporter = CustomReportExport(self)
        return exporter.generate_excel_report()
        
class CustomReportExport:
    def __init__(self, record):
        self.record = record
        
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
    
    def generate_excel_report(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        if self.record.municipalidad == 'cobrar':
            dataExcel= self.format_salta_excel(self.record)
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
            'name': 'informe_ddjj.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
    
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
    
    
    def nrodeIdentificacion(self,contacto):
        return contacto.vat
    
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
        return contacto.zip