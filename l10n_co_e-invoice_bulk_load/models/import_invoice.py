# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import base64
import csv
from datetime import date as dt


class ImportInvoices(models.Model):
    _name = 'import.invoices'
    _description = 'import.invoices'

    def btn_process(self):
        _procesados = ""
        _procesados_stock = ""
        _noprocesados = ""
        vals={}    
        self.ensure_one()
        if not self.delimiter:
            raise ValidationError('Debe ingresar el delimitador')
        if not self.invoices_file:
            raise ValidationError('Debe seleccionar el archivo')
        if self.state != 'draft':
            raise ValidationError('Archivo procesado!')
        self.file_content = base64.decodebytes(self.invoices_file)

        journal_id = self.env['account.journal'].search([('type','=','sale')])[0]

        lines = self.file_content.split('\n')
        for i,line in enumerate(lines):
            if self.skip_first_line and i == 0:
                continue
            lista = line.split(self.delimiter)
            if len(lista) == 7:
                rs_nomina = lista[0]
                nit_nomina = lista[1]
                tipo_persona = lista[2]
                documento = lista[3]
                producto = lista[4]
                fecha = lista[5]
                precio = lista[6]

                vals.clear()

                # Carga vals
                if documento != '':
                    
                    cliente_tmp = self.env['res.partner'].search([('vat','=',documento)])
                    client_tercero_tmp = self.env['res.partner'].search([('vat','=',nit_nomina)])
                    producto_tmp = self.env['product.template'].search([('default_code','=',producto)])
                    
                    move_line_vals = []

                    line =(0, 0, {'account_id': 176,
                                    'product_id': producto_tmp.id, 
                                    'quantity': 1, 
                                    'product_uom_id': producto_tmp.uom_id.id,
                                    'price_unit': float(precio),
                                    'tax_ids': [(4, producto_tmp.taxes_id.id)],})
                    
                    move_line_vals.append(line)
                    vals = {
                        "journal_id": journal_id.id,
                        'company_id': self.env.user.company_id.id,
                        "invoice_payment_term_id": 1,
                        "validate_cron": True,
                        "move_type": "out_invoice",
                        "invoice_line_ids": move_line_vals
                    }

                    
                    # Carga vals
                    if client_tercero_tmp: vals['tercero_relacionado'] = client_tercero_tmp.id
                    if cliente_tmp: vals['partner_id'] = cliente_tmp.id

                    factura = self.env['account.move'].create(vals)
                    
                    _procesados += "{} \n".format(documento)
                else:
                    _noprocesados += "{} \n".format(documento)
            else:
                raise ValidationError("El CSV no se procesara por estar mal formado en la linea {0}, contenido de linea: {1}".format(i, line))
        self.facturas_creadas = _procesados
        self.not_processed_content = _noprocesados
        self.state = 'processed'

    name = fields.Char('Nombre')
    invoices_file = fields.Binary('Archivo')
    delimiter = fields.Char('Delimitador',default=";")
    state = fields.Selection(selection=[('draft','Borrador'),('processed','Procesado')],string='Estado',default='draft')
    file_content = fields.Text('Texto archivo')
    not_processed_content = fields.Text('Texto no procesado')
    facturas_creadas = fields.Text('Facturas Creados')
    skip_first_line = fields.Boolean('Saltear primera linea',default=True)