import valkey

def get_cache():
    return valkey.Valkey(host='localhost', port=6379)

def get_cache_key(name):
    return f"fruit_{name}"
