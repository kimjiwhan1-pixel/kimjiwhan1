from zoneinfo import ZoneInfo
import streamlit as st
from data import stock, constituents, market_closes
from indicators import normalize_symbol, metrics, breadth

st.set_page_config(page_title='미국 주식 · ETF 대시보드', page_icon='📈', layout='wide')
st.title('미국 주식 · ETF 대시보드')
st.caption('티커 검색으로 RSI와 200일선 추세를 확인하세요. 가격은 장 마감 후 확정된 일봉 기준입니다.')

with st.form('search'):
    c1, c2 = st.columns([4, 1])
    value = c1.text_input('미국 주식·ETF 티커', value=st.session_state.get('ticker', 'AAPL'),
                         placeholder='AAPL, NVDA, QQQ, VOO, BRK.B')
    submitted = c2.form_submit_button('검색', use_container_width=True)
if submitted:
    try:
        st.session_state.ticker = normalize_symbol(value)
    except ValueError as exc:
        st.error(str(exc))
symbol = st.session_state.get('ticker', 'AAPL')


def render_stock(symbol, chart=True):
    try:
        with st.spinner(f'{symbol} 일봉을 불러오는 중…'):
            result = stock(symbol)
            m = metrics(result['close'])
        st.subheader(f"{symbol} · {result['name']}")
        fetched = result['fetched'].astimezone(ZoneInfo('Asia/Seoul'))
        st.caption(f"기준 거래일: {m['date']:%Y-%m-%d} (미국) · 조회: {fetched:%m-%d %H:%M} (한국)")
        cols = st.columns(4)
        cols[0].metric('확정 일봉 종가', f"${m['price']:,.2f}")
        cols[1].metric('RSI (14)', '—' if m['rsi14'] is None else f"{m['rsi14']:.1f}",
                       help='Wilder 방식. 70 이상 과매수, 30 이하 과매도라는 관례적 구간입니다.')
        cols[2].metric('200일 이동평균', '—' if m['sma200'] is None else f"${m['sma200']:,.2f}")
        cols[3].metric('200일선 이격도', '—' if m['distance'] is None else f"{m['distance']:+.2f}%",
                       help='(확정 종가 ÷ 200거래일 단순이동평균 − 1) × 100')
        if m['sma200'] is None:
            st.info(f"확보한 일봉이 {m['count']}개입니다. 200개가 쌓여야 SMA200과 이격도를 계산합니다.")
        if chart:
            st.line_chart(m['chart'].tail(320), height=360)
            label = '최근 252거래일 종가 고점 대비' if m['count'] >= 252 else '확보 기간 종가 고점 대비'
            st.caption(f"{label}: {m['drawdown']:+.2f}% · 배당·분할을 반영한 조정종가")
        return m
    except Exception as exc:
        st.subheader(symbol)
        st.error('시세를 불러오지 못했습니다. 티커를 확인하거나 잠시 후 다시 검색하세요.')
        with st.expander('오류 내용'):
            st.write(str(exc))
        return None

selected = render_stock(symbol)
st.divider()
st.subheader('SPY 시장 추세')
spy = selected if symbol == 'SPY' else render_stock('SPY', chart=False)

st.divider()
st.subheader('S&P 500 · 200일선 상회 종목 비중')
st.caption('시장 전체 지표입니다. 검색한 종목의 ETF 구성 비율과는 다릅니다. 최초 조회에는 몇 분이 걸릴 수 있습니다.')
if spy is not None:
    try:
        with st.spinner('S&P 500 구성종목의 200일선을 계산하는 중… (결과는 6시간 재사용)'):
            symbols, source = constituents()
            closes = market_closes(symbols, spy['date'].strftime('%Y-%m-%d'))
            b = breadth(closes, symbols, spy['date'])
        cols = st.columns(3)
        cols[0].metric('계산 가능한 종목 중 상회 비율', f"{b['value']:.1f}%",
                       delta=None if b['delta'] is None else f"{b['delta']:+.1f}%p",
                       help='전일 변화는 양일 모두 계산 가능한 동일 종목 집합 기준입니다.')
        cols[1].metric('200일선 상회', f"{b['above']} / {b['valid']}개")
        cols[2].metric('전체 구성종목 대비 계산 범위', f"{b['coverage']:.1f}%")
        st.caption(f"기준 거래일: {b['date']:%Y-%m-%d} · 전체 {b['total']}개 증권 · 전일 비교 대상 {b['common_n']}개")
        if b['coverage'] < 95:
            st.warning('데이터 누락이 많아 시장 전체를 충분히 대표하지 못할 수 있습니다. 이 수치는 수신된 종목의 비율입니다.')
        st.line_chart(b['chart'].rename('상회 비율 (%)'), height=250)
        st.caption('최근 약 6개월 · 현재 구성종목으로 과거를 계산하므로 당시의 구성종목 기준 지표와 차이가 있습니다.')
        with st.expander('계산 기준 및 누락 종목'):
            st.write('각 종목의 실제 종가 200개 평균보다 기준일 종가가 높은 경우만 상회로 셉니다. 결측 가격은 전일 가격으로 채우지 않습니다.')
            st.write('누락 또는 200일봉 미확보: ' + (', '.join(b['missing']) or '없음'))
            st.markdown(f'[구성종목 목록 출처]({source})')
    except Exception as exc:
        st.warning('시장 전체 데이터를 받지 못했습니다. 다른 지표는 계속 사용할 수 있습니다.')
        with st.expander('시장 지표 오류 내용'):
            st.write(str(exc))
else:
    st.info('SPY의 기준 거래일을 받으면 시장 전체 비중을 계산합니다.')

with st.expander('TradingView S5TH 참고 차트'):
    st.caption('아래는 외부 참고 위젯입니다. 위의 수치는 Yahoo Finance 가격으로 앱이 계산한 값이며 S5TH 값을 가져온 것이 아닙니다. 위젯이 표시되지 않으면 원본 페이지에서 확인하세요.')
    st.link_button('TradingView S5TH 원본 열기', 'https://www.tradingview.com/symbols/INDEX-S5TH/')
    st.iframe('''<div class="tradingview-widget-container" style="height:350px;width:100%">
<div class="tradingview-widget-container__widget" style="height:318px;width:100%"></div>
<div class="tradingview-widget-copyright"><a href="https://www.tradingview.com/symbols/INDEX-S5TH/" target="_blank" rel="noopener nofollow">S5TH chart</a> by TradingView</div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
{"autosize":true,"symbol":"INDEX:S5TH","interval":"D","timezone":"America/New_York","theme":"light","style":"2","locale":"kr","allow_symbol_change":false,"save_image":false,"support_host":"https://www.tradingview.com"}
</script></div>''', height=360, alt='TradingView S5TH 참고 차트')

st.divider()
st.caption('가격: Yahoo Finance (yfinance) · RSI/SMA200/상회 비중: 앱 직접 계산 · 무료 데이터는 지연·누락·호출 제한이 있을 수 있습니다.')
with st.expander('계산 방법'):
    st.write('가격은 배당·분할 조정종가입니다. RSI는 첫 14일 변동 평균으로 초기화한 Wilder 방식, SMA200은 200거래일 단순평균입니다. 이격도는 (종가/SMA200−1)×100입니다. 장중 일봉은 제외하며 마감 후 15분부터 당일 값을 포함합니다.')
    st.write('종목·SPY 시세는 30분, 시장 전체 가격은 6시간 동안 재사용합니다. 앱을 다시 열면 필요한 최신 데이터를 자동으로 조회합니다.')
