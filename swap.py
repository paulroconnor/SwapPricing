# Swap.py


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import ustreasurycurve as ustc
from scipy.optimize import curve_fit
import warnings


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
    
def nelsonsiegelsvensson(t, beta0, beta1, beta2, beta3, lambda0, lambda1):
    # beta0: Long-Term Level of Yields
    # beta1: Short-Term Component
    # beta2: Medium-Term Hump or Curvature
    # beta3: Extra Flexibility for Long-Term Component
    # lambda0: Decay Factor for beta1 and beta2
    # lambda1: Decay Factor for beta3

    t = np.asarray(t, dtype = float)

    term1 = (1 - np.exp(-t / lambda0)) / (t / lambda0)
    term2 = term1 - np.exp(-t / lambda0)
    term3 = (1 - np.exp(-t / lambda1)) / (t / lambda1) - np.exp(-t / lambda1)
    return beta0 + beta1 * term1 + beta2 * term2 + beta3 * term3

def discountfactor(spot, time, compounding):
    # Convert to numpuy array to handle arrays or single entries
    spot = np.asarray(spot, dtype = float)
    time = np.asarray(time, dtype = float)

    if compounding == 'Continuous':
        return np.exp(-spot * time)
    else:
        compoundmapping = {'Monthly':1,'Quarterly':4,'Semi-Annual':2,'Annual':1}
        m = compoundmapping[compounding]
        return (1 + spot / m) ** (-time * m)




class InterestRateSwap:

    def __init__(self, notional, fixed, floating, maturity, frequency, daycount, valuation, compounding):
        self.notional = notional
        self.fixed = fixed
        self.floating = floating
        self.maturity = datetime.strptime(maturity, '%Y-%m-%d')
        self.frequency = frequency
        self.daycount = daycount
        self.valuation = datetime.strptime(valuation, '%Y-%m-%d')
        self.compounding = compounding
        self.yieldcurveparams = self.nssparameters()
    
    def __repr__(self):
        return (f'InterestRateSwap(notional={self.notional}, fixed={self.fixed}, floating={self.floating}, '
                f'maturity={self.maturity.strftime('%Y-%m-%d')}, frequency={self.frequency}, '
                f'daycount={self.daycount}, valuation={self.valuation.strftime('%Y-%m-%d')}, '
                f'compounding={self.compounding})')
    
    def __str__(self):
        return (f'Interest Rate Swap with notional: {self.notional}, fixed rate: {self.fixed}, floating rate: {self.floating}, '
                f'maturity date: {self.maturity.strftime('%Y-%m-%d')}, frequency: {self.frequency}, '
                f'day count convention: {self.daycount}, valuation date: {self.valuation.strftime('%Y-%m-%d')}, '
                f'compounding method: {self.compounding}')
    
    def dates(self):    
        frequencymapping = {'Monthly':'M','Quarterly':'3M','Semi-Annual':'6M','Annual':'12M'}
        setdate = lambda x: datetime.strptime(x.strftime('%Y-%m') + '-' + str(self.maturity.day), '%Y-%m-%d')
        period = pd.period_range(end = self.maturity, periods = 1000, freq = frequencymapping[self.frequency])
        return [setdate(date) for date in period if setdate(date) > self.valuation]
    
    def businessdates(self):
        period = pd.Series(self.dates())
        return period.apply(lambda date: date if date in pd.bdate_range(date,date) else date + pd.tseries.offsets.BDay(1))

    def decimaldates(self):
        return [yeartime(date, self.valuation, convention = self.daycount) for date in self.businessdates()]
    
    def termstructure(self):
        tenormapping = {'1m':1/12,'2m':1/6,'3m':0.25,'6m':0.5,'1y':1,'2y':2,'3y':3,'5y':5,'10y':10,'20y':20,'30y':30}
        warnings.simplefilter('ignore', category = UserWarning)
        ts = ustc.nominalRates(date_start = self.valuation, date_end = self.valuation)
        warnings.simplefilter('default', category = UserWarning)
        ts = ts.iloc[:,1:].melt(var_name = 'tenor', value_name = 'rate')
        ts['time'] = [tenormapping[tenor] for tenor in ts['tenor']]
        return ts[['tenor','time','rate']].dropna()

    def nssparameters(self, initial = [0.03, -0.02, 0.01, 0.05, 2.0, 5.0]):
        ts = self.termstructure()
        return curve_fit(nelsonsiegelsvensson, ts['time'], ts['rate'], p0 = initial)[0]

    def discountfactors(self):
        params = self.yieldcurveparams
        times = np.asarray(self.decimaldates(), dtype = float)
        spots = np.asarray(nelsonsiegelsvensson(times, *params), dtype = float)

        if self.compounding == 'Continuous':
            return np.exp(-spots * times)
        else:
            compoundmapping = {'Monthly':1,'Quarterly':4,'Semi-Annual':2,'Annual':1}
            m = compoundmapping[self.compounding]
            return (1 + spots / m) ** (-times * m)

    def forwardrates(self):
        params = self.yieldcurveparams
        times = self.decimaldates()
        spots = nelsonsiegelsvensson(times, *params)
        forwards = []

        for i in range(len(times)):
            ti = times[i]
            si = spots[i]
            tj = ti + 1
            sj = nelsonsiegelsvensson(tj, *params)  # One-year lending rate

            if self.compounding == 'Continuous':
                forwards.append((sj * tj - si * ti) / (tj - ti))
            else:
                compoundmapping = {'Monthly':1,'Quarterly':4,'Semi-Annual':2,'Annual':1}
                m = compoundmapping[self.compounding]
                forwards.append((m * (((1 + sj / m) ** tj) / ((1 + si / m) ** ti)) ** (1 / (tj - ti))) - m)

        return forwards

    def fixedleg(self):
        df = pd.DataFrame({
            'Date':self.businessdates(),
            'Time':self.decimaldates(),
            'Fixed Rate':[self.fixed] * len(self.dates()),
            'Payment':[self.fixed * self.notional] * len(self.dates()),
            'Discount':self.discountfactors()
        })
        df.loc[df.index[-1], 'Fixed Rate'] = 1 + self.fixed
        df.loc[df.index[-1], 'Payment'] = (1 + self.fixed) * self.notional
        df['Present Value'] = df['Payment'] * df['Discount']
        return df

    def floatleg(self):
        df = pd.DataFrame({
            'Date':self.businessdates(),
            'Time':self.decimaldates(),
            'Floating Rate':[rate + self.floating for rate in self.forwardrates()],
            'Payment':[(rate + self.floating) * self.notional for rate in self.forwardrates()],
            'Discount':self.discountfactors()
        })
        df.loc[df.index[-1], 'Floating Rate'] = 1 + df.loc[df.index[-1], 'Floating Rate'] 
        df.loc[df.index[-1], 'Payment'] = df.loc[df.index[-1], 'Floating Rate'] * self.notional
        df['Present Value'] = df['Payment'] * df['Discount']
        return df

    def npv(self):
        return self.fixedleg().loc[:,'Present Value'].sum() - self.floatleg().loc[:,'Present Value'].sum()

    def plotcashflows(self):
        fixed = self.fixedleg()
        floating = self.floatleg()

        df = pd.merge(fixed, floating, on = 'Date', suffixes = ('_fixed', '_floating'))
        df['Net Cash Flow'] = df['Present Value_fixed'] - df['Present Value_floating']

        custom = {'axes.edgecolor': '#505258', 'grid.linestyle': 'dashed',
               'grid.color': 'white', 'axes.facecolor': '#E8E9EB'}
        sns.set_style('whitegrid', rc = custom)
        plt.figure(figsize = (16, 8))
        plt.bar(df['Date'], df['Present Value_fixed'], label = 'Fixed Leg', color = '#4062BB', width = 300, align = 'center')
        plt.bar(df['Date'], -df['Present Value_floating'], label = 'Floating Leg', color = '#04E762', width = 300, align = 'center')
        plt.plot(df['Date'], df['Net Cash Flow'].cumsum(), color = 'red', marker = 'o', label = 'Net Cash Flow')
        plt.xlabel('Date')
        plt.ylabel('Present Value')
        plt.title('Fixed vs Floating Leg Cash Flows with Net Present Value of Cash Flows')
        plt.legend(loc = 'lower center', ncol = 3, bbox_to_anchor = (0.5,-0.15), frameon = False)
        plt.show()

    def plotyieldcurve(self):
        params = self.yieldcurveparams
        t = np.linspace(0.1, 30, 100)
        line = nelsonsiegelsvensson(t, *params)
        # ts = self.termstructure()

        custom = {'axes.edgecolor': '#505258', 'grid.linestyle': 'dashed',
               'grid.color': 'white', 'axes.facecolor': '#E8E9EB'}
        sns.set_style('whitegrid', rc = custom)
        plt.figure(figsize = (16,8))
        # sns.scatterplot(x = ts['time'], y = ts['rate'], marker = 'o', linestyle = '', s = 75, color = '#4062BB')
        sns.lineplot(x = t, y = line, linestyle = '-', linewidth = 2, color = '#4062BB')
        plt.title(f'Yield Curve on Valuation Date ({self.valuation.date()})')
        plt.xlabel('Maturity')
        plt.ylabel('Rate')
        plt.grid(True, axis = 'y')
        plt.show()

    def plotdiscountcurve(self):
        params = self.yieldcurveparams
        t = np.linspace(0.1, 30, 100)
        spots = np.asarray(nelsonsiegelsvensson(t, *params), dtype = float)

        if self.compounding == 'Continuous':
            disc = np.exp(-spots * t)
        else:
            compoundmapping = {'Monthly':1,'Quarterly':4,'Semi-Annual':2,'Annual':1}
            m = compoundmapping[self.compounding]
            disc = (1 + spots / m) ** (-t * m)
        
        custom = {'axes.edgecolor': '#505258', 'grid.linestyle': 'dashed',
               'grid.color': 'white', 'axes.facecolor': '#E8E9EB'}
        sns.set_style('whitegrid', rc = custom)
        plt.figure(figsize = (16,8))
        sns.lineplot(x = t, y = disc, linestyle = '-', linewidth = 2, color = '#04E762')
        plt.title(f'Discount Rate Curve on Valuation Date ({self.valuation.date()})')
        plt.xlabel('Maturity')
        plt.ylabel('Discount Rate')
        plt.show()

    def plotforwardcurve(self):
        params = self.yieldcurveparams
        t = np.linspace(0.1, 30, 100)
        spots = nelsonsiegelsvensson(t, *params)
        forwards = []

        for i in range(len(t)):
            ti = t[i]
            si = spots[i]
            tj = ti + 1
            sj = nelsonsiegelsvensson(tj, *params)  # One-year lending rate

            if self.compounding == 'Continuous':
                forwards.append((sj * tj - si * ti) / (tj - ti))
            else:
                compoundmapping = {'Monthly':1,'Quarterly':4,'Semi-Annual':2,'Annual':1}
                m = compoundmapping[self.compounding]
                forwards.append((m * (((1 + sj / m) ** tj) / ((1 + si / m) ** ti)) ** (1 / (tj - ti))) - m)
        
        custom = {'axes.edgecolor': '#505258', 'grid.linestyle': 'dashed',
               'grid.color': 'white', 'axes.facecolor': '#E8E9EB'}
        sns.set_style('whitegrid', rc = custom)
        plt.figure(figsize = (16,8))
        sns.lineplot(x = t, y = forwards, linestyle = '-', linewidth = 2, color =  '#F5B700')
        plt.title(f'Forward Rate Curve on Valuation Date ({self.valuation.date()})')
        plt.xlabel('Maturity')
        plt.ylabel('Forward Rate')
        plt.show()

        
# IRS = InterestRateSwap(notional = 10000, fixed = 0.05, floating = 0.03, 
#                  maturity = '2020-08-22', frequency = 'Semi-Annual', daycount = 'Actual/360', valuation = '2008-06-13', 
#                  compounding = 'Continuous'
#                 )

# IRS.plotcashflows()
# Plots and graphs  - stacked bar: +fixed -float 
# business day