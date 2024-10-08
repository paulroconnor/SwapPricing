import pandas as pd
from datetime import datetime
import ustreasurycurve as ustc

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
    
    def yieldcurve(self):
        tenormapping = {'1m':1/12,'2m':1/6,'3m':0.25,'6m':0.5,'1y':1,'2y':2,'3y':3,'5y':5,'10y':10,'20y':20,'30y':30}
        ts = ustc.nominalRates(date_start = self.valuation, date_end = self.valuation)
        ts = ts.iloc[:,1:].melt(var_name = 'tenor', value_name = 'rate')
        ts['time'] = [tenormapping[tenor] for tenor in ts['tenor']]
        return ts[['tenor','time','rate']]



# check = Swap(notional = 100, fixed = 0.05, floating = 0.05, maturity = '2020-12-11', frequency = 'Semi-Annual', daycount = '30/360', valuation = '2015-03-17')
# print(check.yieldcurve())