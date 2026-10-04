from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
import io
import pandas as pd
import requests
import streamlit as st
import yfinance as yf
from indicators import clean_close, normalize_symbol

NY = ZoneInfo('America/New_York')


def completed_rows(frame, metadata=None, now=None):
    """진행 중 일봉 제거. 메타데이터 없을 때는 뉴욕 16:15 이후만 당일 확정."""
    if frame.empty:
        return frame
    now = now or datetime.now(timezone.utc)
    local = now.astimezone(NY)
    dates = pd.DatetimeIndex(frame.index)
    if dates.tz is not None:
        dates = dates.tz_convert(NY).tz_localize(None)
    today_rows = dates.date == local.date()
    end = ((metadata or {}).get('currentTradingPeriod', {}).get('regular', {}) or {}).get('end')
    completed = local.time().replace(tzinfo=None) >= time(16, 15)
    if end is not None:
        # yfinance may return a timezone-aware Timestamp instead of Unix seconds.
        if isinstance(end, (datetime, pd.Timestamp)):
            trading_end = pd.Timestamp(end)
            if trading_end.tzinfo is None:
                trading_end = trading_end.tz_localize(NY)
            end = trading_end.timestamp()
        else:
            end = float(end)
        if datetime.fromtimestamp(end, NY).date() == local.date():
            completed = now.timestamp() >= end + 900
    return frame.loc[~today_rows] if not completed else frame


@st.cache_data(ttl=1800, max_entries=128, show_spinner=False)
def stock(symbol):
    obj = yf.Ticker(symbol)
    frame = obj.history(period='2y', interval='1d', auto_adjust=True,
                        repair=False, timeout=15, raise_errors=True)
    if frame.empty:
        raise ValueError('시세가 없습니다. 티커를 확인하거나 잠시 후 다시 검색하세요.')
    meta = obj.get_history_metadata() or {}
    if meta.get('currency') != 'USD' or meta.get('instrumentType') not in ('EQUITY', 'ETF'):
        raise ValueError('이 앱은 USD로 거래되는 미국 주식과 ETF를 지원합니다.')
    frame = completed_rows(frame, meta)
    close = clean_close(frame['Close'])
    close.index = pd.DatetimeIndex(close.index).tz_localize(None).normalize()
    return dict(close=close, name=meta.get('longName') or meta.get('shortName') or symbol,
                fetched=datetime.now(timezone.utc))


@st.cache_data(ttl=86400, show_spinner=False)
def constituents():
    urls = [
        'https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv',
        'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',
    ]
    for url in urls:
        try:
            response = requests.get(url, timeout=15, headers={'User-Agent': 'MarketDashboard/1.0'})
            response.raise_for_status()
            table = (pd.read_csv(io.StringIO(response.text)) if url.endswith('.csv')
                     else pd.read_html(io.StringIO(response.text))[0])
            symbols = sorted({normalize_symbol(s) for s in table['Symbol']})
            if 450 <= len(symbols) <= 550:
                return tuple(symbols), url
        except (requests.RequestException, ValueError, KeyError, ImportError):
            continue
    raise ValueError('S&P 500 구성종목 목록을 받지 못했습니다. 잠시 후 다시 확인하세요.')


@st.cache_data(ttl=21600, max_entries=3, show_spinner=False)
def market_closes(symbols, asof):
    # 네트워크 호출은 최초 조회/캐시 만료에만. 최대 네 스레드로 요청량 제한.
    end = (pd.Timestamp(asof) + pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    start = (pd.Timestamp(asof) - pd.Timedelta(days=730)).strftime('%Y-%m-%d')
    def get_one(symbol):
        try:
            frame = yf.Ticker(symbol).history(start=start, end=end, interval='1d',
                        auto_adjust=True, repair=False, timeout=12, raise_errors=True)
            if frame.empty:
                return symbol, pd.Series(dtype=float)
            close = clean_close(frame['Close'])
            close.index = pd.DatetimeIndex(close.index).tz_localize(None).normalize()
            return symbol, close
        except Exception:
            return symbol, pd.Series(dtype=float)
    with ThreadPoolExecutor(max_workers=4) as pool:
        probes = dict(pool.map(get_one, symbols[:4]))
        if not any(not s.empty for s in probes.values()):
            raise ValueError('데이터 제공처에 접속할 수 없어 시장 전체 조회를 중단했습니다. 잠시 후 다시 검색하세요.')
        rows = {**probes, **dict(pool.map(get_one, symbols[4:]))}
    return pd.DataFrame(rows).sort_index()
