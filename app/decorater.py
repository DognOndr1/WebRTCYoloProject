def check_active_decorator(func):
    """
    A decorator that checks if the server is active.

    This decorator checks if the server is active before executing the target method.
    If the server is not active, an error message is logged, and the method is not executed.
    """

    def wrapper(self):
        if not self.is_active:
            self.logger.error("Server Aktif Değil")
            return
        return func(self)

    return wrapper
