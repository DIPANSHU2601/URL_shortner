ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
BASE = len(ALPHABET)

def encode_base62(num: int) -> str:
    if num == 0:
        return ALPHABET[0]
    encoded = []
    while num > 0:
        num, rem = divmod(num, BASE)
        encoded.append(ALPHABET[rem])
    return "".join(reversed(encoded))
