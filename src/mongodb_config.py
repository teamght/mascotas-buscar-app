import logging

import pymongo
from datetime import datetime

from .util import DB_URI, DB_NAME, DB_COLECCION

class MongoDB_Config():

    client = pymongo.MongoClient(DB_URI)
    db = client[DB_NAME]
    
    def __init__(self):
        pass
    
    def registrar_mascota_reportada(self, encoded_string, full_file_name, image_path, label, caracteristicas, distancia):
        logging.info('Inicio obtener data mascotas de base de datos ({})'.format(datetime.now()))
        try:
            self.db[DB_COLECCION].insert_one({
                'image':encoded_string, 
                'file_name':image_path,
                'full_file_name':full_file_name,
                'label':label,
                'caracteristicas':caracteristicas,
                'distancia':distancia})
            return True, 'Se logró registrar mascota como desaparecida.'
        except Exception as e:
            logging.info('Hubo un error en obtener data mascotas de base de datos ({})'.format(datetime.now()))
            logging.info('Hubo un error. {}'.format(e))
            return False, None
