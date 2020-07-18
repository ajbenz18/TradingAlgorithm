import alpaca_trade_api as tradeapi
import datetime as dt
import pandas as pd


base_url_paper = "https://paper-api.alpaca.markets"
api_key_id_paper ='PKL6C20IVZZ8QTU3FPJV'
api_secret_paper ='OVUsMMixRuPeMDQI4unV02x6eFKrkCYRCXdPBsdA'
api_paper=tradeapi.REST(api_key_id_paper, api_secret_paper, base_url_paper, 'v2')

#this gets all the stocks in your first watchlist in alpaca
TICKERS=[i['symbol'] for i in api_paper.get_watchlist(api_paper.get_watchlists()[0].id).assets]

ACCOUNT = api_paper.get_account()
VALUE=float(ACCOUNT.equity)
TPP=1.15 #take profit percentage
SLP=.94 #stop loss percentage

class Stock():
    def __init__(self, ticker):
        self.ticker=ticker
        self.data=self.getData() #retrieves candlestick data
        self.sma9=self.data['c'][0:9].mean()
        self.oldsma9=self.data['c'][1:10].mean()
        self.sma120=self.getsma120()
        self.sma180=self.getsma180()
        self.uptrending=self.isUptrending()
        self.price=api_paper.get_last_trade(self.ticker).price #gets approximate current price

    def __repr__(self):
        print("\n"+self.ticker)
        print(self.data)
        print("SMA9:", self.sma9)
        print("old SMA9:", self.oldsma9)
        print("uptrending: ", self.uptrending)
        print("price:", self.price)
        return "\n"

    def __str__(self):
        print("\n"+self.ticker)
        print(self.data)
        print("SMA9:", self.sma9)
        print("old SMA9:", self.oldsma9)
        print("uptrending: ", self.uptrending)
        print("price:", self.price)
        return "\n"

    def getsma180(self):
        """180 hour SMA line (which I wanted to use) is essentially the same as the the 26 day SMA. Data for 
        26 day SMA line is much easier to get, so I'm actually calculating the 26 day SMA line here instead"""
        barData=api.get_barset(self.ticker, "day", after=now-dt.timedelta(hours=27*24))[self.ticker]
        closeData=[barData[x].c for x in range(-1, -27, -1)]
        sma180=sum(closeData)/len(closeData)
        return sma180

    def getsma120(self):
        """120 hour SMA line (which I wanted to use) is essentially the same as the the 17 day SMA. Data for 
        17 day SMA line is much easier to get, so I'm actually calculating the 17 day SMA line here instead"""
        now=dt.datetime.now()
        barData=api.get_barset(self.ticker, "day", after=now-dt.timedelta(hours=18*24))[self.ticker]
        closeData=[barData[x].c for x in range(-1, -18, -1)]
        sma120=sum(closeData)/len(closeData)
        return sma120

    def isUptrending(self):
        if self.sma120>self.sma180:
            uptrending=True
        else:
            uptrending=False
        return uptrending

    def getData(self):
        """uses alpaca API to get 15 minute candlestick data and convert it to hourly since alpaca doesn't offer
        hourly data"""
        now=dt.datetime.now()
        m15=api.get_barset(self.ticker, "15Min", after=now-dt.timedelta(hours=12))[self.ticker]
        numBars=len(m15)
        c=[m15[x].c for x in range(numBars-1, 0, -1)] #close prices of the candles in list form
        o=[m15[x].o for x in range(numBars-1, 0, -1)] #open prices of the candles in list form
        v=[m15[x].v for x in range(numBars-1, 0, -1)] #volume of the candles in list form
        t=[m15[x].t for x in range(numBars-1, 0, -1)] #time of the candles in list forms
        rawData=pd.DataFrame({"c":c, "o":o, "v":v, "t":t})

        #gets rid of any premarket or after hours data with low volume
        threshold=rawData['v'].median()/10
        rawData=rawData[rawData['v']>threshold].reset_index(drop=True) 

        cl=[] #close
        op=[] #open
        vo=[] #volume
        ti=[] #time
        for i in range(0, len(rawData['c'])-4, 4):
            #converts to hourly data from 15 minute data
            cl.append(rawData['c'][i])
            op.append(rawData['o'][i+3])
            ti.append(rawData['t'][i])
            vo.append(sum(rawData['v'][i:i+4]))
        hourlyData=pd.DataFrame({"c":cl, "o":op, "v":vo, "t":ti})
        return hourlyData

    def getStatus(self):
        """tells us whether the stock should be bought, sold, or held
        We buy if the stock is long term uptrending and there is exactly 1 hourly candlestick over the 9 hour
        sma line. We hold if either the open or the close of the current candlestick is abovet the 9 hour
        sma line. We sell if there is a whole candle below the sma line """
        status=None
        if self.data['c'][0]>self.sma9 and self.data['o'][0]>self.sma9 and\
            (self.data['o'][1]<self.oldsma9 or self.data['c'][0]<self.oldsma9) and self.uptrending==True:
            status="buy"
        elif self.data['o'][0]>self.sma9 or self.data['c'][0]>self.sma9:
            status="hold"
        else:
            status="sell"
        return status

def buyQuantity(stock, cash):
    """determines the number of shares to buy based on account size and available cash.
    We want the value of each stock we buy to be one fifth of the value of our portfolio. 
    If we don't have enough cash available for that, we buy however much we can afford"""
    price=stock.price
    if (1.02* price)>cash:
        return None
    optimal=VALUE/5
    if cash<optimal:
        amt=(cash//(1.02*price))
        if amt>0:
            return amt
        else:
            return None
    return (optimal//(1.02*price))

def buy():
    """creates the stock objects and determines which ones to buy"""
    cash=float(api_paper.get_account().cash)
    owned=[i.symbol for i in api_paper.list_positions()]
    for symbol in TICKERS:
        stock=Stock(symbol)
        if stock.getStatus()!="buy" or stock.ticker in owned:
            #we only buy stocks with a buy signal that we don't already own
            continue
        quantity=buyQuantity(stock, cash)
        cash=float(api_paper.get_account().cash)
        print("buying", quantity, stock.ticker)
        try:
            #alpaca api needs all parameters as strings
            api_paper.submit_order(
                symbol=symbol,
                side='buy',
                type='market',
                qty=str(quantity),
                time_in_force='day',
                take_profit=dict(
                    limit_price=str(stock.price*TPP),
                ),
                stop_loss=dict(
                    stop_price=str(SLP*stock.price),
                    limit_price=str((SLP-.01)*stock.price),
                )
            )
        except:
            print("error")
            print("tried to buy", stock.ticker)

def sell():
    """looks at our current positions and determines if anything needs to be sold"""
    positions=api_paper.list_positions()
    print(positions)
    for position in positions:
        stock=Stock(position.symbol)
        if stock.getStatus()!="sell":
            print("holding", stock.ticker)
            continue
        quantity=position.qty
        print("selling", stock.ticker)
        try:
            api_paper.submit_order(
            symbol=stock.ticker,
            side='sell',
            type='market',
            qty=str(quantity),
            time_in_force='day',
            )
        except: #pattern day trade violation
            print("wanted to sell", stock.ticker, "but something went wrong")

def execute(event=None, context=None):
    """the function to call to execute the algorithm. Event and context are paremters because AWS Lambda
    requires them to be there"""
    print(ACCOUNT)
    if api_paper.get_clock().is_open:
        sell()
        buy()
        print("done")
        return "done"
    else:
        print("market is closed")
        return "market is closed"
