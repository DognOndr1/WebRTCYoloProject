import toml
import os



class ConfigLoader:
    """
    Konfigürasyon dosyalarını yükleyen bir sınıf.

    Attributes:
        config_file (str): Yüklemek istenen konfigürasyon dosyasının adı.

    Methods:
        __init__(config_file: str): Konfigürasyon dosyasının adını ayarlayan yapıcı metod.
        load_configs(): Konfigürasyon dosyasını yükler ve içeriğini döndürür.

    Example:
        >>> config_loader = ConfigLoader("config.toml")
        >>> configs = config_loader.load_configs()
        >>> print(configs)
        {'database': {'host': 'localhost', 'port': 5432}, 'api': {'key': 'your_api_key'}}
    """

    def __init__(self, config_file: str):
        
        self.config_file = config_file

    def load_configs(self):

        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        config_path = os.path.join(base_dir, 'configs', self.config_file)
        
        configs = toml.load(config_path)

        return configs


