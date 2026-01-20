from typing import Any, Callable

SubscribeFactory = Callable[[list[str]], Any]
SubscribeFactoryRegistry = dict[str, SubscribeFactory]
