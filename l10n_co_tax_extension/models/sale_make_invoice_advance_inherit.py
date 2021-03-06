# -*- coding: utf-8 -*-
###################################################################################
###################################################################################
##                                                                               ##
##    OpenERP, Open Source Management Solution                                   ##
##    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).                      ##
##                                                                               ##
##    This program is free software: you can redistribute it and/or modify       ##
##    it under the terms of the GNU Affero General Public License as             ##
##    published by the Free Software Foundation, either version 3 of the         ##
##    License, or (at your option) any later version.                            ##
##                                                                               ##
##    This program is distributed in the hope that it will be useful,            ##
##    but WITHOUT ANY WARRANTY; without even the implied warranty of             ##
##    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the              ##
##    GNU Affero General Public License for more details.                        ##
##                                                                               ##
##    Autor: Brayhan Andres Jaramillo Castaño                                    ##
##    Correo: brayhanjaramillo@hotmail.com                                       ##
##                                                                               ##
##    You should have received a copy of the GNU Affero General Public License   ##
##    along with this program.  If not, see <http://www.gnu.org/licenses/>.      ##
##                                                                               ##
##                                                                               ##
##     Co-Authors    Odoo LoCo                                                   ##
##     Localización funcional de Odoo para Colombia                              ##
##                                                                               ##
###################################################################################
###################################################################################

from odoo import api, fields, models, _

import time
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError, ValidationError

class SaleAdvancePaymentInvInherit(models.TransientModel):
	_description = "Sales Advance Payment Invoice"
	_inherit = "sale.advance.payment.inv"

	#@api.multi
	def _create_invoice(self, order, so_line, amount):
		inv_obj = self.env['account.invoice']
		ir_property_obj = self.env['ir.property']

		account_id = False
		if self.product_id.id:
			account_id = self.product_id.property_account_income_id.id
		if not account_id:
			inc_acc = ir_property_obj.get('property_account_income_categ_id', 'product.category')
			account_id = order.fiscal_position_id.map_account(inc_acc).id if inc_acc else False
		if not account_id:
			raise UserError(
				_('There is no income account defined for this product: "%s". You may have to install a chart of account from Accounting app, settings menu.') % \
					(self.product_id.name,))

		if self.amount <= 0.00:
			raise UserError(_('The value of the down payment amount must be positive.'))
		if self.advance_payment_method == 'percentage':
			amount = order.amount_untaxed * self.amount / 100
			name = _("Down payment of %s%%") % (self.amount,)
		else:
			amount = self.amount
			name = _('Down Payment')
		if order.fiscal_position_id and self.product_id.taxes_id:
			tax_ids = order.fiscal_position_id.map_tax(self.product_id.taxes_id).ids
		else:
			tax_ids = self.product_id.taxes_id.ids

		invoice = inv_obj.create({
			'name': order.client_order_ref or order.name,
			'origin': order.name,
			'type': 'out_invoice',
			'reference': False,
			'account_id': order.partner_id.property_account_receivable_id.id,
			'partner_id': order.partner_invoice_id.id,
			'invoice_line_ids': [(0, 0, {
				'name': name,
				'origin': order.name,
				'account_id': account_id,
				'price_unit': amount,
				'quantity': 1.0,
				'discount': 0.0,
				'uom_id': self.product_id.uom_id.id,
				'product_id': self.product_id.id,
				'sale_line_ids': [(6, 0, [so_line.id])],
				'invoice_line_tax_ids': [(6, 0, tax_ids)],
				'account_analytic_id': order.analytic_account_id.id or False,
			})],
			'currency_id': order.pricelist_id.currency_id.id,
			'payment_term_id': order.payment_term_id.id,
			'fiscal_position_id': order.fiscal_position_id.id or order.partner_id.property_account_position_id.id,
			'team_id': order.team_id.id,
			'invoice_date': fields.Date.context_today(self),
		})
		invoice.compute_taxes()
		return invoice




SaleAdvancePaymentInvInherit()