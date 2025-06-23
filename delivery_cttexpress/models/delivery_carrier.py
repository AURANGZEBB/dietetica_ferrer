# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from datetime import date

from .cttexpress_master_data import (
    CTTEXPRESS_DELIVERY_STATES_STATIC,
    CTTEXPRESS_SERVICES,
    REST_CTTEXPRESS_SERVICES,
)
from .cttexpress_request import CTTExpressRequest
from .cttexpress_rest_request import CttExpressRestAPI
import json
import base64
import requests

import logging
import time
_logger = logging.getLogger(__name__)

class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[('ctt', 'CTT Express')],
        ondelete={'ctt': 'set default'}  # <- Política obligatoria para evitar errores
    )

    is_ctt = fields.Boolean(string="Es CTT", compute="_compute_is_ctt", store=True)
    is_ctt_visible = fields.Boolean(
        string="Es CTT Visible", store=True
    )

    @api.model
    def create(self, vals):
        record = super(DeliveryCarrier, self).create(vals)
        record._onchange_delivery_type_ctt()
        return record

    @api.depends('name')
    def _compute_is_ctt(self):
        for carrier in self:
            # Obtiene el valor del nombre, que puede ser una cadena o un JSON
            name_value = carrier.name
            if isinstance(name_value, str):
                try:
                    name_value = json.loads(name_value)
                except Exception:
                    # Si no es un JSON, se mantiene la cadena
                    pass
            # Si es un dict, extraemos el valor en 'en_US' (o el idioma que prefieras)
            if isinstance(name_value, dict):
                value = name_value.get("en_US", "").strip().lower()
            else:
                value = str(name_value).strip().lower()
            carrier.is_ctt = (value == "ctt express")
    cttexpress_api = fields.Selection(
        selection=[
            ('REST', 'REST'),
            ('SOAP', 'SOAP'),
        ],
        string="CTT Express API",
        default='SOAP'
    )

    cttexpress_user = fields.Char(string="User")
    cttexpress_password = fields.Char(string="Password")
    cttexpress_customer = fields.Char(string="Customer code")
    cttexpress_agency = fields.Char(string="Agency code")
    cttexpress_contract = fields.Char(string="Contract code")

    cttexpress_rest_id = fields.Char(string="Id Cliente")
    cttexpress_rest_secret = fields.Char(string="Clave Secreta Cliente")
    cttexpress_rest_user = fields.Char(string="Nombre de Usuario")
    cttexpress_rest_password = fields.Char(string="Contraseña")
    cttexpress_rest_agency = fields.Char(string="Código Centro Cliente")

    cttexpress_shipping_type = fields.Selection(
        selection=CTTEXPRESS_SERVICES,
        string="Shipping type",
    )
    cttexpress_rest_shipping_type = fields.Selection(
        selection=REST_CTTEXPRESS_SERVICES,
        string="Tipo de Servicio",
    )
    cttexpress_document_model_code = fields.Selection(
        selection=[
            ("SINGLE", "Single"),
            ("MULTI1", "Multi 1"),
            ("MULTI3", "Multi 3"),
            ("MULTI4", "Multi 4"),
        ],
        default="SINGLE",
        string="Document model",
    )
    cttexpress_document_format = fields.Selection(
        selection=[("PDF", "PDF"), ("PNG", "PNG"), ("BMP", "BMP")],
        default="PDF",
        string="Document format",
    )
    cttexpress_document_offset = fields.Integer(string="Document Offset")

    custom_ask_package_number = fields.Boolean(
        string="Preguntar número de bultos", default=True,
        help="Si se desactiva, no se solicitará el número de paquetes al validar el picking."
    )

    default_number_of_packages = fields.Integer(
        string="Número de Bultos por Defecto", default=1,
        help="Número de bultos que se asignará por defecto si no se pregunta al usuario."
    )
    
    # Estos campos se calcularán según el valor de cttexpress_api
    show_soap = fields.Boolean(compute="_compute_show_api_flags", store=True)
    show_rest = fields.Boolean(compute="_compute_show_api_flags", store=True)

    @api.depends('cttexpress_api')
    def _compute_show_api_flags(self):
        for rec in self:
            rec.show_soap = (rec.cttexpress_api == 'SOAP')
            rec.show_rest = (rec.cttexpress_api == 'REST')

    def _is_ctt(self):
        # Si el nombre es un diccionario (o una cadena que representa un diccionario)
        name_value = self.name
        if isinstance(name_value, str):
            try:
                # Intentamos cargarlo como JSON
                name_value = json.loads(name_value)
            except Exception:
                # Si falla, se queda como string
                pass
        # Si es un dict, tomamos el valor en 'en_US' (o el idioma que prefieras)
        if isinstance(name_value, dict):
            name_value = name_value.get("en_US", "").strip().lower()
        else:
            name_value = str(name_value).strip().lower()

        return name_value == "ctt express"

    @api.onchange("delivery_type", "name")
    def _onchange_delivery_type_ctt(self):
        """Si el transportista es CTT Express, se activa la funcionalidad específica."""
        if self._is_ctt():
            self.price_method = "base_on_rule"
            self.is_ctt = True
        else:
            self.is_ctt = False

    def _ctt_request(self):
        """Get CTT Request object

        :return CTTExpressRequest: CTT Express Request object
        """
        return CTTExpressRequest(
            user=self.cttexpress_user,
            password=self.cttexpress_password,
            agency=self.cttexpress_agency,
            customer=self.cttexpress_customer,
            contract=self.cttexpress_contract,
            prod=self.prod_environment,
        )
    
    def _ctt_rest_request(self):
        """Crea el objeto de integración REST usando los parámetros de REST."""
        return CttExpressRestAPI(
            url="https://api.cttexpress.com/integrations",  
            client_id=self.cttexpress_rest_id,
            client_secret=self.cttexpress_rest_secret,
            username=self.cttexpress_rest_user,
            password=self.cttexpress_rest_password,
            client_code=self.cttexpress_rest_agency,
            platform=self.cttexpress_rest_shipping_type  # O el campo que corresponda
        )

    @api.model
    def _ctt_log_request(self, ctt_request):
        """When debug is active requests/responses will be logged in ir.logging

        :param ctt_request: CTT Express request object
        """
        self.log_xml(ctt_request.ctt_last_request, "ctt_request")
        self.log_xml(ctt_request.ctt_last_response, "ctt_response")

    def _ctt_check_error(self, error):
        """Common error checking. We stop the program when an error is returned.

        :param list error: List of tuples in the form of (code, description)
        :raises UserError: Prompt the error to the user
        """
        if not error:
            return
        error_msg = ""
        for code, msg in error:
            if not code:
                continue
            error_msg += "{} - {}\n".format(code, msg)
        if not error_msg:
            return
        raise UserError(_("CTT Express Error:\n\n%s") % error_msg)

    @api.model
    def _cttexpress_format_tracking(self, tracking):
        """Helper to format tracking history strings

        :param OrderedDict tracking: CTT tracking values
        :return str: Tracking line
        """
        status = "{} - [{}] {}".format(
            fields.Datetime.to_string(tracking["StatusDateTime"]),
            tracking["StatusCode"],
            tracking["StatusDescription"],
        )
        if tracking["IncidentCode"]:
            status += " ({}) - {}".format(
                tracking["IncidentCode"], tracking["IncidentDescription"]
            )
        return status

    @api.onchange("cttexpress_shipping_type")
    def _onchange_cttexpress_shipping_type(self):
        """Control service validity according to credentials

        :raises UserError: We list the available services for given credentials
        """
        if not self.cttexpress_shipping_type:
            return
        # Avoid checking if credentials aren't setup or are invalid
        try:
            self.action_ctt_validate_user()
        except UserError:
            return
        ctt_request = self._ctt_request()
        error, service_types = ctt_request.get_service_types()
        self._ctt_log_request(ctt_request)
        self._ctt_check_error(error)
        type_codes, type_descriptions = zip(*service_types)
        if self.cttexpress_shipping_type not in type_codes:
            service_name = dict(
                self._fields["cttexpress_shipping_type"]._description_selection(self.env)
            )[self.cttexpress_shipping_type]
            raise UserError(
                _(
                    "This CTT Express service (%(service_name)s) isn't allowed for "
                    "this account configuration. Please choose one of the followings\n"
                    "%(type_descriptions)s",
                    service_name=service_name,
                    type_descriptions=type_descriptions,
                )
            )

    def action_ctt_validate_user(self):
        """Maps to API's ValidateUser method

        :raises UserError: If the user credentials aren't valid
        """
        self.ensure_one()
        ctt_request = self._ctt_request()
        error = ctt_request.validate_user()
        self._ctt_log_request(ctt_request)
        # For user validation success there's an error return as well.
        # We better ignore it.
        if error[0]:
            self._ctt_check_error(error)

    def _prepare_cttexpress_shipping(self, picking):
        """Convierte los valores de un picking para la API de CTT Express,
        diferenciando entre SOAP y REST.

        :param record picking: Registro de `stock.picking`
        :return dict: Valores preparados para el conector de CTT
        """
        self.ensure_one()
        # Se obtiene el partner remitente: se usa el del almacén o de la compañía
        sender_partner = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        recipient = picking.partner_id
        recipient_entity = picking.partner_id.commercial_partner_id

        # Se crea una referencia basada en el nombre del picking (y la venta si existe)
        reference = picking.name
        if picking.sale_id:
            reference = "{}-{}".format(picking.sale_id.name, reference)

        if self.cttexpress_api == 'REST':
            # Estructura del manifest para la API REST (según la documentación y ejemplo proporcionado)
            manifest = {
                "client_center_code": self.cttexpress_rest_agency,  
                "platform": "ODOO17", 
                "shipping_type_code": self.cttexpress_rest_shipping_type,  
                "client_references": [reference],  
                "shipping_weight_declared": int(picking.shipping_weight) or 1, 
                "item_count": int(picking.number_of_packages) or 1,
                "sender_name": sender_partner.name,
                "sender_country_code": sender_partner.country_id.code or "ES",
                "sender_postal_code": sender_partner.zip or "",
                "sender_address": (sender_partner.street + "," + sender_partner.street2) if sender_partner.street2 else sender_partner.street or "",
                "sender_town": sender_partner.city or "",
                "sender_phones": [sender_partner.phone or ""],
                "recipient_name": recipient.name or (recipient_entity.name if recipient_entity else ""),
                "recipient_country_code": recipient.country_id.code or "ES",
                "recipient_postal_code": recipient.zip or "",
                "recipient_address": (recipient.street + "," + recipient.street2) if recipient.street2 else recipient.street or "",
                "recipient_town": recipient.city or "",
                "recipient_phones": [recipient.phone or ""],
                "shipping_date": date.today().strftime("%Y-%m-%d"),  
                "delivery": {
                    "comments": ""
                },
            }
            _logger.info("Manifest a enviar: %s", json.dumps(manifest, indent=4))
            return manifest
        else:
            # Estructura para SOAP (la versión original)
            return {
                "ClientReference": reference,  
                "ClientDepartmentCode": None,  
                "ItemsCount": picking.number_of_packages,
                "IsClientPodScanRequired": None,  
                "RecipientAddress": recipient.street,
                "RecipientCountry": recipient.country_id.code,
                "RecipientEmail": recipient.email or recipient_entity.email,  
                "RecipientSMS": None,  
                "RecipientMobile": recipient.mobile or recipient_entity.mobile, 
                "RecipientName": recipient.name or recipient_entity.name,
                "RecipientPhone": recipient.phone or recipient_entity.phone,
                "RecipientPostalCode": recipient.zip,
                "RecipientTown": recipient.city,
                "RefundValue": None,  
                "HasReturn": None, 
                "IsSaturdayDelivery": None,  
                "SenderAddress": sender_partner.street,
                "SenderName": sender_partner.name,
                "SenderPhone": sender_partner.phone or "",
                "SenderPostalCode": sender_partner.zip,
                "SenderTown": sender_partner.city,
                "ShippingComments": None,  
                "ShippingTypeCode": self.cttexpress_shipping_type,
                "Weight": int(picking.shipping_weight * 1000) or 1,  
                "PodScanInstructions": None, 
                "IsFragile": None,  
                "RefundTypeCode": None,  
                "CreatedProcessCode": "ODOO",  
                "HasControl": None,  
                "HasFinalManagement": None,  
            }
        
    def rate_shipment(self, order):
        self.ensure_one()
        if self.delivery_type != 'ctt':
            return super().rate_shipment(order)

        # Si usas reglas de precio de Odoo, usa la lógica estándar
        if self.delivery_type == 'ctt' and self.fixed_price is not None:
            return {'success': True, 'price': self.fixed_price, 'error_message': False, 'warning_message': False}
        
        # O si tienes lógica personalizada:
        price = 7.0
        return {
            'success': True,
            'price': price,
            'error_message': False,
            'warning_message': False,
        }

    def send_shipping(self, pickings):
        result = []

        # Only continue if delivery type is CTT
        if self.delivery_type != "ctt":
            _logger.info("Skipping shipping because delivery_type is not CTT.")
            return super().send_shipping(pickings)

        for picking in pickings:
            _logger.info("picking a enviar: %s", json.dumps(picking.read(), indent=4, default=str))
            vals = self._prepare_cttexpress_shipping(picking)
            if self.cttexpress_api == 'REST':
                # Uso de la integración REST
                rest_api = self._ctt_rest_request()
                api_result = rest_api.createShipment(vals)
                tracking = api_result.get("shipping_data", {}).get("shipping_code")
            else:
                # Uso de la integración SOAP (método actual)
                ctt_request = self._ctt_request()
                try:
                    error, documents, tracking = ctt_request.manifest_shipping(vals)
                    self._ctt_check_error(error)
                except Exception as e:
                    _logger.debug("Excepción en manifest_shipping para picking %s: %s", picking.name, e)
                    raise e
                finally:
                    self._ctt_log_request(ctt_request)
            # Se asigna el tracking al picking
            if tracking:
                if not picking.carrier_tracking_ref:
                    picking.carrier_tracking_ref = tracking
                else:
                    picking.carrier_tracking_ref += "," + tracking

            price_result = self.rate_shipment(picking.sale_id)
            exact_price = price_result.get("price", 0.0)
            picking.write({
                'carrier_price': exact_price,
            })

            vals.update({
                "tracking_number": tracking,
                "exact_price": exact_price,
            })
            # Solicitar la etiqueta
            time.sleep(2)
            documents = self.cttexpress_get_label(tracking)
            if not documents:
                attachments = []
            else:
                attachments = documents
            picking.message_post(body=_("CTT Shipping Documents"), attachments=attachments)
            result.append(vals)
        return result

    def cancel_shipment(self, pickings):
        """Cancela la expedición

        :param recordset pickings: pickings `stock.picking` recordset
        :returns boolean: True si la cancelación fue exitosa
        """
        for picking in pickings.filtered("carrier_tracking_ref"):
            if self.cttexpress_api == 'REST':
                rest_api = self._ctt_rest_request()
                try:
                    response = rest_api.cancelShipment(picking.carrier_tracking_ref)
                    _logger.info("Respuesta de cancelShipment (REST): %s", response)
                    if not response:
                        # Si la respuesta está vacía, se asume que no hay error.
                        api_result = {}
                    else:
                        api_result = response.json()
                    _logger.info("Respuesta completa de cancelShipment (REST): %s", json.dumps(api_result, indent=4))
                    # Si en la respuesta existe un campo error, lo procesamos
                    error = api_result.get("error")
                    if error:
                        self._ctt_check_error(error)
                except requests.exceptions.JSONDecodeError as e:
                    _logger.error("Error al decodificar JSON en cancelShipment (REST): %s", e)
                    raise UserError(_("La respuesta de cancelShipment está vacía o no es JSON válido."))
            else:
                # Integración SOAP
                ctt_request = self._ctt_request()
                try:
                    error = ctt_request.cancel_shipping(picking.carrier_tracking_ref)
                    self._ctt_check_error(error)
                    _logger.debug("Cancelación en CTT Express ID %s (tracking: %s)", picking.id, picking.carrier_tracking_ref)
                except Exception as e:
                    _logger.error("Error en cancel_shipping (SOAP) para picking %s: %s", picking.name, e)
                    raise e
                finally:
                    self._ctt_log_request(ctt_request)
            # Asegurarse de que el picking esté en estado 'done'
            if picking.state != 'done':
                picking.state = 'done'
        return True

    def cttexpress_get_label(self, reference):
        """Genera la etiqueta para un picking usando el API de CTT Express.

        :param str reference: Tracking ID (shipping reference)
        :returns list: Lista con una tupla (file_name, file_content) o una lista vacía si no se obtiene la etiqueta.
        """
        self.ensure_one()
        if not reference:
            return []

        if self.cttexpress_api == 'REST':
            # Selección del formato de impresión: si cttexpress_document_model_code es "NOSINGLE", se usa document_format;
            # de lo contrario se usa cttexpress_document_model_code.
            if self.cttexpress_document_model_code == 'NOSINGLE':
                print_format = self.cttexpress_document_format
            else:
                print_format = self.cttexpress_document_model_code

            rest_api = self._ctt_rest_request()
            try:
                api_result = rest_api.printLabel(reference, print_format)
                if "data" in api_result and api_result["data"]:
                    # Se extrae el contenido en Base64
                    label_b64 = api_result["data"][0].get("label", False)
                else:
                    label_b64 = False
            except Exception as e:
                _logger.error("Error en printLabel (REST): %s", e)
                raise e
            if label_b64:
                try:
                    # Decodificamos la etiqueta de Base64 a bytes
                    label_content = base64.b64decode(label_b64)
                except Exception as e:
                    _logger.error("Error al decodificar la etiqueta REST: %s", e)
                    raise e
            else:
                label_content = False
        else:
            # Uso de la integración SOAP (versión actual)
            ctt_request = self._ctt_request()
            try:
                error, label_content = ctt_request.get_documents_multi(
                    reference,
                    model_code=self.cttexpress_document_model_code,
                    kind_code=self.cttexpress_document_format,
                )
                self._ctt_check_error(error)
            except Exception as e:
                _logger.error("Error en get_documents_multi (SOAP): %s", e)
                raise e
            finally:
                self._ctt_log_request(ctt_request)
        
        if not label_content:
            return []

        # En el caso SOAP, label_content puede ser una lista (por ejemplo, una lista de tuplas)
        # Procesamos la respuesta para asegurarnos de obtener un único adjunto en formato (file_name, bytes)
        if isinstance(label_content, list):
            # Tomamos el primer documento (si hay más, podrías adaptarlo según tus necesidades)
            file_doc = label_content[0]
            # file_doc debería ser una tupla (file_name, file_data)
            if isinstance(file_doc, (list, tuple)) and len(file_doc) == 2:
                file_name, file_data = file_doc
                # Si file_data no es bytes, intentamos convertirlo
                if not isinstance(file_data, bytes):
                    try:
                        file_data = bytes(file_data)
                    except Exception as e:
                        _logger.error("Error al convertir el contenido de la etiqueta SOAP a bytes: %s", e)
                        raise e
                label_content = file_data
                file_name = f"ctt_label_{reference}.{self.cttexpress_document_format.lower()}"
            else:
                _logger.error("Formato inesperado en la respuesta SOAP: %s", label_content)
                return []
        else:
            # Si label_content no es una lista, asumimos que ya es el contenido binario
            file_name = f"ctt_label_{reference}.{self.cttexpress_document_format.lower()}"

        return [(file_name, label_content)]

    def cttexpress_tracking_state_update(self, picking):
        """Wildcard method for CTT Express tracking followup

        :param record picking: `stock.picking` record
        """
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        ctt_request = self._ctt_request()
        try:
            error, trackings = ctt_request.get_tracking(picking.carrier_tracking_ref)
            self._ctt_check_error(error)
        except Exception as e:
            raise e
        finally:
            self._ctt_log_request(ctt_request)
        picking.tracking_state_history = "\n".join(
            [self._cttexpress_format_tracking(tracking) for tracking in trackings]
        )
        current_tracking = trackings.pop()
        picking.tracking_state = self._cttexpress_format_tracking(current_tracking)
        picking.delivery_state = CTTEXPRESS_DELIVERY_STATES_STATIC.get(
            current_tracking["StatusCode"], "incidence"
        )

    def get_tracking_link(self, picking):
        """Wildcard method for CTT Express tracking link.

        :param record picking: `stock.picking` record
        :return str: tracking url
        """
        tracking_url = (
            "https://www.cttexpress.com/localizador-de-envios/?sc={}"
        )
        return tracking_url.format(picking.carrier_tracking_ref)

    def get_ask_package_number_custom(self):
        self.ensure_one()
        # Retorna el valor que quieras para influir en el cálculo
        return self.custom_ask_package_number
