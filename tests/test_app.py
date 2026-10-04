"""합성 데이터로 UI 경로 검증. 실제 시세로 사용하지 않는다."""
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

class AppTests(unittest.TestCase):
    def test_search_metrics_and_breadth(self):
        idx=pd.bdate_range('2025-01-01',periods=320)
        close=pd.Series(np.linspace(100,200,320),index=idx)
        prices=pd.DataFrame({'A':close,'B':300-close},index=idx)
        with patch('data.stock',return_value=dict(close=close,name='UI TEST',fetched=datetime.now(timezone.utc))), patch('data.constituents',return_value=(('A','B'),'https://example.com')), patch('data.market_closes',return_value=prices):
            at=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'),default_timeout=20).run()
            self.assertEqual(len(at.exception),0)
            self.assertEqual(len(at.metric),11)
            self.assertEqual(at.metric[8].value,'50.0%')
            at.text_input[0].set_value('QQQ')
            at.button[0].click().run()
            self.assertEqual(len(at.exception),0)
            self.assertTrue(any('QQQ' in x.value for x in at.subheader))

    def test_invalid_symbol_does_not_break_spy(self):
        with patch('data.stock',side_effect=ValueError('provider unavailable')):
            at=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'),default_timeout=20).run()
            self.assertEqual(len(at.exception),0)
            self.assertEqual(len(at.error),2)
            at.text_input[0].set_value('<bad>')
            at.button[0].click().run()
            self.assertEqual(len(at.exception),0)
            self.assertEqual(len(at.error),3)

    def test_one_failed_stock_keeps_market(self):
        idx=pd.bdate_range('2025-01-01',periods=320)
        close=pd.Series(np.linspace(100,200,320),index=idx)
        def fake(symbol):
            if symbol=='AAPL': raise ValueError('invalid ticker')
            return dict(close=close,name=symbol,fetched=datetime.now(timezone.utc))
        with patch('data.stock',side_effect=fake), patch('data.constituents',return_value=(('A',),'https://example.com')), patch('data.market_closes',return_value=pd.DataFrame({'A':close},index=idx)):
            at=AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'),default_timeout=20).run()
            self.assertEqual(len(at.exception),0)
            self.assertEqual(len(at.error),1)
            self.assertEqual(at.metric[-3].value,'100.0%')
