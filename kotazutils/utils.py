import time
import random


def uuid_generator(fixed_hex, as_string=True):
    """
    0x AAAA BBBB BBBB BBBB CCCC
    A - random
    B - timestamp
    c - fixed hex
    """

    def fill(string, length):
        """
        >>> fill("a", 5)
        '0000a'
        """
        return "0" * (length - len(string)) + string

    fixed = int(fixed_hex, 16) if isinstance(fixed_hex, str) else fixed_hex
    random_hex = hex(random.getrandbits(16))[2:]
    timestamp_hex = hex(int(time.time() * 1000))[2:]
    fixed = hex(fixed)[2:]
    return fill(random_hex, 4), fill(timestamp_hex, 12), fill(fixed, 4)
