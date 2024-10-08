import pandas as pd
from datetime import datetime

class Swap:

    def __init__(self, notional, fixed, floating, maturity, frequency, daycount, valuation):
        self.notional = notional
        self.fixed = fixed
        self.floating = floating
        self.maturity = datetime.strptime(maturity, '%Y-%m-%d')
        self.frequency = frequency
        self.daycount = daycount
        self.valuation = datetime.strptime(valuation, '%Y-%m-%d')
    
    def dates(self):    
        frequencymapping = {'Monthly':'M','Quarterly':'3M','Semi-Annual':'6M','Annual':'12M'}
        setdate = lambda x: datetime.strptime(x.strftime('%Y-%m') + '-' + str(self.maturity.day), '%Y-%m-%d')
        period = pd.period_range(end = self.maturity, periods = 1000, freq = frequencymapping[self.frequency])
        return [setdate(date) for date in period if setdate(date) > self.valuation]
    

# check = Swap(notional = 100, fixed = 0.05, floating = 0.05, maturity = '2020-12-11', frequency = 'Semi-Annual', daycount = '30/360', valuation = '2015-03-17')