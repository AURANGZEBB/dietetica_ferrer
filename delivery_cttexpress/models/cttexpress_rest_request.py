import requests
import logging
from odoo import _
from odoo.exceptions import UserError

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
        self.load_token()

    def load_token(self):
        """Solicita y almacena el token de acceso a la API REST."""
        token_url = "https://es-ctt-integration-clients-pool-ids.auth.eu-central-1.amazoncognito.com/oauth2/token"
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
            self.token_expires = result.get("expires_in")
        except Exception as e:
            _logger.error("Error al obtener token: %s", e)
            raise

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
            response = self.session.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result
        except Exception as e:
            _logger.error("Error en createShipment: %s", e)
            raise

    def cancelShipment(self, shipping_code):
        """Ejecuta la cancelación de un envío."""
        endpoint = f"/manifest/v1.0/rpc-cancel-shipping-by-shipping-code/{shipping_code}"
        url = self.url + endpoint
        headers = {
            'user_name': self.username,
            'password': self.password,
            'Authorization': 'Bearer ' + (self.token or ''),
            'Content-Type': 'application/json'
        }

        _logger.info("🚚 Enviando cancelShipment a: %s", url)
        _logger.info("🔐 Headers enviados: %s", headers)

        try:
            # Enviar body vacío como en PHP
            response = self.session.post(url, headers=headers, json={})
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
            response = self.session.get(url, headers=headers, params=params)
            response.raise_for_status()
            result = response.json()
            return result
        except Exception as e:
            _logger.error("Error en printLabel: %s", e)
            raise