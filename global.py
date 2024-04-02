import pyupbit
import numpy as np
import time
from collections import deque
import schedule 
from datetime import datetime

access = "NGus8PVOuz6hvM4F9xJNXtGPqxF4sOxUzMabbW1u"          # 본인 값으로 변경
secret = "ArR3LRFSZi8Kci3SfAzkbeNFU34TXnN68a50rEK3"          # 본인 값으로 변경
upbit = pyupbit.Upbit(access, secret)

bestvolcoin = "NULL"
buy_amount_index = 0
buy_amount = 0
now_hold_coin_amount = 0
buy_avg       = 0 

# 거래 코인 결정 함수
def bestVolCoinSearch():
    global bestvolcoin  
    global now_hold_coin_amount

    # KRW마켓에 있는 모든 코인 호출
    krw_tickers = pyupbit.get_tickers("KRW")
    coinNum = len(krw_tickers)
    bestvol = 0

    # 최근4시간 봉이 양봉이면서 30분 간 가장 거래량이 높은 COIN 검색
    for coinNum in krw_tickers:
        price = pyupbit.get_current_price(coinNum) 
        
        df = pyupbit.get_ohlcv(coinNum,interval='minute5',count=6)
        df4 = pyupbit.get_ohlcv(coinNum,interval='day',count=6)

        Search_Coin_df4= pyupbit.get_ohlcv(coinNum, interval='day',count=5)
        for_SearchCoin_minute240_Close= deque(maxlen=20)
        for_SearchCoin_minute240_Open= deque(maxlen=20)
        for_SearchCoin_minute240_Close.extend(Search_Coin_df4['close'])
        for_SearchCoin_minute240_Open.extend(Search_Coin_df4['open'])
        PreMinute_240Close = for_SearchCoin_minute240_Close[-1]
        PreMinute_240Open  = for_SearchCoin_minute240_Open[-1]

        now = datetime.now()
        print("현재 시각:", now)
        print("Searching for trade coin")

        #volsum = (df['volume'][0] + df['volume'][1] + df['volume'][2] + df['volume'][3] + df['volume'][4] + df['volume'][5]) * price
        Fourhourvol = df4['volume'][4] * price
        #if PreMinute_240Open < PreMinute_240Close :
        if coinNum != "KRW-BTC" :
            if Fourhourvol > bestvol :
                bestvol = Fourhourvol
                bestvolcoin = coinNum
                now_hold_coin_amount = upbit.get_balance(coinNum)
                print(coinNum)
                print(bestvol)
    return bestvolcoin
        

# 5분봉을 담을 배열(최대20봉)
minute5_Close = deque(maxlen=20)
minute5_Open  = deque(maxlen=20)

# 30분봉을 담을 배열
minute30_Close= deque(maxlen=20)

# 잔고 조회 krw
def get_balance_krw():    
    balance = upbit.get_balance("KRW")
    return balance
 
# 잔고 조회 coin
def get_balance_wallet(ticker):
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker[4:]:
            balance = b['balance']
            avg_buy_price = b['avg_buy_price']
            return float(avg_buy_price), float(balance)
        else:
            return int(0), int(0)
        
def get_balance(ticker):
    """잔고 조회"""
    balances = upbit.get_balances()
    for b in balances:
        if b['currency'] == ticker:
            if b['balance'] is not None:
                return float(b['balance'])
            else:
                return 0
    return 0

 
#--------------------------------------------------------------------------------------------------------------------------------------------
# 매수 매도 함수
def get_ticker_trend_chagne(ticker):  
    global bestvolcoin  
    global buy_amount_index    
    global buy_amount
    global buy_avg
    global now_hold_coin_amount
    profitPercent = 0

    # 매수 매도 조건 확인 전 5분봉 30 분봉 배열 초기화
    minute5_Close.clear()
    minute30_Close.clear()

    #'''get_ohlcv 함수는 고가/시가/저가/종가/거래량을 DataFrame으로 반환합니다'''
    df5 = pyupbit.get_ohlcv(ticker, interval='minute5',count=5)
    df30= pyupbit.get_ohlcv(ticker, interval='minute30',count=5)
   
    # 매수조건 생성 - 5분봉으로 봤을때 이전 5분봉이 3연속 음봉에 현재 음봉이 이전음봉보다 종가가 낮을 경우
    minute5_Close.extend(df5['close'])
    minute5_Open.extend(df5['open'])
    minute30_Close.extend(df30['close'])
    if now_hold_coin_amount == 0:
        print(f"CoinName: {ticker}, Buy_waiting" )

    total_krw = get_balance("KRW")

    # 이전 봉 3개의 종가가 점점 낮아 지다가 현재 봉의 종가가 마지막 음봉의 시가보다 크고 양봉 종가로 마감했을 경우
    if (minute5_Close[2] < minute5_Close[1] < minute5_Close[0] and minute5_Close[3] > minute5_Close[2] and minute5_Open[3] < minute5_Open[-1] and total_krw > 5000 )   : 
        
        
        print('income buy condition but now buy_avg < now_price')

        krw = get_balance("KRW")

        one_buy_amount = krw * 0.2
        two_buy_amount = krw * 0.2
        thr_buy_amount = krw * 0.3
        for_buy_amount = krw * 0.5
        fiv_buy_amount = krw

        if buy_amount_index == 0 :
            buy_amount = one_buy_amount
        elif buy_amount_index == 1 :
            buy_amount = two_buy_amount
        elif buy_amount_index == 2 :
            buy_amount = thr_buy_amount
        elif buy_amount_index == 3 :
            buy_amount = for_buy_amount
        elif buy_amount_index == 4 :
            buy_amount = fiv_buy_amount
                
        # 5번 이상 구매하지 못하도록
        # 첫 구매 이후에는 평균 매수 금액보다 현재 가격이 -2% 낮을때 조건 출몰시 추매한다.
        if buy_amount_index < 5 :
            if  buy_amount_index == 0 :
                upbit.buy_market_order(ticker, buy_amount*0.9995)
                now_hold_coin_amount = upbit.get_balance(ticker)
                buy_amount_index += 1

                print("sleepBuy")
                time.sleep(303) # 한 번 구매했으면 5분 뒤 구매 ( 같은 봉에서 구매 하지 앉도록하기 위함 )
                return
            elif buy_amount_index >= 1  :
                buy_avg = upbit.get_avg_buy_price(ticker)
                now_price = pyupbit.get_current_price(ticker)
                profitPercent = ((now_price - buy_avg) / buy_avg) * 100
                if profitPercent < -2.0 :
                    upbit.buy_market_order(ticker, buy_amount*0.9995)
                    
                    print(profitPercent)
                    now_hold_coin_amount = upbit.get_balance(ticker)
                    buy_amount_index += 1

                print("sleepBuy")
                time.sleep(303) 
                return
        

    else:
        # 현재 매수가격
        buy_avg = upbit.get_avg_buy_price(ticker)
        
        # 손절/익절가 계산
        vol30_3percent =  minute30_Close[3] + (minute30_Close[3] * -0.03)  #손/익절가
        buy_Minusprofit =  buy_avg + (buy_avg * -0.05)                     #손절가
        sell_Plusprofit =  buy_avg + (buy_avg * 0.05)                      #익절가

        # 현재 가격
        now_price = pyupbit.get_current_price(ticker)
        profitPercent = ((now_price - buy_avg) / buy_avg) * 100
        total_krw = get_balance("KRW")
        if buy_avg != 0:
            print(f"CoinName: {ticker}, Holding" )
            print(f"Buy_avg :{buy_avg}")
            print(f"수익률: {profitPercent}%" )
            print(f"Pre30-3%_price :{vol30_3percent}")
            print(f"Buyavg-5%_price :{buy_Minusprofit}")
            
        # 매도 조건 : 바로 전 30분봉의 종가에서 3% 빠진가격 보다 현재 가격이 낮을 때 시 <or> -3% 이하인 경우 매도
        # 익절 조건 : 수익률 3% 경우 50% 정리 나머지는 홀딩 후 매도조건에 따름
        if (vol30_3percent > now_price and profitPercent > 1.0) or (buy_Minusprofit >= now_price and total_krw < 5000) :
            
            print(vol30_3percent)
            print(now_price)
            
            bal = upbit.get_balance(ticker)
            print(f"{ticker} : All Sell")

            # 시장가 매도
            upbit.sell_market_order(ticker, bal)
            buy_amount_index = 0
            bestvolcoin = "NULL"
            buy_avg = 0
        elif buy_avg >= sell_Plusprofit :
            bal = upbit.get_balance(ticker) * 0.5

            upbit.sell_market_order(ticker, bal)
            
            print("sleepSell")
            time.sleep(303) # 한 번 구매했으면 5분 뒤 판매 ( 같은 봉에서 판매 하지 앉도록하기 위함 )
            return

# 30분간 거래량이 가장 큰 Coin거래 함수 반복실행
while True:    
    try:        
        if bestvolcoin == "NULL" :
            bestVolCoinSearch()

        get_ticker_trend_chagne(bestvolcoin)
        time.sleep(0.5)
    except:
        # print("오류 발생 무시")
        pass

# 수정필요 부분 
    # 1. 매수 조건 확인필요 (진입 조건이 조금 이상함) -> get_ohlc() 함수에서 to= 를 이용해 지금 현재시각이 포함된 5분봉 전부터 5개를 불러와야하나
        # 5분봉, 30분봉을 동일하게 5개씩 불러오는데 인덱스의 순서가 좀 이상함 
        # 5분봉에서 현재시각보다 하나 전의 봉의 인덱스는 [4] 이지만 30분봉에서의 현재보다 하나 전의 봉의 인덱스는[3]이다
        # 30분봉은 어제 로그를 찍어서 종가를 비교해 봤음, 5분봉을 재확인 필요
    
        # 여기에서 to에 들어갈 시간은 현재시각으로..(현재시각 호출해주는 함수 찾아봐야함 반환되는 time stamp form도 고려필요)
        #1-1 interval을 minute1로 지정한 경우 2020-10-10 보다 1분 이전 (2020-10-09 23:59:00)까지의 200개 데이터를 반환합니다.
        #1-2 print(pyupbit.get_ohlcv("KRW-BTC", interval="minute1", to="20201010"))
        #1-3 to = null인 경우 to의 인자에는 현재시각이 들어간다 그러니깐 5분봉으로 했을 때는 현재시각 4:49분이면 4시45분 봉부터 이전 5개를 호출해주는 형식

    # done 2. 손절라인 -3%로 조정 
    # done 3. 익절라인 30분봉으로 전봉의 종가보다 낮은 종가의 봉이 출현했을 때

    # 확인중.. 4. 현재가 호출하는 함수도 확인-> 현재가 호출 함수는 이상없음 //   손절/익절 체결이 이상함 -0.5퍼보다 떨어졌는데 매도가 안됨 (아니면 sleep의 영향 일 수도)
    
    # ★ 5. 한 번의 거래가 끝난 후 jump 또는 재실행 해서 큰 거래량 코인 재검색부터 재실행 되도록 구현
        # 30분간 최대거래량의 코인을 찾는 코드를 함수로 변경하여 거래가 끝났을 때 값을 NULL값으로 만들어 NULL인 경우에만 실행하도록
        # 초기값도 NULL이라서 처음 실행할때도 실행 되도록 함
    
    # 매수 시 현재 매수 평균가보다 낮을때만 구매한다. << 추가할지 좀 보자
    # 첫 매수 후 5분봉 5개의 값을 저장하고 있는 배열의 값이 바뀌질 않음 
    # 그래서 현재 시가보다 종가가 높으면 무조건 추가 구매 됨