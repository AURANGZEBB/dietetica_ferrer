# -*- coding: utf-8 -*-
{
    'name': "CTT Express",
    'summary': "Delivery Carrier implementation for CTT Express API",

    'description': """
Este módulo permite la integración con CTT Express como transportista en Odoo.

- Soporta tanto integración REST como SOAP.
- Permite crear, cancelar y hacer seguimiento de envíos.
- Crea manifiestos en formato PDF y XLSX.
- Compatible con múltiples métodos de envío CTT personalizados.
- Son imprescindibles para la instalación las librerías externas: "fpdf2" y "xlsxwriter".
""",

    'category': 'Delivery',
    'version': '17.0.1.3.3',
    'depends': [
        "delivery",
        "delivery_state",
        "delivery_price_method",
        "delivery_package_number"
    ],
    'data': [
        "security/ir.model.access.csv",
        "wizards/cttexpress_manifest_wizard_views.xml",
        "wizards/cttexpress_pickup_wizard.xml",
        "wizards/choose_delivery_carrier_views.xml",
        "views/delivery_cttexpress_view.xml",
        "views/stock_picking_views.xml",
        "data/delivery_carrier_data.xml"
    ],
    'assets': {
        'web.assets_backend': [
            "delivery_cttexpress/assets/assets.xml",
            "delivery_cttexpress/static/src/js/fix_table_style.js",
        ]
    },
    'license': 'AGPL-3',
}