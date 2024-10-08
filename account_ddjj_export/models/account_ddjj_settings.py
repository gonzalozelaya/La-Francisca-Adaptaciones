from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tax_group_id_ret_agip = fields.Many2one(
        'account.tax.group', 
        string='Grupo de Impuestos Retención AGIP',
        config_parameter='account_ddjj_settings.tax_group_id_ret_agip',
        help="Seleccione el grupo de impuestos"
    )
    account_id_ret_agip = fields.Many2one(
        'account.account', 
        string=' Plan de Cuentas Retenciones AGIP',
        config_parameter='account_ddjj_settings.account_id_ret_agip',
        help="Seleccione la cuenta del plan de cuentas"
    )
    tax_group_id_perc_agip = fields.Many2one(
        'account.tax.group', 
        string='Grupo de Impuestos Percepción AGIP',
        config_parameter='account_ddjj_settings.tax_group_id_perc_agip',
        help="Seleccione el grupo de impuestos"
    )
    account_id_perc_agip = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Percepción AGIP',
        config_parameter='account_ddjj_settings.account_id_perc_agip',
        help="Seleccione la cuenta del plan de cuentas"
    )
#################################JUJUY##############3
    tax_group_id_ret_jujuy = fields.Many2one(
        'account.tax.group', 
        string='Grupo de Impuestos Retenciones Jujuy',
        config_parameter='account_ddjj_settings.tax_group_id_ret_jujuy',
        help="Seleccione el grupo de impuestos"
    )
    account_id_ret_jujuy = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Ret. Jujuy',
        config_parameter='account_ddjj_settings.account_id_ret_jujuy',
        help="Seleccione la cuenta del plan de cuentas"
    )
    tax_group_id_perc_jujuy = fields.Many2one(
        'account.tax.group', 
        string='Grupo de Impuestos Perc. Jujuy',
        config_parameter='account_ddjj_settings.tax_group_id_perc_jujuy',
        help="Seleccione el grupo de impuestos"
    )
    account_id_perc_jujuy = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Perc. Jujuy',
        config_parameter='account_ddjj_settings.account_id_perc_jujuy',
        help="Seleccione la cuenta del plan de cuentas"
    )

#################################TUCUMAN##############3
    tax_group_id_ret_tucuman = fields.Many2one(
        'account.tax.group', 
        string='Grupo de Impuestos Ret. Tucumán',
        config_parameter='account_ddjj_settings.tax_group_id_ret_tucuman',
        help="Seleccione el grupo de impuestos"
    )
    account_id_ret_tucuman = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Ret. Tucumnán',
        config_parameter='account_ddjj_settings.account_id_ret_tucuman',
        help="Seleccione la cuenta del plan de cuentas"
    )
    tax_group_id_perc_tucuman = fields.Many2one(
        'account.tax.group', 
        string='Grupo de Impuestos Perc. Tucuman',
        config_parameter='account_ddjj_settings.tax_group_id_perc_tucuman',
        help="Seleccione el grupo de impuestos"
    )
    account_id_perc_tucuman = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Perc. Tucuman',
        config_parameter='account_ddjj_settings.account_id_perc_tucuman',
        help="Seleccione la cuenta del plan de cuentas"
    )

#################################SICORE##############3
    tax_group_id_ret_sicore = fields.Many2one(
        'account.tax.group', 
        string='Grupo de Impuestos SICORE',
        config_parameter='account_ddjj_settings.tax_group_id_ret_sicore',
        help="Seleccione el grupo de impuestos"
    )
    account_id_ret_sicore = fields.Many2one(
        'account.account', 
        string='Plan de Cuentas Retención ganancias',
        config_parameter='account_ddjj_settings.account_id_ret_sicore',
        help="Seleccione la cuenta del plan de cuentas"
    )