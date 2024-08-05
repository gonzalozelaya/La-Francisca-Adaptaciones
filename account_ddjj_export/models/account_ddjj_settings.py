from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tax_group_id = fields.Many2one(
        'account.tax.group', 
        string='Grupo de Impuestos',
        config_parameter='account_ddjj_settings.tax_group_id',
        help="Seleccione el grupo de impuestos"
    )
    account_id = fields.Many2one(
        'account.account', 
        string='Cuenta del Plan de Cuentas',
        config_parameter='account_ddjj_settings.account_id',
        help="Seleccione la cuenta del plan de cuentas"
    )