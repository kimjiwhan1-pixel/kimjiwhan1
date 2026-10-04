"""지표 계산: Wilder RSI는 첫 14개 변동의 산술평균으로 초기화한다."""
import re
import numpy as np
import pandas as pd


def normalize_symbol(value):
    symbol = value.strip().upper().replace('.', '-')
    if not re.fullmatch(r'[A-Z][A-Z0-9-]{0,11}', symbol):
        raise ValueError('미국 주식·ETF 티커를 입력하세요. 예: AAPL, QQQ, BRK.B')
    return symbol


def clean_close(close):
    close = pd.to_numeric(close, errors='coerce').replace([np.inf, -np.inf], np.nan)
    close = close[close > 0].dropna().sort_index()
    return close[~close.index.duplicated(keep='last')].astype(float)


def wilder_rsi(close, period=14):
    close = clean_close(close)
    out = pd.Series(np.nan, index=close.index, dtype=float)
    if len(close) <= period:
        return out
    diff = close.diff()
    gains = diff.clip(lower=0).to_numpy()
    losses = (-diff.clip(upper=0)).to_numpy()
    ag, al = gains[1:period + 1].mean(), losses[1:period + 1].mean()
    for i in range(period, len(close)):
        if i > period:
            ag = (ag * (period - 1) + gains[i]) / period
            al = (al * (period - 1) + losses[i]) / period
        out.iloc[i] = 50 if ag == al == 0 else 100 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def metrics(close):
    close = clean_close(close)
    if close.empty:
        raise ValueError('시세를 받지 못했습니다. 티커 또는 데이터 제공처 상태를 확인하세요.')
    ma = close.rolling(200, min_periods=200).mean()
    price = float(close.iloc[-1])
    s200 = float(ma.iloc[-1]) if len(close) >= 200 else None
    rsi = wilder_rsi(close).iloc[-1]
    high = float(close.tail(252).max())
    return dict(close=close, chart=pd.DataFrame({'종가': close, 'SMA200': ma}),
                date=close.index[-1], price=price, sma200=s200,
                rsi14=None if pd.isna(rsi) else float(rsi),
                distance=None if s200 is None else (price / s200 - 1) * 100,
                drawdown=(price / high - 1) * 100, count=len(close))


def breadth(closes, symbols, asof):
    """동일 날짜 데이터만 집계. 전일 변화는 양일 모두 유효한 종목으로 계산."""
    idx = pd.DatetimeIndex(closes.index).tz_localize(None).normalize()
    data = closes.copy()
    data.index = idx
    data = data.sort_index().loc[:pd.Timestamp(asof).tz_localize(None).normalize()]
    data = data.loc[~data.index.duplicated(keep='last')].reindex(columns=symbols)
    if data.empty:
        raise ValueError('시장 전체 데이터를 받지 못했습니다.')
    # 결측치를 전일 가격으로 채우지 않는다. 각 종목의 실제 200개 종가를 사용한다.
    ma = pd.DataFrame(index=data.index, columns=data.columns, dtype=float)
    for symbol in symbols:
        clean = clean_close(data[symbol])
        ma[symbol] = clean.rolling(200, min_periods=200).mean().reindex(data.index)
    valid = data.notna() & (data > 0) & ma.notna()
    above = (data > ma) & valid
    count = valid.sum(axis=1)
    series = (above.sum(axis=1) / count.replace(0, np.nan) * 100).dropna()
    date = pd.Timestamp(asof).tz_localize(None).normalize()
    if date not in data.index or count.loc[date] == 0:
        raise ValueError('기준 거래일의 시장 데이터를 확보하지 못했습니다. 이전 날짜를 최신 값으로 표시하지 않습니다.')
    n, a = int(count.loc[date]), int(above.loc[date].sum())
    previous_dates = series.index[series.index < date]
    delta, common_n = None, 0
    if len(previous_dates):
        prev = previous_dates[-1]
        # 직전 행(거래일)의 데이터가 아예 없으면 전일 대비로 오인하지 않는다.
        if data.index.get_loc(prev) == data.index.get_loc(date) - 1:
            common = valid.loc[date] & valid.loc[prev]
            common_n = int(common.sum())
            if common_n:
                delta = float((above.loc[date, common].mean() - above.loc[prev, common].mean()) * 100)
    return dict(date=date, value=a / n * 100, above=a, valid=n, total=len(symbols),
                coverage=n / len(symbols) * 100, delta=delta, common_n=common_n,
                chart=series.tail(126), missing=[s for s in symbols if not valid.loc[date, s]])
