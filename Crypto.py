from decimal import Decimal
import time
import ccxt
import numpy as np

class Crypto_Bittrex:
    '''This class implements the Bittrex using ccxt and provides functions
    that ccxt does not.'''  
    last_call_at = 0
    max_number = 1000000000
    def __init__(self, apiKey, secret):
        self.ex = ccxt.bittrex({
                'apiKey':apiKey,
                'secret':secret})
        
    def rate_limiter(self):
        '''Makes sure that the calls are limited to the Bittrex API.
        If the calls come too early, it makes the system wait.'''
        current = time.time()
        if current - Crypto_Bittrex.last_call_at >= 1:
            # here is the difference in seconds between this call and
            # last is >= 1; it is safe to execute
            Crypto_Bittrex.last_call_at = current
        else:
            diff = current - Crypto_Bittrex.last_call_at
            time.sleep(1 - diff)
    
    def get_markets(self):
        '''Returns the current market information for trading pairs. Returns a
        dict and key is the pair. For example 'LTC/BTC'.'''
        self.rate_limiter()
        return self.ex.load_markets()
    
    def get_order_book(self, keys):
        '''Returns the order book for the given pairs. For multiple ones,
        pass them in a list like ['BTC/USD', 'LTC/BTC']. If a list is passed,
        a list will be returned, otherwise a dict with .'''
        if type(keys) == str:
            # here if only one string has been passed
            self.rate_limiter()
            return self.ex.fetch_order_book(keys)
        else:
            # here if passed was a list
            values = [None] * len(keys)
            for i, pair in enumerate(keys):
                self.rate_limiter()
                values[i] = self.ex.fetch_order_book(pair)
            return values
        
    def get_currencies(self):
        '''Returns a dict of currencies with keys as currency names like BTC.
        '''
        self.rate_limiter()
        return self.ex.fetch_currencies()
    
    def get_ticker(self, key):
        '''Returns a dict of containing information like price and high/low
        etc.'''
        self.rate_limiter()
        return self.ex.fetch_ticker(key)
        
    
    def get_tickers(self, keys = None):
        '''Returns information for selected, or all tickers if keys is None.'''
        self.rate_limiter()
        data = self.ex.fetch_tickers()
        if keys is None:
            return data
        else:
            return {symbol: data[symbol] for symbol in keys}
        
    def get_trades(self, keys):
        '''Returns the last 100 trades for the pair if it exists. A list can
        also be passed to get information for multiple pairs.'''
        if type(keys) == str:
            self.rate_limiter()
            return self.ex.fetch_trades(keys)
        else:
            values = [None] * len(keys)
            for i, pair in enumerate(keys):
                self.rate_limiter()
                values[i] = self.ex.fetch_trades(pair)
            return values
    
    def get_balance(self):
        '''Returns the balance of the account in various currencies.'''
        self.rate_limiter()
        return self.ex.fetch_balance()    
    
    def get_active_pairs_with_cur(self, currency, top: bool = True):
        '''Returns a list of all market pairs where the specified currency
        is on top'''
        market_data = self.get_markets()
        active = [market_data[pairName]['active'] for pairName in market_data.keys()]
        keys = np.array(list(market_data.keys()))
        if top == True:
            func = np.frompyfunc(lambda x, y: (x.split('/')[0] == currency) and (y), 2, 1)
        else:
            func = np.frompyfunc(lambda x, y: (x.split('/')[1] == currency) and (y), 2, 1)
        
        return keys[np.where(func(keys, active) == True)]
    
    def _is_an_active_pair(self, pair):
        '''Returns a boolean value and the entire markets.'''
        market_data = self.get_markets()
        keys = np.array(list(market_data.keys()))
        if (pair in keys) and (market_data[pair]['active'] == True):
            return (True, market_data)
        else:
            return (False, market_data)
    
    def set_order(self, pair: str, buy_sell: str, price: float, 
                  quantity: float):
        '''Place a simple buy or sell order at the given limit_price
        with the specified amount. Please note it raises exceptions
        where appropriate. For example, if the pair does not exist, an
        exception will be raised.
        For example: to buy BTC using USDT, pair would be BTC/USDT (which
        exists), buy_sell will be 'buy', price will be price in USDT to
        execute the trade at, quantity will be quantity of BTC to buy.'''
        # pair existence
        pair_existence, markets = self._is_an_active_pair(pair)
        if not(pair_existence):
            raise PairError(pair, 'Pair is not available for trading')
        
        balances = self.get_balance()
        
        
        self._check_limits_precision(markets[pair], balances, buy_sell, price, quantity)
        
        # call above will raise exceptions if appropriate
        # stuff below will execute if there are no issues
        self.rate_limiter()
        if buy_sell == 'buy':
            return self.ex.create_limit_buy_order(pair, quantity, price)
        else:
            return self.ex.create_limit_sell_order(pair, quantity, price)
            
        
    def _check_limits_precision(self, market, balances, buy_sell, price, quantity):
        '''Checks requirements for buy order.'''
        # check if the price is higher than min price
        limits = market['limits']
        amnt_min, amnt_max = limits['amount']['min'], limits['amount']['max']
        price_min, price_max = limits['amount']['min'], limits['amount']['max']
        
        if price_max is None: price_max = np.iinfo(np.int32).max
        if amnt_max is None: amnt_max = np.iinfo(np.int32).max
        
        if (price < price_min) or (price > price_max):
            raise PriceError('Price is not within bounds allowed by exchange.')
        
        if (quantity < amnt_min) or (quantity > amnt_max):
            raise QuantityError('Quantity is not within bounds allowed by exchange.')
        
        
        # check precision
        precision_amnt, precision_price = market['precision']['amount'], market['precision']['price']
        # amount check
        digits_after_decimal = Decimal(str(quantity)).as_tuple().exponent * -1
        if digits_after_decimal > precision_amnt:
            raise PrecisionError('Passed: ' + str(digits_after_decimal), 'Allowed: ' + str(precision_amnt))
        # price check
        digits_after_decimal = Decimal(str(price)).as_tuple().exponent * -1
        if digits_after_decimal > precision_price:
            raise PrecisionError('Passed: ' + str(digits_after_decimal), 'Allowed: ' + str(precision_price))
        
        value = price * quantity
        
        top, bottom = market['symbol'].split('/')
        
        if buy_sell == 'buy':
            # is the currency to sell in wallet?
            if bottom not in balances['free'].keys():
                raise NotInWallet(bottom + 'is not in wallet to sell')
            # is the value enought?
            if balances['free'][bottom] < value:
                raise InsufficientFunds('Insufficient amount of currency ' + bottom,
                                        'Available: ' + balances['free'][bottom],
                                        'Requested: ' + value)
        else:
            # it's a sell
            # is the currency being sold in wallet?
            if top not in balances['free'].keys():
                raise NotInWallet(top + ' is not in wallet to sell')
            # is it enough?
            if balances['free'][top] < quantity:
                raise InsufficientFunds('Insufficient amount of currency ' + top,
                                        'Available: ' + balances['free'][top],
                                        'Requested: ' + quantity)
        
        # HERE IF ALL CHECKS HAVE PASSED
        
    def get_open_orders(self):
        '''Returns all open orders.'''
        self.rate_limiter()
        return self.ex.fetch_open_orders()
                
    def ex(self):
        return self.ex




class Error(Exception):
    '''Base class for exceptions.'''
    pass

class PairError(Error):
    '''Raised when trying to trade a currency pair that does not exist'''
    def __init__(self, pair, message):
        self.pair = pair
        self.message = message

class QuantityError(Error):
    '''Raised when the minimum quantity for the trade is not met.'''
    def __init__(self, message):
        self.message = message
    
class PriceError(Error):
    '''Raised when the minimum price for the trade is not met.'''
    def __init__(self, message):
        self.message = message

class PrecisionError(Error):
    '''Raised when digits specified after demcimal exceed exchange limit.'''
    def __init__(self, passed, allowed):
        self.passed = passed
        self.allowed = allowed
        
class NotInWallet(Error):
    '''Raised when the specific currency to trade is actually not in wallet.'''
    def __init__(self, message):
        self.message = message
        
class InsufficientFunds(Error):
    '''Raised when the specific currency being sold (or being sold to buy something)
    is insifficient.'''
    def __init__(self, message, available, tried):
        self.message = message
        self.available = available
        self.tried = tried
