from odoo import models, fields, api, Command, _
import base64
from io import BytesIO
import re
import xlsxwriter

class AccountCustomReportAged(models.TransientModel):
    
    _name = 'account.custom.report.aged'
    _description = 'Modelo para DDJJ de cuentas'
    
    date_end = fields.Date(string='Al', required=True, default=lambda self: fields.Date.today())
    
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
    fac_type = fields.Selection(
        selection=[
            ('x','Factura X'),
            ('fac','Facturas'),
            ('pagos','Pagos a favor del cliente'),
        ],
        string='Tipo de Comprobante',
    )
    
    partner_id = fields.Many2one(
        comodel_name='res.partner',  # Modelo relacionado
        string='Contacto',        # Nombre del campo
        help='Selecciona un contacto',
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

    balance = fields.Float(string='Saldo',compute='_compute_balance')
    ignore_saldo = fields.Boolean(string='Ignorar saldo a favor de cliente en reportes',default=True,help='Marque esta casilla para ignorar los saldos en los reportes Excel.')
                
    @api.depends('apunte_ids')
    def _compute_balance(self):
        for rec in self:
            if len(rec.apunte_ids) > 0:
                rec.balance = sum(line.amount_residual for line in rec.apunte_ids)
            else:
                rec.balance =0
    
    @api.depends('date_end','type','area','partner_id','fac_type')
    def _compute_apunte_ids(self):
        for rec in self:
                    # Primero, define el dominio inicial para los saldos a cobrar
            domain = [
                "&", ("account_id.account_type", "=", "asset_receivable"), ("account_id.non_trade", "=", False),
                ('date', '<=', rec.date_end),
                ('reconciled', '=', False),
                ('move_id.state', '=', 'posted'),
            ]
            # Filtrar por área si se seleccionó una
            if self.area:
                domain.append(('partner_id.category_id', 'child_of', self.area.id))
            # Filtrar por contacto específico si se seleccionó
            if self.partner_id:
                domain.append(('partner_id', '=', self.partner_id.id))
            if self.fac_type == 'x':
                domain.append(('move_id.journal_id.id','=',218))
            if self.fac_type == 'fac':
                domain.append(('move_id.journal_id.id','=',18))
            
            saldos  = self.env['account.move.line'].search(domain).sorted(lambda l: l.partner_id.name)
            rec.apunte_ids = [Command.clear(), Command.set(saldos.ids)]
            rec.move_ids = [Command.clear()]

    
    def generate_excel(self):
        exporter = CustomReportExport(self)
        return exporter.generate_excel_report()
        
class CustomReportExport:
    def __init__(self, record):
        self.record = record
        
    def format_por_cobrar_excel(self,record):
        formatted_lines = []
        fecha = ['Al', record.date_end.strftime('%Y/%m/%d'),'','']
        head = ['Fecha', 'Razon','Factura','Total Factura/Pago']
        formatted_lines.append(fecha)
        formatted_lines.append(head)
        sum_cliente = 0
        sum_total = 0
        cont_cliente = 0
        for index, apunte in enumerate(record.apunte_ids):
            line = []
            sum_cliente += apunte.amount_residual
            cont_cliente += 1
            siguiente_apunte = record.apunte_ids[index + 1] if index + 1 < len(record.apunte_ids) else None
            tipo_operacion = self.tipoOperacion(apunte)
            comprobante = self.obtenerComprobante(apunte,tipo_operacion)
            line.append(str(apunte.date.strftime('%Y/%m/%d')))
            line.append(self.razonSocial(apunte.partner_id))
            line.append(apunte.name)
            line.append(apunte.amount_residual)
            if cont_cliente == 1:
                head = [self.razonSocial(apunte.partner_id),'','','','']
                formatted_lines.append(head)
                cliente_start_index = len(formatted_lines)- 1
            formatted_lines.append(line)
            if siguiente_apunte is None or apunte.partner_id != siguiente_apunte.partner_id:
                line2 = ['','','','',sum_cliente]
                formatted_lines.append(line2)
                if sum_cliente < 0 and record.ignore_saldo:
                    del formatted_lines[cliente_start_index:cliente_start_index + cont_cliente + 2]  # +1 para incluir la línea del saldo
                sum_cliente = 0
                cont_cliente = 0
        return formatted_lines
    
    def generate_excel_report(self):
        output = BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        total_format = workbook.add_format({
        'bold': True,
        'font_color': 'white',  # Puedes cambiar el color del texto si lo deseas
        'bg_color': '#1d1d1b',  # Cambiar el color de fondo
        'align': 'left',  # Alineación a la derecha
        'valign': 'vcenter'  # Alineación vertical centrada
        })
        total_number_format = workbook.add_format({
        'bold': True,
        'font_color': 'white',  # Puedes cambiar el color del texto si lo deseas
        'bg_color': '#1d1d1b',  # Cambiar el color de fondo
        'valign': 'vcenter'  # Alineación vertical centrada
        })
        client_header_format = workbook.add_format({
        'bold': True,
        'font_color': '#1d1d1b',  # Puedes cambiar el color del texto si lo deseas
        'valign': 'vcenter'  # Alineación vertical centrada
        })
        header_format = workbook.add_format({
        'font_size': 12,  # Tamaño de fuente más grande
        'bold': True,
        'align': 'left',
        'bg_color': '#c69c6d',
        'font_color': 'white'})
        
        if self.record.type == 'cobrar':
            dataExcel= self.format_por_cobrar_excel(self.record)
        # Ejemplo de datos
        # Escribir datos en el archivo Excel
        row = 0
        for index,line in enumerate(dataExcel):
            col = 0
            for item in line:
                if index == 0 or index == 1:
                    worksheet.write(row, col, item, header_format)
                elif line[0] != '' and line[1] == '':
                    worksheet.merge_range(row,0, row,3,line[0], client_header_format)
                    worksheet.set_row(row,20)
                    break
                elif line[3] == '' and line[4] != '':
                    # Merge de las primeras cuatro celdas y escribir "Total"
                    worksheet.merge_range(row,0, row,2,'Total', total_format)
                    # Escribir el valor del total en la quinta celda
                    worksheet.write(row, 3, line[4], total_number_format)
                else:
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
            'name': 'Informe a cobrar.xlsx',
            'type': 'binary',
            'datas': file_data,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
    def tipoOperacion(self,apunte):
        if apunte.tax_line_id.type_tax_use == 'sale':
            return 2
        else:
            return 1
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