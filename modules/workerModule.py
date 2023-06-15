from binance.enums import SIDE_BUY
from binance.exceptions import BinanceAPIException
import math
import CONFIG
import threading
import misc.utils

from misc.utils import cprint
from time import sleep
from events import Events
from binance.client import Client
from binance.enums import *
from modules.checkerModule import checkerModuleAPI, checkerModuleSocket
from misc.enums import ORDER_TYPES

class workerModule:
    def __init__(self) -> None:
        self.client = Client(CONFIG.API_KEY, CONFIG.API_SECRET)
        self.threadPool, self.checkerList = [], []
        self.onSymbolUpdated, self.onSymbolValid = Events(), Events()
        self.currentTick, self.lastTick = 0, 0
        self.current_balance = CONFIG.BALANCE
        self.killSwitch = False

    def onCheckerTick(self, symbol, elapsed):
        if (type(symbol) is not BinanceAPIException):
            symbolPrice = float(symbol["price"])
            order_price = self.getOrderPrice(symbolPrice)
            order_quantity = math.floor((CONFIG.BALANCE / CONFIG.ORDER_COUNT) / order_price * CONFIG.ORDER_QUANTITY_BOTTLENECK_MULTIPLER)
            order_total = order_price * order_quantity

            if (self.checkForBalance(symbolPrice, order_total, order_price) != True):
                self.killSwitch = True
                return

            try:
                cprint(4,f'buy order will be created at {order_price} amount of {order_quantity}{symbol["symbol"]}. total: {order_total}')

                if (CONFIG.ORDER_TYPE == ORDER_TYPES.ORDER_TYPE_STATIC_LIMIT):
                    self.createLimitOrder(CONFIG.TARGET_SYMBOL, order_quantity, order_price)
                else:
                    self.createStopLimitOrder(CONFIG.TARGET_SYMBOL, order_quantity, order_price)

                self.current_balance -= order_total  
                self.onSymbolValid.on_change(symbol)
                cprint(3,f'order created successfully. estimated balance: {self.current_balance}')
            except Exception as e:
                if (self.handleApiException(e)):            
                    cprint(1,f'failed to create buy order: {e.message}')
                else:
                    cprint(2,f'failed to create buy order: {e.message}')
                    self.killSwitch = True

            if (self.current_balance < 10):
                cprint(3,f'Order(s) have been created.')
                self.killSwitch = True             
        else:
                self.onSymbolUpdated.on_change(symbol)

    def startApiModule(self):
        for x in range(CONFIG.CHECKER_API_REQUEST_THREAD_MAX_COUNT):
            module = checkerModuleAPI(self.client, x)   
            module.onTick.on_change += self.onCheckerTick
            thread = threading.Thread(target= self.runApiModule, args= [module])

            self.threadPool.append(thread)
            self.checkerList.append(module)
            thread.start()

    def startSocketModule(self):
        self.runSocketModule()

    def tickLogic(self):
        diff = misc.utils.getMs() - self.lastTick

        if (diff < CONFIG.CHECKER_API_REQUEST_MIN_TICK):
            tickDiff = (CONFIG.CHECKER_API_REQUEST_MIN_TICK - diff) / 1000
            sleep((CONFIG.CHECKER_API_REQUEST_MIN_TICK - diff) / 1000)
        else:
            tickDiff = 0

        self.currentTick = diff + tickDiff
        self.lastTick = misc.utils.getMs()

    def runApiModule(self, module):
        while(self.killSwitch != True):
            symbol, elapsed = module.update()
            self.tickLogic()

    def runSocketModule(self):
        module = checkerModuleSocket(self.onCheckerTick)
        module.start()

    def checkForBalance(self, symbol_price, order_total, order_price):
        if (symbol_price > order_price or self.current_balance < order_total):
            cprint(2,f'Symbol price is higher than max price defined in configuration: '
             + f'current price ${symbol_price}, max price ${CONFIG.SYMBOL_ORDER_PRICE_MAX}.')
            return False

        if(self.current_balance < 10):
            cprint(2,f'Insufficant balance to create buy order. Minimum balance must be 10$.')
            return False

        if(order_total < 10):
            cprint(2,f'Invalid configuration. Order total must be greater then 10$.')
            return False

        return True

    def getOrderPrice(self, symbol_price):
        if (CONFIG.ORDER_TYPE == ORDER_TYPES.ORDER_TYPE_STATIC_LIMIT):
            return CONFIG.STATIC_LIMIT_ORDER_PRICE
        if (CONFIG.ORDER_TYPE == ORDER_TYPES.ORDER_TYPE_INCREMENTAL_LIMIT):
            symbolPrice = float(symbol_price)
            order_price = round(symbolPrice * CONFIG.INCREMENTAL_ORDER_LIMIT_PRICE_MULTIPLIER, CONFIG.ORDER_PRICE_MAX_DECIMALS)
            return order_price

    def createLimitOrder(self, symbol, order_quantity, order_price):
        if (CONFIG.ENVIRONMENT == "RE"):
            self.client.create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_LIMIT,
            timeInForce='GTC',
            quantity=order_quantity,
            price=order_price)
        else:
            self.client.create_test_order(
            symbol=CONFIG.TARGET_SYMBOL,
            side=SIDE_BUY,
            type=ORDER_TYPE_LIMIT,
            timeInForce='GTC',
            quantity=order_quantity,
            price=order_price)

    def createStopLimitOrder(self, symbol, order_quantity, order_price):
        if (CONFIG.ENVIRONMENT == "RE"):
            self.client.create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_LIMIT,
            timeInForce='GTC',
            quantity=order_quantity,
            price=order_price)
        else:
            self.client.create_test_order(
            symbol=CONFIG.TARGET_SYMBOL,
            side=SIDE_BUY,
            type=ORDER_TYPE_LIMIT,
            timeInForce='GTC',
            quantity=order_quantity,
            price=order_price)

    def handleApiException(self, exception):
        if (type(exception) is not BinanceAPIException):
            cprint(1,f'Exception type must be BinanceAPIException.')
            return True

        if (exception.code == -1021): 
            return True

        if (exception.code == -2010):
            return False

        return True