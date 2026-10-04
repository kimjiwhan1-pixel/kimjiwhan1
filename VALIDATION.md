# 검증 기록

- RSI 기준값, SMA200, 결측 데이터, 장중/조기마감 일봉 제외, 시장 비중 분모, 제공처 오류 중단 검사.
- yfinance 거래 종료 메타데이터의 Unix 시간, timezone-aware Timestamp, timezone-naive Timestamp 처리 검사.
- Streamlit AppTest: 티커 검색, 카드 수치, 종목 오류 시 SPY/시장 유지, 입력 오류 표시.
- 총 15개 검사 통과. Python 구문 검사 및 설치 의존성 검사 통과.
- Streamlit 서버 로컬 health endpoint HTTP 200.
- 2026-10-04 Streamlit Community Cloud Python 3.12 배포 완료: https://kimjiwhan-us-market.streamlit.app/
- 배포 환경에서 AAPL과 SPY 시세/RSI/SMA200/이격도 정상 표시 확인. QQQ 검색 후 카드와 차트 변경 확인.
- 2026-10-02 기준 S&P 500 구성 503개 중 501개 수신, 229개 200일선 상회, 비중 45.7%, 수신 범위 99.6% 확인.
- TradingView INDEX:S5TH 외부 참고 차트 표시 확인. 앱 계산 비중과 별도 지표이며 값이 같을 필요는 없음.
- 로컬 환경 Yahoo 호출은 429 제한을 받았으나 배포 환경에서 실제 시세를 수신함. 합성 데이터는 검사에만 사용하며 앱에 표시하지 않음.
- 무료 데이터의 지연·누락·호출 제한과 서비스 자원/절전 제한은 이후에도 발생할 수 있음.
