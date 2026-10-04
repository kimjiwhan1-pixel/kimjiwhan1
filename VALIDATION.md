# 검증 기록

- RSI 기준값, SMA200, 결측 데이터, 장중/조기마감 일봉 제외, 시장 비중 분모, 제공처 오류 중단 검사.
- Streamlit AppTest: 티커 검색, 카드 수치, 종목 오류 시 SPY/시장 유지, 입력 오류 표시.
- 총 14개 검사 통과. Python 구문 검사 및 설치 의존성 검사 통과.
- Streamlit 서버가 로컬에서 시작되고 health endpoint가 HTTP 200 응답.
- 실제 Yahoo AAPL/SPY 조회는 HTTP 429 호출 제한으로 완료하지 못함. 합성 데이터는 검사에만 사용하며 앱에 표시되지 않음.
- 실제 500종목 조회, TradingView 외부 위젯 표시, Streamlit Community Cloud 배포 후 동작은 아직 검증하지 못함.
- GitHub 브라우저 로그인 확인됨. Streamlit 배포 후 실시간 조회 검증 필요.
