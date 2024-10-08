import pandas as pd
from datetime import datetime
import ustreasurycurve as ustc


def isleapyear(year):
    if (year % 4 == 0):
        return True
    elif (year % 100 == 0) and (year % 400 == 0):
        return True
    else:
        return False


def yeartime(end, start, convention):

    d1, m1, y1 = [start.day, start.month, start.year]
    d2, m2, y2 = [end.day, end.month, end.year]

    if convention == '30/360':
        return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 360

    elif convention == '30U/360':
        if ((m1 == 2) and (d1 in [28, 29])) and ((m2 == 2) and (d2 in [28, 29])):
            d2 = 30
        if (m1 == 2) and (d1 in [28, 29]):
            d1 = 30
        if (d2 == 31) and (d1 in [30, 31]):
            d2 = 30
        if (d1 == 31):
            d1 = 30
        return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 360

    elif convention == '30B/360':
        d1 = min(d1, 30)
        if d1 > 29:
            d2 = min(d2, 30)
        if (d2 == 31) and (d1 in [30, 31]):
            d2 = 30
        if (d1 == 31):
            d1 = 30
        return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 360

    elif convention == '30E/360':
        if (d1 == 31):
            d1 = 30
        if (d2 == 31):
            d2 = 30
        return (360 * (y2 - y1) + 30 * (m2 - m1) + (d2 - d1)) / 360
    
    elif convention == 'Actual/Actual':

        if isleapyear(y1):
            dec1 = (start - datetime(y1,12,31)).days / 366
        else:
            dec1 = (start - datetime(y1,12,31)).days / 365

        if isleapyear(y2):
            dec2 = (end - datetime(y2,1,1)).days / 366
        else:
            dec2 = (end - datetime(y2,1,1)).days / 365
        
        return dec1 + dec2 + len([year for year in range(y1 + 1, y2)])

    elif convention == 'Actual/365':
        return (end - start).days / 365

    elif convention == 'Actual/360':
        return (end - start).days / 360

    elif convention == 'Actual/364':
        return (end - start).days / 364
    



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