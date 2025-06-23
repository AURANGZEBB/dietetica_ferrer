import requests
import logging
from odoo import _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import os
import json

TOKEN_FILE = "/tmp/cttexpress_token.json"  
_logger = logging.getLogger(__name__)

class CttExpressRestAPI:
    def __init__(self, url, client_id, client_secret, username, password, client_code, platform):
        self.url = url
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.client_code = client_code
        self.platform = platform
        self.token = None
        self.token_expires = None
        self.session = requests.Session()
        
        # ✅ Primero intentar cargar el token del archivo
        if not self.load_token_from_file():
            self.load_token()

    def load_token(self):
        """Solicita un nuevo token y lo guarda en un archivo JSON."""
        token_url = "https://api.cttexpress.com/integrations/oauth2/token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "urn:com:ctt-express:integration-clients:scopes:common/ALL",
            "grant_type": "client_credentials"
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        try:
            response = self.session.post(token_url, data=payload, headers=headers)
            response.raise_for_status()
            result = response.json()

            self.token = result.get("access_token")
            expires_in = result.get("expires_in", 0)
            self.token_expires = datetime.utcnow() + timedelta(seconds=expires_in)

            token_data = {
                "access_token": self.token,
                "expires_at": self.token_expires.isoformat()
            }

            with open(TOKEN_FILE, "w") as f:
                json.dump(token_data, f)

            _logger.info("🔐 [CTT REST] Nuevo token obtenido y guardado. Expira a las %s", self.token_expires)

        except Exception as e:
            _logger.error("❌ [CTT REST] Error al obtener o guardar el token: %s", e)
            raise

    def load_token_from_file(self):
        """Carga el token desde un archivo si aún no ha expirado."""
        if not os.path.exists(TOKEN_FILE):
            _logger.info("🔍 [CTT REST] No se encontró archivo de token. Se solicitará uno nuevo.")
            return False

        try:
            with open(TOKEN_FILE, "r") as f:
                data = json.load(f)

            token = data.get("access_token")
            expires_at_str = data.get("expires_at")

            if not token or not expires_at_str:
                _logger.warning("⚠️ [CTT REST] El archivo de token está incompleto. Se solicitará uno nuevo.")
                return False

            expires_at = datetime.fromisoformat(expires_at_str)
            if datetime.utcnow() >= expires_at:
                _logger.info("⏰ [CTT REST] El token ha expirado. Se solicitará uno nuevo.")
                return False

            self.token = token
            self.token_expires = expires_at
            _logger.info("✅ [CTT REST] Token válido cargado desde archivo. Expira a las %s", expires_at)
            return True

        except Exception as e:
            _logger.error("❌ [CTT REST] Error al cargar token desde archivo: %s", e)
            return False
        
    def _request_with_token_refresh(self, method, url, **kwargs):
        """Envía una petición y si da 401, refresca el token y reintenta una vez."""
        headers = kwargs.pop("headers", self.get_headers())
        response = self.session.request(method, url, headers=headers, **kwargs)

        if response.status_code == 401:
            _logger.warning("🔁 Token expirado o inválido. Reintentando tras renovación.")
            self.load_token()
            headers = self.get_headers()
            response = self.session.request(method, url, headers=headers, **kwargs)

        response.raise_for_status()
        return response

    def get_headers(self):
        """Prepara los encabezados para las peticiones a la API REST."""
        return {
            'user_name': self.username,
            'password': self.password,
            'Authorization': 'Bearer ' + (self.token or ''),
            'Content-Type': 'application/json'
        }

    def createShipment(self, data):
        """Ejecuta la creación de un envío."""
        endpoint = "/manifest/v1.0/shippings"
        url = self.url + endpoint
        headers = self.get_headers()
        try:
            response = self._request_with_token_refresh("POST", url, json=data)
            return response.json()
        except Exception as e:
            _logger.error("Error en createShipment: %s", e)
            raise

    def cancelShipment(self, shipping_code):
        """Ejecuta la cancelación de un envío."""
        endpoint = f"/manifest/v1.0/rpc-cancel-shipping-by-shipping-code/{shipping_code}"
        url = self.url + endpoint
        headers = self.get_headers()

        _logger.info("🚚 Enviando cancelShipment a: %s", url)
        _logger.info("🔐 Headers enviados: %s", headers)

        try:
            # Enviar body vacío como en PHP
            response = self._request_with_token_refresh("POST", url, json={})
            _logger.info("📬 Status code recibido: %s", response.status_code)
            _logger.info("📨 Respuesta recibida: %s", response.text)

            response.raise_for_status()

            if response.status_code == 201:
                _logger.info("✅ Cancelación exitosa de envío %s", shipping_code)
                return {"status": "success"}

            if response.text.strip():
                return response.json()
            else:
                return {}

        except requests.exceptions.HTTPError as e:
            _logger.error("❌ Error HTTP en cancelShipment: %s", e)
            _logger.error("🔁 Código: %s", response.status_code)
            _logger.error("📄 Contenido completo: %s", response.text)
            raise UserError(_("CTT Express respondió con error:\n%s") % response.text)
        except Exception as e:
            _logger.error("🔥 Error inesperado en cancelShipment: %s", e)
            raise

    def printLabel(self, shipping_code, print_format):
        """Solicita la impresión de la etiqueta de un envío."""
        endpoint = f"/trf/labelling/v1.0/shippings/{shipping_code}/shipping-labels"
        params = {
            "label_type_code": "PDF",
            "model_type_code": print_format,
            "label_offset": 1
        }
        url = self.url + endpoint
        headers = self.get_headers()
        try:
            response = self._request_with_token_refresh("GET", url, params=params)
            return response.json()
        except Exception as e:
            _logger.error("Error en printLabel: %s", e)
            raise

    def parse_datetime_safe(self, date_str):
        try:
            # Intentamos usar fromisoformat (Python 3.7+)
            if date_str.endswith('Z'):
                date_str = date_str.replace('Z', '+00:00')  # fromisoformat no entiende 'Z'
            return datetime.fromisoformat(date_str)
        except Exception:
            # Si falla, lo dejamos en None
            _logger.warning("⚠️ No se pudo parsear fecha (formato raro): %s", date_str)
            return None

    def getTracking(self, shipping_code):
        """Obtiene el historial de tracking para un envío concreto en la API REST."""
        endpoint = f"/trf/item-history-api/history/{shipping_code}"
        url = self.url + endpoint
        headers = self.get_headers()
        params = {
            "view": "APITRACK",
            "showItems": "false",
        }
        _logger.info("📦 Solicitando tracking de envío %s a URL: %s con params: %s", shipping_code, url, params)

        try:
            response = self._request_with_token_refresh("GET", url, params=params)
            result = response.json()
            _logger.info("📨 Tracking obtenido para %s: %s", shipping_code, result)

            shipping_history = result.get("data", {}).get("shipping_history", {})
            events = shipping_history.get("events", [])

            if not events:
                return []

            trackings = []
            for event in events:
                event_date_str = event.get("event_date")
                event_date = self.parse_datetime_safe(event_date_str)

                tracking = {
                    "StatusDateTime": event_date,
                    "StatusCode": event.get("code", ""),
                    "StatusDescription": event.get("description", ""),
                    "IncidentCode": None,
                    "IncidentDescription": None,
                }
                trackings.append(tracking)

            return trackings

        except Exception as e:
            _logger.error("❌ Error en getTracking (REST): %s", e)
            raise

    def get_bulk_tracking(self, client_center_code, shipping_date=None, page_limit=50, page_offsets=1, order_by=None):
        """Obtiene información de seguimiento de múltiples envíos por fecha.

        :param client_center_code: Código del centro del cliente
        :param shipping_date: Fecha o rango de fechas (formato: YYYY-MM-DD o YYYY-MM-DD[range]YYYY-MM-DD)
        :param page_limit: Cantidad de registros por página
        :param page_offsets: Página a consultar
        :param order_by: Campo de ordenación (ej: "-shipping_date")
        :return: Diccionario con los resultados de la API
        """
        endpoint = "/trf/web-tracking/v1.0/shippings"
        url = self.url + endpoint
        headers = {
            'Authorization': 'Bearer ' + (self.token or ''),
            'Content-Type': 'application/json',
        }

        params = {
            "client_center_code": client_center_code,
            "mapping_table_code": "APITRACK",
            "page_limit": page_limit,
            "page_offsets": page_offsets
        }

        if shipping_date:
            params["shipping_date"] = shipping_date
        if order_by:
            params["order_by"] = order_by

        _logger.info("🔍 Llamando a seguimiento masivo: %s con params: %s", url, params)

        try:
            response = self._request_with_token_refresh("GET", url, params=params)
            return response.json()
        except Exception as e:
            _logger.error("❌ Error en get_bulk_tracking: %s", e)
            raise UserError(_("Error al obtener el seguimiento masivo: %s") % str(e))