"""Generates fairly plausible random dummy universe data

Naming conventions:

symbol - a high level symbol (i.e. a "contract constructor" in functional terms) like YG
contract - a low level symbol that represents a specific contract like ZLF17
"""

from pandas.tslib import Timestamp
from pandas.core.frame import DataFrame
import datetime
import random
import pytz
import pandas as pd

ACCEPTABLE_SYMBOLS = {
    "GC": "GHMQVZ",
    "SI": "HKNUZ",
    "HG": "HKNUZ",
    "PL": "FJNV",
    "PA": "HMUZ",
    "CT": "HKNVZ",
    "OJ": "FHKNUX",
    "KC": "HKNUZ",
    "ES": "HMUZ",
    "LE": "GJMQVZ",
    "ZL": "FHKNQUVZ",
}

class PrevIterator(object):
    """Iterator with the capability to fetch the previous element
    (though history does not go back any farther).
    """
    def __init__(self, iterator):
        self.iterator = iterator
        self.current_element = None
        self.last_element = None
    
    def __iter__(self):
        return self
    
    def next(self):
        self.last_element = self.current_element
        self.current_element = next(self.iterator)
        return self.current_element
        
    def last(self):
        return self.last_element
        
def lazy_contracts():
    for symbol, months in ACCEPTABLE_SYMBOLS.iteritems():
        for month in list(months):
            for year in range(datetime.date.today().year, 2020 + 1):
                short_year = year - 2000
                yield (symbol, month, str(short_year))
                
def lazy_timestamps():
    start = Timestamp('2013-05-13 13:30:00+0000', tz='UTC')
    end = Timestamp('2013-09-11 20:30:00+0000', tz='UTC')
    exchange_opens = datetime.time(hour=13, minute=30) # UTC
    exchange_closes = datetime.time(hour=20, minute=0) # UTC
    step = datetime.timedelta(minutes=30)
    
    running_timestamp = start
    while running_timestamp <= end:
        yield running_timestamp
        if exchange_opens <= running_timestamp.time() <= exchange_closes:
            running_timestamp += step
        elif running_timestamp.time() < exchange_opens:
            d = running_timestamp.date()
            z = running_timestamp.tz
            running_timestamp = Timestamp(d, exchange_opens, z)
        elif running_timestamp.time() > exchange_closes:
            d = running_timestamp.date()
            z = running_timestamp.tz
            running_timestamp = datetime.datetime.combine(d + datetime.timedelta(days=1), exchange_opens)
            running_timestamp = running_timestamp.replace(tzinfo=pytz.UTC)
            running_timestamp = Timestamp(running_timestamp)

def create_dummy_universe_dict():
    """
    WARNING: Because the underlying data structure has to be highly nested, the logic in here
    will be highly nested.
    """
    universe_dict = {}
    timestamps = PrevIterator(lazy_timestamps())
    for timestamp in timestamps:
        universe_dict[timestamp] = {}
        for symbol, month, short_year in lazy_contracts():
            if symbol not in universe_dict[timestamp]:
                universe_dict[timestamp][symbol] = {}
            expiry = month + str(short_year)
            universe_dict[timestamp][symbol][expiry] = {}
            
            if timestamps.last() in universe_dict:
                old_price = universe_dict[timestamps.last()][symbol][expiry]["Price"]
                percent_change = 0.2
                change_scale = (random.random()) * percent_change * 2 + (1 - percent_change)
                new_price = old_price * change_scale
                
                old_open_interest = universe_dict[timestamps.last()][symbol][expiry]["Open Interest"]
                percent_change = 0.08
                change_scale = (random.random()) * percent_change * 2 + (1 - percent_change)
                new_open_interest = old_open_interest * change_scale
            else:
                # First price
                new_price = random.random() * 100
                new_open_interest = random.random() * 2000
                
            new_price = round(new_price, 2)
            universe_dict[timestamp][symbol][expiry]["Price"] = new_price
            
            new_open_interest = int(round(new_open_interest, 0))
            universe_dict[timestamp][symbol][expiry]["Open Interest"] = new_open_interest
        
    return universe_dict

def dataframe_from_universe_dict(universe_dict):
    timestamps = []
    outer_frames = []
    for timestamp, hl_ticker_dict in universe_dict.iteritems():
        timestamps.append(timestamp)
        
        inner_frames = []
        hl_tickers = []
        for hl_ticker, low_level_ticker_dict in hl_ticker_dict.iteritems():
            hl_tickers.append(hl_ticker)
            inner_frames.append(DataFrame.from_dict(low_level_ticker_dict, orient='index'))
        hl_ticker_frame = pd.concat(inner_frames, keys=hl_tickers)
        outer_frames.append(hl_ticker_frame)
        
    universe_df = pd.concat(outer_frames, keys=timestamps)
    return universe_df
    
"""
A small set of dummy futures data will have this structure:

{Timestamp('2013-05-13 07:45:49+0000', tz='UTC'): 
    {'YG':
        {'F15': 
            {'Price': 180.00, 
             'Open Index': 1000,
            },
         'N16': 
            {'Price': 250.75, 
             'Open Index': 2000,
            },
        },
     'XSN':
         {'F15': 
            {'Price': 360.00, 
             'Open Index': 4682,
            },
         'N16': 
            {'Price': 405.75, 
             'Open Index': 4001,
            },
        },
    },
 Timestamp('2013-05-13 08:45:49+0000', tz='UTC'): 
    {'YG':
        {'F15': 
            {'Price': 195.66, 
             'Open Index': 996,
            },
         'N16': 
            {'Price': 266.75, 
             'Open Index': 2003,
            },
        },
     'XSN':
        {'F15': 
            {'Price': 358.08, 
             'Open Index': 5000,
            },
         'N16': 
            {'Price': 402.75, 
             'Open Index': 4002,
            },
        },
    },
}
"""