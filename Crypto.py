import ccxt
import numpy as np
class Crypto_Bittrex:
    '''This class implements the Bittrex using ccxt and provides functions
    that ccxt does not.'''
    def __init__(self, apiKey, secret):
        self.ex = ccxt.bittrex({
                'apiKey':apiKey,
                'secret':secret})
        self.ex.enableRateLimit = True
        
    def get_markets(self):
        '''Returns the current market information for trading pairs. Returns a
        dict and key is the pair. For example 'LTC/BTC'.'''
        return self.ex.load_markets()
    
    def get_order_book(self, keys):
        '''Returns the order book for the given pairs. For multiple ones,
        pass them in a list like ['BTC/USD', 'LTC/BTC']. If a list is passed,
        a list will be returned, otherwise a dict with .'''
        if type(keys) == str:
            # here if only one string has been passed
            return self.ex.fetch_order_book(keys)
        else:
            # here if passed was a list
            values = [None] * len(keys)
            for i, pair in enumerate(keys):
                values[i] = self.ex.fetch_order_book(pair)
            return values
        
    def get_currencies(self):
        '''Returns a dict of currencies with keys as currency names like BTC.
        '''
        return self.ex.fetch_currencies()
    
    def get_ticker(self, key):
        '''Returns a dict of containing information like price and high/low
        etc.'''
        return self.ex.fetch_ticker(key)
        
    
    def get_tickers(self, keys = None):
        '''Returns information for selected, or all tickers if keys is None.'''
        data = self.ex.fetch_tickers()
        if keys is None:
            return data
        else:
            return {symbol: data[symbol] for symbol in keys}
        
    def get_trades(self, keys):
        '''Returns the last 100 trades for the pair if it exists. A list can
        also be passed to get information for multiple pairs.'''
        if type(keys) == str:
            return self.ex.fetch_trades(keys)
        else:
            values = [None] * len(keys)
            for i, pair in enumerate(keys):
                values[i] = self.ex.fetch_trades(pair)
            return values
    
    def get_balance(self):
        '''Returns the balance of the account in various currencies.'''
        return self.ex.fetch_balance()
    
    def set_order(self, pair: str, buy_sell: str, limit_price: float, 
                  amount: float):
        '''Place a simple buy or sell order at the given limit_price
        with the specified amount.'''
        # first make sure the pair exists
        markets = self.get_markets() # provides the most information
        
    
    def get_active_pairs_with_cur_on_top(self, currency, top: bool = True):
        '''Returns a list of all market pairs where the specified currency
        is on top'''
        markets = self.get_markets()
        all_pairs = markets.keys()
        
        if top == True:
            pass
        
        
        
    
    def ex(self):
        return self.ex

