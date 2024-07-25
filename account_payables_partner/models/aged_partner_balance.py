# -*- coding: utf-8 -*-
import datetime

from odoo import models, fields, _, api
from odoo.tools.misc import format_date

class AgedPartnerBalanceCustomHandler(models.AbstractModel):
    _inherit = 'account.aged.partner.balance.report.handler'
    
    def build_result_dict(report, query_res_lines):
        rslt = {f'period{i}': 0 for i in range(len(periods))}

        for query_res in query_res_lines:
            for i in range(len(periods)):
                period_key = f'period{i}'
                rslt[period_key] += query_res[period_key]

        if current_groupby == 'id':
            query_res = query_res_lines[0] # We're grouping by id, so there is only 1 element in query_res_lines anyway
            currency = self.env['res.currency'].browse(query_res['currency_id'][0]) if len(query_res['currency_id']) == 1 else None
            expected_date = len(query_res['expected_date']) == 1 and query_res['expected_date'][0] or len(query_res['due_date']) == 1 and query_res['due_date'][0]
            partner_id = query_res['partner_id'][0] if query_res['partner_id'] else None
            rslt.update({
                'invoice_date': query_res['invoice_date'][0] if len(query_res['invoice_date']) == 1 else None,
                'due_date': query_res['due_date'][0] if len(query_res['due_date']) == 1 else None,
                'amount_currency': query_res['amount_currency'],
                'currency_id': query_res['currency_id'][0] if len(query_res['currency_id']) == 1 else None,
                'currency': currency.display_name if currency else None,
                'account_name': query_res['account_name'][0] if len(query_res['account_name']) == 1 else None,
                'expected_date': expected_date or None,
                'total': None,
                'has_sublines': query_res['aml_count'] > 0,

                # Needed by the custom_unfold_all_batch_data_generator, to speed-up unfold_all
                'partner_id': partner_id,
                'partner_name': self.env['res.partner'].browse(partner_id).name,
            })
        else:
            rslt.update({
                'invoice_date': None,
                'due_date': None,
                'amount_currency': None,
                'currency_id': None,
                'currency': None,
                'account_name': None,
                'expected_date': None,
                'total': sum(rslt[f'period{i}'] for i in range(len(periods))),
                'has_sublines': False,
                'partner_id': None,
                'partner_name': None,
            })

        return rslt

    def _prepare_partner_values(self):
        return {
            'invoice_date': None,
            'due_date': None,
            'amount_currency': None,
            'currency_id': None,
            'currency': None,
            'account_name': None,
            'expected_date': None,
            'total': 0,
            'partner_id': None,
            'partner_name': None,
        }

# class my_module(models.Model):
#     _name = 'my_module.my_module'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100