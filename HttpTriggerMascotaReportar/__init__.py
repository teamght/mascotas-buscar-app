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

def reportar_mascota_desaparecida(nombre_imagen):
    '''
    Invocar API para registrar en memoria la nueva imagen del rostro de la mascota
    '''
    logging.info('reportar_mascota_desaparecida')
    try:
        if ENDPOINT_REPORTAR_MASCOTA:
            file_imagen = open(nombre_imagen,'rb')
            files = {'upload_file': file_imagen}
            response = requests.post(ENDPOINT_REPORTAR_MASCOTA, files=files)
            logging.info('Respuesta: {}'.format(response.text))
            respuesta = json.loads(response.text)
            
            file_imagen.close()
            return True, respuesta
        return False, 'No se ha inicializado variable de entorno ENDPOINT_REPORTAR_MASCOTA'
    except Exception as e:
        logging.info('Error al reportar mascota: {}'.format(e))
        file_imagen.close()
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
        ## Respuesta:
        # dict_respuesta['file_name']
        # dict_respuesta['label']

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
        blob_name = f"images/{nombre_imagen}"
        logging.info(blob_name)
        logging.info(file_path)
        block_blob_service.create_blob_from_path(CONTAINER_NAME, blob_name, file_path)

        #
        # Guardar en base de datos
        #
        # Genero un valor random para la distancia
        distancia = str(random.randint(0,999))+' km.'
        file_name = dict_respuesta['file_name']
        label = dict_respuesta['label']
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())

        flag, respuesta = mongodb.registrar_mascota_reportada(encoded_string=encoded_string, image_path=file_name, label, caracteristicas, distancia)
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
