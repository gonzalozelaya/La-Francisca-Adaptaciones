class AccountDDJJSettings(models.TransientModel):
    _inherit = 'res.config.settings'
   
    tax_group_id = fields.Many2one('account.tax.group', string='Grupo de Impuestos')
    account_id = fields.Many2one('account.account', string='Cuenta del Plan de Cuentas')