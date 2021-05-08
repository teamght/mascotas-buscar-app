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
            response = requests.post(ENDPOINT_REPORTAR_MASCOTA, files=files)

            logging.info('Respuesta: {}'.format(response.text))
            respuesta = json.loads(response.text)['imagen']
            
            if type(respuesta) == bytes:
                return True, respuesta
            else:
                return False, None
        return False, 'No se ha inicializado variable de entorno ENDPOINT_REPORTAR_MASCOTA'
    except Exception as e:
        logging.info('Error al reportar mascota: {}'.format(e))
        return False, None

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    dict_respuesta = {}
    try:
        #Aca se agrega la descripcion del input
        caracteristicas = req.params.get('inputdesc')

        data = req.files['img']
        logging.info(data)
        
        #
        # Guardar imagen en Azure Storage
        #
        current_date = datetime.utcnow().strftime('%Y-%m-%d_%H%M%S.%f')[:-3]
        nombre_imagen = 'image_{}.jpg'.format(current_date)
        file_path = tempfile.gettempdir() + '/' + nombre_imagen

        logging.info(current_date)
        logging.info(file_path)

        with open(file_path, 'wb') as f:
            f.write(data.read())

        blob_name = f"images/{nombre_imagen}"
        logging.info(blob_name)
        logging.info(file_path)
        block_blob_service.create_blob_from_path(CONTAINER_NAME, blob_name, file_path)

        #
        # Registrar en memoria la imagen reportada
        #
        flag, respuesta = reportar_mascota_desaparecida(data)

        if not flag:
            dict_respuesta['mensaje'] = "Hubo un error. Volver a ingresar la imagen."
            return func.HttpResponse(
                dict_respuesta,
                mimetype="application/json",
                status_code=400
            )

        #    #
        #    # Guardar en base de datos
        #    #
        #    #Genero un valor random para la distancia
        distancia = str(random.randint(0,999))+' km.'
        file_name = 'static\\1\\1.21.jpg'
        label = '1'

        flag, respuesta = mongodb.registrar_mascota_reportada(encoded_string=imagen_base, image_path=file_name, label, caracteristicas, distancia)
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
