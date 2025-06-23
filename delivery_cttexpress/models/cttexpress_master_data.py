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

CTTEXPRESS_REST_DELIVERY_STATES = {  # REST
    "0000": "shipping_recorded_in_carrier",  # MANIFESTADO
    "0010": "shipping_recorded_in_carrier",  # RECEPCIÓN PROVISIONAL
    "0020": "shipping_recorded_in_carrier",  # PENDIENTE DE DEPOSITAR EN PUNTO
    "0030": "shipping_recorded_in_carrier",  # DEPOSITADO EN PUNTO
    "0300": "shipping_recorded_in_carrier",  # RECOGIDA ASIGNADA
    "0400": "canceled_shipment",             # RECOGIDA ANULADA
    "0500": "in_transit",                     # ENVÍO RECOGIDO
    "0600": "incidence",                      # RECOGIDA FALLIDA
    "0700": "in_transit",                     # DELEGACIÓN DE ORIGEN
    "0900": "in_transit",                     # EN TRÁNSITO
    "1000": "in_transit",                     # DELEGACIÓN DE TRÁNSITO
    "1100": "incidence",                      # MAL TRANSITADO
    "1200": "in_transit",                     # DELEGACIÓN DE DESTINO
    "1500": "in_transit",                     # EN REPARTO
    "1600": "incidence",                      # REPARTO FALLIDO
    "1700": "incidence",                      # ENVÍO ESTACIONADO
    "1800": "in_transit",                     # ESTACIONADO UBICADO
    "1900": "in_transit",                     # PENDIENTE DE EXTRACCIÓN
    "2100": "customer_delivered",             # ENTREGADO
    "2200": "customer_delivered",             # ENTREGA PARCIAL
    "2300": "shipping_recorded_in_carrier",   # PENDIENTE DE ADMISIÓN
    "2310": "shipping_recorded_in_carrier",   # DISPONIBLE EN PUNTO
    "2400": "in_transit",                     # NUEVO REPARTO
    "2500": "canceled_shipment",              # DEVOLUCIÓN
    "2600": "in_transit",                     # REEXPEDICIÓN
    "2700": "in_transit",                     # ALMACÉN REGULADOR
    "2900": "in_transit",                     # RECOGER EN DELEGACIÓN
    "3000": "canceled_shipment",              # ENVÍO ANULADO
    "3900": "in_transit",                     # TRÁNSITO INTERNACIONAL
    "3901": "in_transit",                     # GESTIÓN ADUANERA
    "3902": "in_transit",                     # DESPACHADO
    "3903": "in_transit",                     # REVISIÓN ADUANERA
    "3904": "in_transit",                     # INSPECCIÓN ADUANERA
}

CTTEXPRESS_REST_DELIVERY_STATES_LABELS = {
    "0000": "Manifestado",
    "0010": "Recepción provisional",
    "0020": "Pendiente de depositar en punto",
    "0030": "Depositado en punto",
    "0300": "Recogida asignada",
    "0400": "Recogida anulada",
    "0500": "En tránsito",
    "0600": "Recogida fallida",
    "0700": "Delegación de origen",
    "0900": "En tránsito",
    "1000": "Delegación de tránsito",
    "1100": "Mal transitado",
    "1200": "Delegación de destino",
    "1500": "En reparto",
    "1600": "Reparto fallido",
    "1700": "Envío estacionado",
    "1800": "Estacionado ubicado",
    "1900": "Pendiente de extracción",
    "2100": "Entregado",
    "2200": "Entrega parcial",
    "2300": "Pendiente de admisión",
    "2310": "Disponible en punto",
    "2400": "Nuevo reparto",
    "2500": "Devuelto",
    "2600": "Reexpedición",
    "2700": "Almacén regulador",
    "2900": "Recoger en delegación",
    "3000": "Envío anulado",
    "3900": "Tránsito internacional",
    "3901": "Gestión aduanera",
    "3902": "Despachado",
    "3903": "Revisión aduanera",
    "3904": "Inspección aduanera",
}
