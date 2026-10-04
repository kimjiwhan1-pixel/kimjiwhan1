import unittest
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from indicators import normalize_symbol, metrics, wilder_rsi, breadth
from unittest.mock import patch
from data import completed_rows, market_closes

class IndicatorTests(unittest.TestCase):
    def series(self, values):
        return pd.Series(values, index=pd.bdate_range('2025-01-01', periods=len(values)))

    def test_wilder_reference(self):
        values = [44.34,44.09,44.15,43.61,44.33,44.83,45.10,45.42,45.84,46.08,45.89,46.03,45.61,46.28,46.28,46.00]
        r = wilder_rsi(self.series(values))
        self.assertTrue(r.iloc[:14].isna().all())
        self.assertAlmostEqual(r.iloc[14], 70.464135, places=5)
        self.assertAlmostEqual(r.iloc[15], 66.249619, places=5)

    def test_monotonic_and_flat(self):
        for values, expected in ((range(1,31),100),(range(30,0,-1),0),([50]*30,50)):
            self.assertEqual(wilder_rsi(self.series(values)).iloc[-1], expected)

    def test_sma_and_distance(self):
        m = metrics(self.series(range(1,202)))
        self.assertEqual(m['sma200'],101.5)
        self.assertAlmostEqual(m['distance'],(201/101.5-1)*100)
        self.assertEqual(m['drawdown'],0)

    def test_short_history(self):
        m = metrics(self.series(range(1,31)))
        self.assertIsNone(m['sma200'])
        self.assertIsNone(m['distance'])
        self.assertEqual(m['rsi14'],100)

    def test_invalid_ticker(self):
        self.assertEqual(normalize_symbol(' brk.b '),'BRK-B')
        for bad in ('','<script>','AAPL SPY','../../file'):
            with self.assertRaises(ValueError): normalize_symbol(bad)

    def test_breadth_denominator_and_no_stale_fill(self):
        idx = pd.bdate_range('2025-01-01',periods=205)
        closes = pd.DataFrame({'UP':np.arange(1,206),'DOWN':np.arange(205,0,-1),'MISSING':np.arange(1,206,dtype=float)},index=idx)
        closes.loc[idx[-1],'MISSING']=np.nan
        b = breadth(closes,['UP','DOWN','MISSING','ABSENT'],idx[-1])
        self.assertEqual(b['value'],50)
        self.assertEqual(b['valid'],2)
        self.assertEqual(b['coverage'],50)
        self.assertEqual(b['missing'],['MISSING','ABSENT'])
        self.assertEqual(b['delta'],0)
        self.assertEqual(b['common_n'],2)

    def test_breadth_strict_above(self):
        idx = pd.bdate_range('2025-01-01',periods=201)
        b = breadth(pd.DataFrame({'FLAT':100},index=idx),['FLAT'],idx[-1])
        self.assertEqual(b['above'],0)

    def test_no_old_breadth_as_latest(self):
        idx = pd.bdate_range('2025-01-01',periods=201)
        with self.assertRaises(ValueError):
            breadth(pd.DataFrame({'A':100},index=idx),['A'],idx[-1]+pd.Timedelta(days=5))

    def test_incomplete_daily_row(self):
        index = pd.date_range('2026-07-01',periods=2,tz='America/New_York')
        frame = pd.DataFrame({'Close':[100,101]},index=index)
        before = datetime(2026,7,2,19,0,tzinfo=timezone.utc)
        after = datetime(2026,7,2,20,16,tzinfo=timezone.utc)
        self.assertEqual(len(completed_rows(frame,now=before)),1)
        self.assertEqual(len(completed_rows(frame,now=after)),2)

    def test_early_close_metadata(self):
        frame = pd.DataFrame({'Close':[100]},index=pd.DatetimeIndex(['2026-11-27'],tz='America/New_York'))
        early = datetime(2026,11,27,18,0,tzinfo=timezone.utc).timestamp()
        meta={'currentTradingPeriod':{'regular':{'end':early}}}
        self.assertEqual(len(completed_rows(frame,meta,datetime(2026,11,27,18,16,tzinfo=timezone.utc))),1)

    def test_timestamp_trading_period_metadata(self):
        frame = pd.DataFrame({'Close':[100]},index=pd.DatetimeIndex(['2026-11-27'],tz='America/New_York'))
        for end in (pd.Timestamp('2026-11-27 13:00',tz='America/New_York'),
                    pd.Timestamp('2026-11-27 13:00')):
            meta = {'currentTradingPeriod':{'regular':{'end':end}}}
            with self.subTest(end=end):
                self.assertEqual(len(completed_rows(frame,meta,datetime(2026,11,27,18,14,tzinfo=timezone.utc))),0)
                self.assertEqual(len(completed_rows(frame,meta,datetime(2026,11,27,18,16,tzinfo=timezone.utc))),1)

    def test_provider_failure_stops_full_market_download(self):
        market_closes.clear()
        with patch('data.yf.Ticker', side_effect=RuntimeError('429')) as ticker:
            with self.assertRaises(ValueError):
                market_closes(tuple(f'SYM{i}' for i in range(500)), '2026-10-02')
            self.assertEqual(ticker.call_count,4)
