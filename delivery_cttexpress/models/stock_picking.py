# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
import logging
_logger = logging.getLogger(__name__)

class StockPicking(models.Model):
    _inherit = "stock.picking"

    def cttexpress_get_label(self):
        """Get label for current picking

        :return tuple: (filename, filecontent)
        """
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        _logger.debug("reference: %s", tracking_ref)
        # Se utiliza el método auxiliar del carrier para identificar si es CTT Express.
        if not self.carrier_id._is_ctt() or not tracking_ref:
            return
        label = self.carrier_id.cttexpress_get_label(tracking_ref)
        self.message_post(
            body=_("CTT Express label for %s") % tracking_ref,
            attachments=label,
        )
        return label
        
    def _compute_ask_number_of_packages(self):
        for picking in self:
            picking.number_of_packages = None
            picking.ask_number_of_packages = None
            if picking.carrier_id:
                if picking.carrier_id.delivery_type == "ctt":
                    custom = picking.carrier_id.get_ask_package_number_custom()
                    if custom is not None:
                        picking.ask_number_of_packages = custom
                    else:
                        picking.ask_number_of_packages = bool(
                            picking.carrier_id and not picking.package_ids or picking.picking_type_id.force_set_number_of_packages
                        )
                    # Si no se va a preguntar y no se han definido paquetes, asignamos el valor por defecto
                    if not picking.ask_number_of_packages and not picking.package_ids:
                        default_nop = picking.carrier_id.default_number_of_packages or 1
                        picking.number_of_packages = default_nop