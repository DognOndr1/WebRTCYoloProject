from loguru import logger
import sys
from dataclasses import dataclass

@dataclass
class Logger:
    """
    Loglama işlevselliği sağlayan bir Logger sınıfı.

    Bu sınıf, Loguru kütüphanesini kullanarak log mesajlarını stdout ve bir dosyaya yazdırır.
    Logların formatını ve dosya rotasını ayarlamak için yapılandırma sağlar.

    Attributes:
        log_file (str): Logların yazılacağı dosya yolu.
        log_format (str): Log mesajlarının formatı.
        rotation (str): Log dosyasının rotasyonunu belirleyen parametre.

    Methods:
        __post_init__(): Loguru logger'ını yapılandırır ve ekler.
        info(message: str): Bilgi seviyesinde bir log mesajı yazar.
        error(message: str): Hata seviyesinde bir log mesajı yazar.
        warning(message: str): Uyarı seviyesinde bir log mesajı yazar.
        debug(message: str): Hata ayıklama seviyesinde bir log mesajı yazar.
    """
    
    log_file: str
    log_format: str
    rotation: str

    def __post_init__(self):
        logger.remove()
        logger.add(
                    sys.stdout, 
                    level = "INFO",
                    format= self.log_format,
                    diagnose=True)
        logger.add(
                    self.log_file, 
                    rotation=self.rotation,
                    format=self.log_format + "{line}")

    def info(self, message: str):
        logger.opt(depth=1).info(message)

    def error(self, message: str):
        logger.opt(depth=1).error(message)

    def warning(self, message: str):
        logger.opt(depth=1).warning(message)

    def debug(self, message: str):
        logger.opt(depth=1).debug(message)

