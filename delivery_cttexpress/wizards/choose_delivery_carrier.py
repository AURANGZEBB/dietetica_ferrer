# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from odoo.tools.json import scriptsafe as json_safe

class ChooseCttDeliveryCarrier(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    def _get_shipment_rate(self):
        # Aquí puedes personalizar la lógica o capturar el error y manejarlo
        try:
            vals = self.carrier_id.with_context(order_weight=self.total_weight).rate_shipment(self.order_id)
            if vals.get('success'):
                self.delivery_message = vals.get('warning_message', False)
                self.delivery_price = vals['price']
                self.display_price = vals.get('carrier_price', 0.0)  # uso get para evitar KeyError
                return {'no_rate': vals.get('no_rate', False)}
            return {'error_message': vals['error_message']}
        except Exception as e:
            # Manejo del error personalizado
            return {'error_message': f"Ocurrió un error: {str(e)}"}
        
