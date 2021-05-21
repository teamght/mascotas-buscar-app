import logging

import base64
import json
import requests
import os
import io
from datetime import datetime

import azure.functions as func

from ..src.util import ENDPOINT_DOG_FACE_CROPPER, ENDPOINT_TENSORFLOW_MODEL


def obtener_imagen_recortada(data_imagen):
    '''
    Invocar API de detección y recorte de rostro de perro
    Request: Imagen en base 64 del perro
    Response: Imagen en base 64 del rostro del perro
    '''
    print('obtener_imagen_recortada')
    try:
        if ENDPOINT_DOG_FACE_CROPPER:
            files = {'upload_file': data_imagen}
            response = requests.post(ENDPOINT_DOG_FACE_CROPPER, files=files)

            logging.info('Respuesta: {}'.format(type(json.loads(response.text)['img'])))
            
            imagen_bytes = base64.b64decode(json.loads(response.text)['img'])
            logging.info('API de recorte e identificación de rostro de perro retornó: {}'.format(type(imagen_bytes)))

            if type(imagen_bytes) == bytes:
                return True, imagen_bytes
            else:
                return False, None
        return False, 'No se ha inicializado variable de entorno ENDPOINT_DOG_FACE_CROPPER'
    except Exception as e:
        logging.info('Error al identificar y recortar imagen: {}'.format(e))
        return False, None

def obtener_mascotas_parecidas(image_bytes):
    '''
    Invocar API de detección de perros parecidos a partir de la foto del rostro
    Request: Imagen en base 64 del rostro del perro
    Response: JSON con los datos de los perros más parecidos
    '''
    print('obtener_mascotas_parecidas')
    try:
        if ENDPOINT_TENSORFLOW_MODEL:
            files = {'upload_file': image_bytes}
            response = requests.post(ENDPOINT_TENSORFLOW_MODEL, files=files)

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
        data = req.files['img']
        logging.info(data)

        flag, img_recortada = obtener_imagen_recortada(data)
        
        if flag == False:
            return func.HttpResponse(
                "Hubo un error. Volver a ingresar la imagen.",
                status_code=400
            )
        
        dict_respuesta["imagen_recortada"] = base64.b64encode(img_recortada).decode("utf-8")

        flag, respuesta = obtener_mascotas_parecidas(img_recortada)
        if flag == False:
            return func.HttpResponse(
                "Hubo un error al mostrar mascotas. Volver a ingresar la imagen.",
                status_code=500
            )
        
        if 'parecidos' in respuesta:
            for key,value in respuesta['parecidos'].items():
                dict_respuesta[key] = {'rutas':value['image'],
                                        'caracteristicas':value['caracteristicas'],
                                        'distancia':value['distancia']}
        
        dict_respuesta['codigo'] = respuesta['codigo']
        dict_respuesta['mensaje'] = respuesta['mensaje']
    except ValueError as e:
        logging.info('Ocurrió un error')
        logging.info(e)
        return func.HttpResponse(
            "Hubo un error. Volver a ingresar la imagen.",
            status_code=500
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
