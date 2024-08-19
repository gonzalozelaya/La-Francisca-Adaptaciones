# -*- coding: utf-8 -*-
{
    'name': 'Reporte personalizado, cuentas por cobrar',

    'summary': """
        Este módulo permite generar reportes personalizados de las cuentas por cobrar/pagar""",

    'description': """
        Este módulo permite generar reportes personalizados de las cuentas por cobrar/pagar
    """,

    'author': "OutsourceArg",
    'website': "http://www.outsourcearg.com",
    'installable': True,
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['account'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/custom_report.xml',
    ],
}