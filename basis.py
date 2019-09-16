# -*- coding: utf-8 -*-
"""
# Author: Li Xiang@CICC.EQ
# Created Time : Mon 16 Sep 2019 01:54:03 PM CST
# File Name: basis.py
# Description:
"""
#%% Import Part
import os,sys
import datetime
import rqdatac as rq
rq.init()
from qpc import *
import warnings
warnings.filterwarnings("ignore")
import pdb

#%% Class of StockIndexFutureBasis
class StockIndexFutureBasis(base_):
    def __init__(self,fini,types=None):
        super().__init__(fini)
        self.width = self.ini.findString('width')
        if types is None: types = ['IC','IF','IH']
        self.types = types
        self.index_name_mapping = {'IC':'CSI500',
                                   'IF':'CSI300',
                                   'IH':'SSE50'}
        self.index_code_mapping = {'IC':'000905',
                                   'IF':'000300',
                                   'IH':'000016'}

    def get_contracts(self):
        ticker_df = rq.all_instruments(type='Future')
        ticker_list = [(tp,self._contracts_(ticker_df,tp)) for tp in self.types]
        self.ticker_dict = {id:(tp,df) for tp,(id,df) in ticker_list}
        return self.ticker_dict

    def _contracts_(self,ticker_df,type):
        df = ticker_df[ticker_df['underlying_symbol']==type].sort_values(by=\
                'de_listed_date').iloc[-4:]
        index_id = df['underlying_order_book_id'].values[0]
        df = df[['de_listed_date','order_book_id']].set_index('order_book_id')
        df['de_listed_date'] = df['de_listed_date'].apply(lambda s:s.replace('-',''))
        return index_id,df

    def get_basis(self):
        # Get all ids
        future_ids = sum([df.index.tolist() for _,(_,df) in self.ticker_dict.items()],[])
        index_ids = [*self.ticker_dict.keys()]
        ids = future_ids+index_ids
        # Get snapshot prices
        data_list = rq.current_snapshot(ids)
        ask1 = [data.asks[0] for data in data_list]
        bid1 = [data.bids[0] for data in data_list]
        last = [data.last for data in data_list]
        price_df = pd.DataFrame({'ask1':ask1,'bid1':bid1,'last':last},index=ids)
        price_df['sp'] = price_df['ask1'] - price_df['bid1']
        price_df['mid'] = (price_df['ask1'] + price_df['bid1'])/2
        # Loop types to cal annualized basis
        basis_df = {}
        for index_id,(type,df) in self.ticker_dict.items():
            df['ndays'] = [count_dates(today(),ddate[0]) for ddate in df.values]
            price_index = price_df.loc[index_id,'last']
            df['f.last'] = price_df.loc[df.index,'last']
            df['i.last'] = price_index
            df['basis'] = df['f.last'].values - price_index
            df['ann.basis'] = df['basis']/price_index*252/df['ndays']
            df['sp'] = price_df.loc[df.index,'sp']
            basis_df[type] = df
            #pdb.set_trace()
        self.basis_df = basis_df

    def print(self):
        print(format('[ '+datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')+' ]',\
                '^'+str(int(self.width)*6)))
        for type,df in self.basis_df.items():
            self._print_(type,df)

    def _print_(self,type,df):
        width = self.width
        print(format('','-^'+str(int(self.width)*6)))
        #                  CSI500      IC1909      IC1910      IC1912      IC2003
        line = '',self.index_name_mapping[type],*df.index
        print((('{:^'+width+'}')*1+('{:>'+width+'}')*5).format(*line))
        #   Spread                       0.20        0.40        5.00        0.80
        line = 'Spread','',*df['sp']
        print((('{:^'+width+'}')*2+('{:>'+width+'.2f}')*4).format(*line))
        #  SettDate                  20190920    20191018    20191220    20200320
        line = 'SettDate','',*df['de_listed_date']
        print((('{:^'+width+'}')*1+('{:>'+width+'}')*5).format(*line))
        #   #Days                           4          19          64         127
        line = '#Days','',*df['ndays']
        print((('{:^'+width+'}')*2+('{:>'+width+'d}')*4).format(*line))
        # LastPrice        5250.3      5237.4      5207.2      5135.0      5052.4
        line = 'LastPrice',df['i.last'][0],*df['f.last']
        print((('{:^'+width+'}')+('{:>'+width+'.1f}')*5).format(*line))
        #   Basis                       -12.9       -43.1      -115.3      -197.9
        line = 'Basis','',*df['basis']
        print((('{:^'+width+'}')*2+('{:>'+width+'.1f}')*4).format(*line))
        #  AnnBasis                   -15.53%     -10.90%      -8.65%      -7.48%
        line = 'AnnBasis','',*df['ann.basis']*100
        print((('{:^'+width+'}')*2+('{:>'+str(int(width)-1)+'.2f}%')*4).format(*line))

#%% Test codes
if __name__=='__main__':
    if len(sys.argv)>1:
        types = sys.argv[1:]
    else:
        types = None
    bs = StockIndexFutureBasis('./stock.index.future.ini',types)
    bs.get_contracts()
    bs.get_basis()
    bs.print()



