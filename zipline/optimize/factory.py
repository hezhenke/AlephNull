"""
Factory functions to prepare useful data for optimize tests.

Author: Thomas V. Wiecki (thomas.wiecki@gmail.com), 2012
"""
from datetime import datetime, timedelta

import zipline.protocol as zp

from zipline.utils.factory import get_next_trading_dt, create_trading_environment
from zipline.finance.sources import SpecificEquityTrades
from zipline.optimize.algorithms import BuySellAlgorithm
from zipline.lines import SimulatedTrading
from zipline.finance.trading import SIMULATION_STYLE

from copy import deepcopy
from itertools import cycle

def create_updown_trade_source(sid, trade_count, trading_environment, start_price, amplitude):
    volume = 1000
    events = []
    price = start_price-amplitude/2.

    cur = trading_environment.first_open
    one_day = timedelta(days = 1)

    #create iterator to cycle through up and down phases
    change = cycle([1,-1])

    for i in xrange(trade_count + 2):
        cur = get_next_trading_dt(cur, one_day, trading_environment)

        event = zp.ndict({
            "type"      : zp.DATASOURCE_TYPE.TRADE,
            "sid"       : sid,
            "price"     : price,
            "volume"    : volume,
            "dt"        : cur,
        })

        events.append(event)

        price += change.next()*amplitude

    trading_environment.period_end = cur

    source = SpecificEquityTrades("updown_" + str(sid), events)

    return source


def create_predictable_zipline(config, sid=133, amplitude=10, base_price=50, offset=0, trade_count=3, simulate=True):
    #config = deepcopy(config)
    trading_environment = create_trading_environment()
    source = create_updown_trade_source(sid,
                                        trade_count,
                                        trading_environment,
                                        base_price,
                                        amplitude)

    if 'algorithm' not in config:
        config['algorithm'] = BuySellAlgorithm(sid, 100, offset)

    config['order_count'] = trade_count - 1
    config['trade_count'] = trade_count
    config['trade_source'] = source
    config['environment'] = trading_environment
    config['simulation_style'] = SIMULATION_STYLE.FIXED_SLIPPAGE

    zipline = SimulatedTrading.create_test_zipline(**config)

    if simulate:
        zipline.simulate(blocking=True)

    return zipline, config