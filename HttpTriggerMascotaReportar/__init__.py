import logging

import os
import json
import base64
import requests
import random
from datetime import datetime

import tempfile
import azure.functions as func
from azure.storage.blob import BlockBlobService

from ..src.util import ENDPOINT_REPORTAR_MASCOTA, ACCOUNT_NAME, ACCOUNT_KEY, CONTAINER_NAME
from ..src.mongodb_config import MongoDB_Config


mongodb = MongoDB_Config()

#
# Configuración de cuenta de Azure
#
block_blob_service = BlockBlobService(
    account_name=ACCOUNT_NAME,
    account_key=ACCOUNT_KEY
)

def reportar_mascota_desaparecida(image_bytes):
    '''
    Invocar API para registrar en memoria la nueva imagen del rostro de la mascota
    '''
    logging.info('reportar_mascota_desaparecida')
    try:
        if ENDPOINT_REPORTAR_MASCOTA:
            files = {'upload_file': image_bytes}
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
        data = req.json
        logging.info(data)
        if data is None:
            return {'mensaje':'Debe ingresar una imagen.', 'codigo': 400}
        if not 'imagen' in data:
            return {'mensaje':'Debe ingresar una imagen.', 'codigo': 400}
        
        bytes_imagen = data['imagen']
        caracteristicas = data['caracteristicas']
        geolocalizacion = data['geolocalizacion']
        
        #
        # Crear archivo temporal
        #
        current_date = datetime.utcnow().strftime('%Y-%m-%d_%H%M%S.%f')[:-3]
        nombre_imagen = 'image_{}.jpg'.format(current_date)
        file_path = tempfile.gettempdir() + '/' + nombre_imagen

        logging.info(current_date)
        logging.info(file_path)

        with open(file_path, 'wb') as f:
            f.write(data.read())
        
        #
        # Registrar en memoria la imagen reportada
        #
        flag, dict_respuesta = reportar_mascota_desaparecida(file_path)
        ## Respuesta variable dict_respuesta:
        # dict_respuesta['file_name']
        # dict_respuesta['label']
        # dict_respuesta['full_file_name']

        if not flag:
            dict_respuesta['mensaje'] = "Hubo un error. Volver a ingresar la imagen."
            return func.HttpResponse(
                dict_respuesta,
                mimetype="application/json",
                status_code=400
            )

        #
        # Guardar imagen en Azure Storage
        #
        # Nombre con el que se guardará en Azure Storage
        full_file_name = dict_respuesta['full_file_name']
        logging.info(full_file_name)
        logging.info(file_path)
        block_blob_service.create_blob_from_path(CONTAINER_NAME, full_file_name, file_path)

        #
        # Guardar en base de datos
        #
        file_name = dict_respuesta['file_name']
        label = dict_respuesta['label']
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())

        flag, respuesta = mongodb.registrar_mascota_reportada(encoded_string=encoded_string, full_file_name=full_file_name, image_path=file_name, label=label, caracteristicas=caracteristicas, ubicacion=geolocalizacion)
        if not flag:
            dict_respuesta['mensaje'] = "Hubo un error. Volver a ingresar la imagen."
            return func.HttpResponse(
                dict_respuesta,
                mimetype="application/json",
                status_code=500
            )
        
        dict_respuesta['mensaje'] = respuesta
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
