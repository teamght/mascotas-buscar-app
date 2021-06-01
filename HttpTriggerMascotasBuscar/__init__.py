import logging

import base64
import json
import requests
import os
import io
from datetime import datetime

import azure.functions as func

from ..src.util import ENDPOINT_TENSORFLOW_MODEL


def obtener_mascotas_parecidas(image_bytes, geolocalizacion):
    '''
    Invocar API de detección de perros parecidos a partir de la foto del rostro
    Request: Imagen en base 64 del rostro del perro
    Response: JSON con los datos de los perros más parecidos
    '''
    print('obtener_mascotas_parecidas')
    try:
        if ENDPOINT_TENSORFLOW_MODEL:
            files = {'imagen_bytes': image_bytes, 'geolocalizacion': geolocalizacion}
            response = requests.post(ENDPOINT_TENSORFLOW_MODEL, json=files)

            logging.info('Respuesta: {}'.format(response.text))
            predictions = json.loads(response.text)
            
            return True, predictions
        return False, 'No se ha inicializado variable de entorno ENDPOINT_TENSORFLOW_MODEL'
    except Exception as e:
        logging.info('Error al predecir imágenes: {}'.format(e))
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
        geolocalizacion = data['geolocalizacion']

        flag, respuesta = obtener_mascotas_parecidas(bytes_imagen, geolocalizacion)
        
        if 'parecidos' in respuesta:
            for key,value in respuesta['resultados'].items():
                dict_respuesta[key] = {'image':value['image'],
                                        'caracteristicas':value['caracteristicas'],
                                        'ubicacion':value['ubicacion'],
                                        'label':value['label'],
                                        'distancia':value['distancia'],
                                        'fecha_perdida':value['fecha_perdida'],
                                        'timestamp_perdida':value['timestamp_perdida']
                                        }
        
        if 'imagen_recortada' in respuesta:
            dict_respuesta["imagen_recortada"] = respuesta["imagen_recortada"]
        
        dict_respuesta['codigo'] = respuesta['codigo']
        dict_respuesta['mensaje'] = respuesta['mensaje']
    except ValueError as e:
        logging.info('Ocurrió un error')
        logging.info(e)
        dict_respuesta['codigo'] = 503
        dict_respuesta['mensaje'] = "Hubo un error. Volver a ingresar la imagen."
        return func.HttpResponse(
            json.dumps(dict_respuesta),
            status_code=503
        )
    
    if data:
        return func.HttpResponse(
            json.dumps(dict_respuesta),
            mimetype="application/json",
        )
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )
