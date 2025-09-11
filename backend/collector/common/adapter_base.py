from abc import ABC, abstractmethod


class TickerAdapter(ABC):
@abstractmethod
def loop(self):
    ...