"""
    TODO: Add smart unparalleled threading logic to reduce effect of network latency. 
"""

import CONFIG
import asyncio

from misc.utils import cprint
from binance.exceptions import BinanceAPIException
from modules.checkerModule import checkerModuleSocket
from modules.workerModule import workerModule

def onSymbolValidHandler(symbol):
    pass

def onSymbolUpdatedHandler(symbol):
    if (type(symbol) is BinanceAPIException):
        if (symbol.status_code == 400):
            cprint(1,f'Symbol is not valid or it is not launched yet. ({symbol.message}, {worker.currentTick}ms)')
    else:
        print(f'{symbol} {worker.currentTick}ms')

def ValidateConfig():
    if (CONFIG.BALANCE < 10):
        cprint(2,f'Insufficant balance. Minimum balance must be 10$.')
    else:
        return True

if (__name__ == "__main__"):

    if (ValidateConfig()):
        try:
            worker = workerModule()
            worker.onSymbolUpdated.on_change += onSymbolUpdatedHandler
            worker.onSymbolValid.on_change += onSymbolValidHandler
            worker.startApiModule()
        except :
            pass
        input()