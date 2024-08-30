# -*- coding: utf-8 -*-
{
    'name': 'Reportes de Retenciones/Percepciones para exportar',

    'summary': """
        Este módulo permite generar reportes para realizar la declaracion jurada de varias municipalidades""",

    'description': """
        Este módulo permite generar reportes para realizar la declaracion jurada de varias municipalidades
    """,

    'author': "OutsourceArg",
    'website': "http://www.outsourcearg.com",
    'installable': True,
    'application':False,
    'icon': '/account_ddjj_export/static/description/icon.png',  # Ruta al icono
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
        'views/account_ddjj_views.xml',
        'views/account_ddjj_settings.xml',
    ],
}