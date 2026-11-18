from slowapi import Limiter
from slowapi.util import get_remote_address

# Per-IP limits on the endpoints that cost money (uploads embed text, questions call the model)
limiter = Limiter(key_func=get_remote_address)
