# -*- coding: utf-8 -*-
{
    'name': "Añadir Contacto a Reportes a pagar/cobrar",

    'summary': """
        Este módulo permite agregar la columna Contacto al reporte de cuentas a Pagar y cuentas a Cobrar""",

    'description': """
        Este módulo permite agregar la columna Contacto al reporte de cuentas a Pagar y cuentas a Cobrar
    """,

    'author': "OutsourceArg SAS",
    'website': "https://outsourcearg.com/",
    'installable': True,

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['account','account_reports'],

    # always loaded
    'data': [
        'data/aged_partner_balance.xml',
        #'views/views.xml',
        #'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}