import numpy as np
import pandas as pd
import yfinance as yf

def get_historical_data(ticker, start, end):
    """
    ticker: e.g., 2454.TW
    start, end: e.g., 2017-05-25, 2022-05-26
    """
    
    d = yf.Ticker(ticker)
    df = d.history(start=start, end=end)
    df.columns = df.columns.str.lower()
    df.columns = pd.Series(df.columns).str.capitalize().values
    
    return df.dropna()

def get_holding_data(ticker, start, end):
    """
    from http://kgieworld.moneydj.com/ZXQW/zc/zcl/zcl.djhtm?a=2454&c=2017-5-25&d=2022-5-25
    
    ticker: e.g., 2454
    start, end: e.g., 2017-5-25, 2022-5-25
    
    NOTE: last row before reverse is 合計買賣超, 
          which can be ignore if we concat dataframes later
    """
    
    pd_li = pd.read_html('http://kgieworld.moneydj.com/ZXQW/zc/zcl/zcl.djhtm?a='+ticker+'&c='+start+'&d='+end)
    
    pd_df = pd.DataFrame(pd_li[1])
    pd_df = pd_df.drop([0, 1, 2, 3, 4, 5])
    pd_df = pd_df.drop([5, 6, 7, 8, 9, 10], axis=1)
    # ['日期', '外資', '投信', '自營商', '單日合計']
    pd_df.columns = ['Date', 'Foreign', 'Trust', 'Dealer', 'Total']
    # reverse
    pd_df = pd_df.iloc[::-1]
    
    return pd_df

def concat_df(df1, df2):
    """
    df1: _df (from yfinance); df2: hd_df (my holding df)
    """
    
    concat_li = ['Foreign', 'Trust', 'Dealer', 'Total']
    df1[concat_li] = np.nan
    i = 0

    for index, row in df2.iterrows():
        if row.Date.split('/') == df1.index[i].strftime('%Y-%m-%d').split('-'):
            df1.loc[df1.index[i], concat_li] = list(row[concat_li])
            i += 1
    return df1

def get_data(ticker, start, end):
    _df = get_historical_data(ticker, start, end)

    # preprocess
    ticker = ticker.split('.')[0]
    d = int(end.split('-')[2])
    end = end.replace(str(d), str(d-1))

    hd_df = get_holding_data(ticker, start, end)
    new_df = concat_df(_df, hd_df)

    return new_df

def chip_signal(_df):
    # print(_df.Foreign)
    count_pos, count_neg = 0, 0
    signal = []
    
    for index, row in _df.iterrows():
        if count_pos == 5:
            # signal rise
            signal.append(1)
            count_pos = 0
        elif count_neg == 5:
            # signal fall
            signal.append(-1)
            count_neg = 0
        else:
            # no signal
            signal.append(0)
        
        # print(index, row.Foreign)
        if int(row.Foreign) >= 0:
            count_pos += 1
            count_neg = 0
        elif int(row.Foreign) < 0:
            count_neg += 1
            count_pos = 0
            
    # print(len(signal))
    _df['ChipSignal'] = signal
    
    return _df