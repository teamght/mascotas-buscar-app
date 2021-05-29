import logging

import json
import base64
import requests
from datetime import datetime

import tempfile
import azure.functions as func

from ..src.util import ENDPOINT_REPORTAR_MASCOTA


def reportar_mascota_desaparecida(image_bytes, geolocalizacion, caracteristicas, fecha_de_perdida):
    '''
    Invocar API para registrar en memoria la nueva imagen del rostro de la mascota
    '''
    logging.info('reportar_mascota_desaparecida')
    try:
        if ENDPOINT_REPORTAR_MASCOTA:
            files = {'imagen_bytes': image_bytes, 
                     'geolocalizacion': geolocalizacion, 
                     'caracteristicas':caracteristicas,
                     'fecha_de_perdida': fecha_de_perdida}
            response = requests.post(ENDPOINT_REPORTAR_MASCOTA, json=files)
            logging.info('Respuesta: {}'.format(response.text))
            respuesta = json.loads(response.text)
            
            return True, respuesta
        return False, 'No se ha inicializado variable de entorno ENDPOINT_REPORTAR_MASCOTA'
    except Exception as e:
        logging.info('Error al reportar mascota: {}'.format(e))
        return False, None

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    dict_respuesta = {}
    try:
        data = req.get_json()
        logging.info(data)
        if data is None:
            return {'mensaje':'Debe ingresar una imagen.', 'codigo': 400}
        if not 'imagen' in data:
            return {'mensaje':'Debe ingresar una imagen.', 'codigo': 400}
        
        bytes_imagen = data['imagen']
        caracteristicas = data['caracteristicas']
        geolocalizacion = data['geolocalizacion']
        fecha_de_perdida = data['fecha_de_perdida']
        
        #
        # Registrar en memoria la imagen reportada
        #
        flag, dict_respuesta = reportar_mascota_desaparecida(bytes_imagen, geolocalizacion, caracteristicas, fecha_de_perdida)
        ## Respuesta variable dict_respuesta:
        # dict_respuesta['file_name']
        # dict_respuesta['label']
        # dict_respuesta['full_file_name']
        # dict_respuesta['codigo']
        # dict_respuesta['mensaje']

        if not flag:
            dict_respuesta['mensaje'] = "Hubo un error. Volver a ingresar la imagen."
            return func.HttpResponse(
                dict_respuesta,
                mimetype="application/json",
                status_code=400
            )

        return func.HttpResponse(
            json.dumps(dict_respuesta),
            mimetype="application/json",
        )
    
    except Exception as e:
        logging.info('Ocurrió un error')
        logging.info(e)
        dict_respuesta['mensaje'] = "Hubo un error. Volver a ingresar la imagen."
        return func.HttpResponse(
            dict_respuesta,
            mimetype="application/json",
            status_code=500
        )
