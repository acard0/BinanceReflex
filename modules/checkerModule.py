import CONFIG
import misc.utils

from misc.utils import cprint
from binance import ThreadedWebsocketManager
from binance.exceptions import BinanceAPIException
from events import Events

class checkerModuleAPI:
    def __init__(self, client, identifier) -> None:
        self.client = client
        self.identifier = identifier
        self.onTick = Events()
        
    def update(self):
        current = misc.utils.getMs()
        try:
            symbol = self.client.get_symbol_ticker(symbol = CONFIG.TARGET_SYMBOL)
            cprint(0,f'{symbol}')          
        except BinanceAPIException as e:
            symbol = e
        
        self.onTick.on_change(symbol, misc.utils.getMs() - current)
        return symbol, misc.utils.getMs() - current

class checkerModuleSocket:
    def __init__(self, handler) -> None:
        self.handler = handler

    def start(self):
        twm = ThreadedWebsocketManager(api_key=CONFIG.API_KEY, api_secret=CONFIG.API_SECRET)
        twm.start()

        twm.start_trade_socket(callback=self.handler, symbol=CONFIG.TARGET_SYMBOL)