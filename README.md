# 미국 주식·ETF 대시보드 — Streamlit Community Cloud

Replit과 OpenAI API 없이 실행하는 웹앱입니다. 종목 검색, Wilder RSI(14), SMA200,
200일선 이격도, 종가 고점 대비, SPY 추세, S&P 500 시장 비중을 표시합니다.

## 한 번만 배포하면 주소로 사용

1. GitHub에 `us-market-dashboard` 저장소를 만듭니다.
2. 이 폴더의 **내용물**을 저장소 루트에 업로드합니다. `app.py`, `data.py`,
   `indicators.py`, `requirements.txt`가 루트에 있어야 합니다.
3. https://share.streamlit.io/ 에 로그인하고 GitHub를 연결합니다.
4. `Create app` → `Yup, I have an app`에서 저장소, `main` 브랜치,
   `app.py`를 선택합니다. Advanced settings에서 Python 3.12를 선택합니다.
5. `Deploy`를 누릅니다. 발급된 `https://….streamlit.app` 주소를 즐겨찾기에 저장합니다.

사용자 PC에 Python 설치나 파일 실행은 필요 없습니다.
무료 플랫폼에도 자원 제한과 비활성 앱 절전이 있으며, 시세 제공처가 호출을
제한할 수 있습니다. 계속 켜져 있는 유료 서버를 계약하는 구성은 없습니다.
현재 플랫폼 조건은 https://docs.streamlit.io/deploy/streamlit-community-cloud 를 확인하세요.

## 데이터와 계산

- 주식·ETF 가격: Yahoo Finance, yfinance. USD 주식/ETF만 지원합니다.
- 종가는 배당·분할 조정종가입니다. 미조정 차트 또는 다른 공급처와 값이 다를 수 있습니다.
- RSI: 첫 14개 종가 변동의 평균으로 초기화 후 Wilder 평활.
- SMA200: 유효한 종가 200개 단순평균. 부족하면 가격과 RSI만 표시합니다.
- 진행 중 일봉 제외: 뉴욕 거래 종료 시각 + 15분. 종료 메타데이터를 받지 못하면
  뉴욕 16:15 이후 포함합니다. 실시간 현재가를 보여 주는 앱은 아닙니다.
- 52주 고점 대비는 최근 252거래일 **조정종가 최고값** 대비입니다. 장중 고가는 아닙니다.
- S&P 500 구성종목: datasets CSV, 실패 시 Wikipedia 목록. 구성종목의 복수 주식
  종류를 각각 셀 수 있어 증권 수는 정확히 500이 아닐 수 있습니다.
- 시장 비중: SPY의 최신 확정 거래일과 같은 날짜의 유효한 구성종목만 분모로
  사용합니다. 데이터 누락과 200일 미확보 종목을 제외하며 수신 범위를 함께 표시합니다.
- 전일 변화는 양일 모두 유효한 동일 종목 집합의 차이입니다.
- 시장 비중 과거 차트는 현재 구성종목을 사용합니다. 당시 구성종목 기준의 공식
  지수나 TradingView S5TH와 일치하는 것으로 간주하면 안 됩니다.
- TradingView S5TH는 참고 위젯/링크입니다. 위젯 심볼 지원에 따라 표시가 제한될
  수 있습니다. 이 앱은 S5TH를 스크래핑하거나 내부 숫자로 가져오지 않습니다.
- 캐시: 개별 종목 30분/최대 128종목, 시장 가격 6시간/최대 3개 집합, 목록 24시간.
  최초 시장 조회는 약 500종목을 최대 4개 스레드로 요청하므로 몇 분이 걸릴 수
  있습니다. 빈 데이터는 수치를 만들어 표시하지 않습니다.

## 개발 검증

```
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app.py
```

비밀번호, 증권계좌 또는 OpenAI API 키를 입력하는 기능은 없습니다.
