from abc import ABC, abstractmethod


class APIOptions(ABC):

    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_options_for_symbol_and_expiration(self, symbol: str, expiration: str, put_call="BOTH") -> {}:
        pass

    @abstractmethod
    def get_options_for_symbol(self, symbol: str, put_call="BOTH", look_a_heads=2) -> list:
        pass

    @abstractmethod
    def get_stock_price_for_symbol(self, symbol: str) -> {}:
        pass
