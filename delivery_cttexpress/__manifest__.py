# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CTT Express",
    "summary": "Delivery Carrier implementation for CTT Express API",
    'version': '17.0.1.1.1',
    "category": "Delivery",
    "website": "https://github.com/OCA/delivery-carrier",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "installable": True,
    "depends": ["delivery","delivery_state", "delivery_price_method", 'delivery_package_number'],
    "data": [
        "security/ir.model.access.csv",
        "wizards/cttexpress_manifest_wizard_views.xml",
        "wizards/cttexpress_pickup_wizard.xml",
        'wizards/choose_delivery_carrier_views.xml',
        "views/delivery_cttexpress_view.xml",
        "views/stock_picking_views.xml",
        'data/delivery_carrier_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            "delivery_cttexpress/assets/assets.xml",
            'delivery_cttexpress/static/src/js/fix_table_style.js',
        ]
    }
}
