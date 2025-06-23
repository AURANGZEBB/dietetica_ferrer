# Copyright 2022 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

# Master Data provided by CTT Express

CTTEXPRESS_SERVICES = [
    ("01V", "VALIJA UNITOQUE DIARIA"),
    ("02V", "VALIJA BITOQUE DIARIA"),
    ("03V", "VALIJA UNITOQUE 3 DIAS"),
    ("04V", "VALIJA BITOQUE 3 DÍAS"),
    ("10H", "10 HORAS"),
    ("13A", "13 HORAS ISLAS"),
    ("13H", "14 HORAS"),
    ("13M", "FRANCIA 13M"),
    ("13O", "OPTICA"),
    ("14H", "PREMIUM EMPRESAS 14h"),
    ("18M", "FRANCIA 18M"),
    ("19A", "CANARIAS DOCUMENTACIÓN"),
    ("19E", "24H E-COMMERCE"),
    ("19H", "24 HORAS"),
    ("48E", "48 E-COMMERCE"),
    ("48H", "48 HORAS"),
    ("48M", "48 CANARIAS MARITIMO"),
    ("48N", "48H"),
    ("48P", "48 E-COMMERCES"),
    ("63E", "RECOGERAN E-COMMERCE CANARIAS"),
    ("63P", "PUNTOS CERCANÍA"),
    ("63R", "RECOGERAN EN AGENCIA"),
    ("80I", "GLOBAL EXPRESS"),
    ("80R", "GLOBAL RECOGIDA INTERNACIONAL"),
    ("80T", "GLOBAL EXPRESS"),
    ("81I", "TERRESTRE ECONOMY"),
    ("81R", "RECOGIDA TERRESTRE ECONOMY"),
    ("81T", "TERRESTRE ECONOMY"),
    ("830", "8.30 HORAS"),
    ("93T", "TERRESTE E-COMMERCE"),
]

REST_CTTEXPRESS_SERVICES = [
    ("C24", "CTT 24"),
    ("C48", "CTT 48"),
    ("C14", "CTT 14"),
    ("C10", "CTT 10"),
    ("CCA24", "CTT CANARIAS AEREOS"),
    ("CCAE", "CTT CANARIAS DOCUMENTACIÓN"),
    ("CCAM", "CTT CANARIAS MARÍTIMO"),
    ("CBA24", "CTT BALEARES EXPRESS"),
    ("CBA48", "CTT BALEARES ECONOMY"),
    ("CIEX", "CTT INTERNACIONAL EXPRESS"),
    ("CIES", "CTT INTERNACIONAL ECONOMY"),
]

CTTEXPRESS_DELIVERY_STATES_STATIC = {
    "0": "shipping_recorded_in_carrier",  # PENDIENTE DE ENTRADA EN RED
    "1": "in_transit",  # EN TRANSITO
    "2": "in_transit",  # EN REPARTO
    "3": "customer_delivered",  # ENTREGADO
    "4": "incidence",  # INCIDENCIA
    "5": "incidence",  # DEVOLUCION
    "6": "in_transit",  # RECOGERAN EN AGENCIA
    "7": "incidence",  # RECANALIZADO
    "8": "incidence",  # NO REALIZADO
    "9": "incidence",  # RETORNADO
    "10": "in_transit",  # EN ADUANA
    "11": "in_transit",  # EN AGENCIA
    "12": "customer_delivered",  # ENTREGA PARCIAL
    "13": "incidence",  # POSICIONADO EN PER
    "50": "incidence",  # DEVOLUCION DESDE PLATAFORMA
    "51": "incidence",  # DEVOLUCION SINIESTROS MERCANCIA YA EVALUADA
    "70": "incidence",  # RECANALIZADO A SINIESTROS POR PLATAFORMA
    "71": "incidence",  # REENCAMINADO
    "90": "canceled_shipment",  # ANULADO
    "91": "in_transit",  # REACTIVACION ENVIO (TOL)
    "99": "in_transit",  # COMPUESTO
}
