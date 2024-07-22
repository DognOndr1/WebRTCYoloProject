from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class WebServer(ABC):
    """
    Temel bir web sunucusu sınıfı.

    Bu sınıf, bir web sunucusunun temel özelliklerini ve metodlarını tanımlar.
    Web sunucusunun nasıl yapılandırılacağı ve başlatılacağı ile ilgili metodları içerir.
    Bu sınıf bir soyut sınıftır (abstract class) ve doğrudan örneği alınamaz. 
    Türetilmiş sınıflar, belirli metodları implement etmek zorundadır.

    Attributes:
        host (str): Sunucunun çalışacağı ana makine adı veya IP adresi.
        port (int): Sunucunun dinleyeceği port numarası.
        is_active (bool): Sunucunun aktif olup olmadığını belirten bir bayrak.
        debug (bool): Hata ayıklama modunu etkinleştiren bir bayrak.

    Methods:
        __post_init__(): Başlangıçta `host` ve `port` parametrelerinin doğruluğunu kontrol eder.
        server(): Bu metod, sunucu yapılandırmasını ve başlatılmasını içermelidir. 
                  Türetilmiş sınıflarda implementasyon gerektirir.
        run(): Bu metod, sunucunun aktif olup olmadığını kontrol eder ve sunucuyu başlatır. 
               Türetilmiş sınıflarda implementasyon gerektirir.
    """
    host: str
    port: int
    is_active: bool
    debug: bool

    def __post_init__(self):
        assert isinstance(self.host, str) and self.host, "Host, bir string olmalı ve boş olmamalıdır."
        assert isinstance(self.port, int) and self.port > 0, "Port, pozitif bir tamsayı olmalıdır."

    @abstractmethod
    def server(self):
        """
        Bu metod, sunucu yapılandırmasını ve başlatılmasını içermelidir.
        Bu metod, türetilmiş sınıflarda implementasyon gerektirir.
        """
        raise NotImplementedError("Server metodu implement edilmelidir.")

    @abstractmethod
    def run(self):
        """
        Bu metod, sunucunun aktif olup olmadığını kontrol eder ve sunucuyu başlatır.
        Bu metod, türetilmiş sınıflarda implementasyon gerektirir.
        """
        raise NotImplementedError("Run metodu implement edilmelidir.")
