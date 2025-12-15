# import os, base64

# print(base64.urlsafe_b64encode(os.urandom(32)).decode())

# from typing import Protocol, Callable

# class HmacHasherPort(Protocol):
#     def get_version(self): ...

# class HmacHasher(HmacHasherPort):
#     def __init__(self, version: int) -> None:
#         self._version = version

#     def get_version(self):
#         return self._version


# def hmac_provider_v1(version: int) -> Callable[[], HmacHasher]:
#     return lambda: HmacHasher(version)

# def hmac_provider_v2() -> Callable[[int], HmacHasher]:
#     return lambda version: HmacHasher(version)

# def hmac_provider_v3() -> HmacHasher:
#     return HmacHasher(3)

# hmac_v1 = hmac_provider_v1(1)
# print(hmac_v1().get_version())

# hmac_v2 = hmac_provider_v2()
# print(hmac_v2(2).get_version())

# hmac_v3 = hmac_provider_v3()
# print(hmac_v3.get_version())
