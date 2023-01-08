import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
import warnings
from PIL import Image
from PIL import ImageDraw
from tkinter.tix import COLUMN
from pyparsing import empty
from haversine import haversine
import webbrowser
st.set_page_config(layout="wide")

empty3,con2,empty4 = st.columns([1.2,1,1])
with con2:
    st.image("119.png")



warnings.filterwarnings('ignore')
st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)


# 부산광역시 
# 응급실 실시간 데이터
pd.set_option('display.max_columns', None)
url = 'https://apis.data.go.kr/B552657/ErmctInfoInqireService/getEmrrmRltmUsefulSckbdInfoInqire?serviceKey=Zv%2FutM8zPV4Cpby0tQi%2FtiDmHPhc19Zr67HNB4XUKyLt89VHIxcmVtAdRSWES5ve3JQGe4P3OL6dyL6vChTt8Q%3D%3D&STAGE1=%EB%B6%80%EC%82%B0%EA%B4%91%EC%97%AD%EC%8B%9C&pageNo=1&numOfRows=100'
df1 = pd.read_xml(url, xpath='.//item')
df1_c = df1.copy()
df2 = df1_c[['dutyName','hpid','hvec','hvoc', 'dutyTel3']]
df2_c = df2.rename(columns={'dutyName':'병원명', 'hpid':'병원코드', 'hvoc':'수술실수', 'dutyTel3':'응급실연락처','hvec':'응급실수'})
# df2_c

# 중증질환자 수용가능정보 실시간 데이터
url = 'https://apis.data.go.kr/B552657/ErmctInfoInqireService/getSrsillDissAceptncPosblInfoInqire?serviceKey=Zv%2FutM8zPV4Cpby0tQi%2FtiDmHPhc19Zr67HNB4XUKyLt89VHIxcmVtAdRSWES5ve3JQGe4P3OL6dyL6vChTt8Q%3D%3D&STAGE1=%EB%B6%80%EC%82%B0%EA%B4%91%EC%97%AD%EC%8B%9C&pageNo=1&numOfRows=100'
df3 = pd.read_xml(url, xpath='.//item')
df3.columns = ['병원명','병원코드','뇌출혈','신생아','중증화상','뇌경색','응급실','심근경색','복부손상','사지접합','응급내시경','응급투석', '조산산모','정신질환자']
df3.drop(['병원명','정신질환자','응급실'],axis=1, inplace=True)
# df3

# 병원 위치 데이터
url = 'https://apis.data.go.kr/B552657/ErmctInfoInqireService/getEgytListInfoInqire?serviceKey=Zv%2FutM8zPV4Cpby0tQi%2FtiDmHPhc19Zr67HNB4XUKyLt89VHIxcmVtAdRSWES5ve3JQGe4P3OL6dyL6vChTt8Q%3D%3D&Q0=%EB%B6%80%EC%82%B0%EA%B4%91%EC%97%AD%EC%8B%9C&pageNo=1&numOfRows=100'
df4 = pd.read_xml(url, xpath='.//item')
df5 = df4[['phpid','dutyAddr','wgs84Lat','wgs84Lon']]
df5_c = df5.rename(columns={'phpid':'병원코드','dutyAddr':'병원주소','wgs84Lat':'위도','wgs84Lon':'경도'})
# df5_c

# 총 데이터 merge
dfx = pd.merge(df2_c, df5_c, on='병원코드')
dfa = pd.merge(dfx, df3, on='병원코드', how='outer')
# dfa

# 병원별 전체병상수, 응급실 포화도/상태 추가
er = pd.read_excel('er1.xlsx')
er.drop(['Unnamed: 0','병원명'], axis=1, inplace=True)
df_er = pd.merge(dfa, er, on='병원코드')
df_er['응급실포화도'] = (1-df_er['응급실수']/df_er['전체병상수'])*100
df_er['응급실포화상태'] = df_er['응급실포화도']
df_er['응급실포화상태'] = pd.cut(df_er['응급실포화상태'] ,bins=[0,30,60,90,np.inf],labels=["원활","보통","혼잡","매우혼잡"],right=False) #라벨 설정
df_er.insert(6, column= "거리", value= 0)

A = (35.11492,  129.04251)
for i in range(df_er.shape[0]):
    B = (df_er["위도"][i], df_er["경도"][i])
    df_er["거리"][i] = round(haversine(A, B), 3)
    
df_er = df_er[(df_er['응급실수']>0)&(df_er['수술실수']>0)]
df_er = df_er.reset_index(drop=True)    
    
    
now = datetime.now() # 현재 시각

empty5,con3,empty6 = st.columns([0.6,0.7,0.5])
with con3:
    st.header(now)
    

# st.header("중증질환")
tab1, tab2, tab3 = st.tabs(["환자", "병원", "지도"])


with tab1:
    st.header("환자정보")
    cols1, cols2 = st.columns(2)
    with cols1:
        name = st.text_input('이름', "홍길동") # 최초 입력 값
    with cols2:
        sex = st.radio(label = '성별', options = ['남', "여"])
    cols3, cols4 = st.columns(2)
    with cols3:
        birth = st.text_input('생년월일(8자리를 입력해주세요)', "20220101")
    etc = 0
    if (int(birth)<19000000)or(int(birth)>21000000):
        st.write("잘못 입력하셨습니다.")
    else:
        age = int(now.year)-int(birth[:4])+1
        with cols4:
            age1 = str(age)+"세"
            age2 = st.text_input("나이", age1)
        if age >=65:
            etc= "고령자"
            st.write("특이사항:", etc)

    st.header("상태")

    final_check = []
    col1, col2 = st.columns(2)
    with col1:
        high_blood = st.number_input("수축기 혈압", min_value=10, max_value=200, value=120, step=1) # 140이상 고혈압, 90이하 저혈압
    with col2:
        low_blood = st.number_input('이완기 혈압', min_value=10, max_value=200, value=80, step=1)   #  90이상 고혈압, 60이하 저혈압
    if (high_blood >= 140) or (low_blood >= 90):
        final_check += ["고혈압"]
    if (high_blood <=  95) or (low_blood <= 65):
        final_check += ["저혈압"]

    col3, col4 = st.columns(2)
    with col3:
        temperature = st.number_input("체온", min_value=20.0, max_value=50.0, value=36.5, step=0.1)
    if temperature >= 37.5:
        final_check += ["발열"]
    if temperature <= 35.5:
        final_check += ["저체온"]

    with col4:
        heart_rate = st.number_input("심박수(분당)", min_value=10, max_value=200, value=70, step=1)
    if etc == "고령자":
        if (heart_rate<=55) or (heart_rate>=85):
            final_check += ["맥박이상"]
    else:
        if (heart_rate<=60) or (heart_rate>=80):
            final_check += ["맥박이상"]

    situation = st.radio(label = '중증질환 예측 필요 여부', options = ['필요', "불필요"])
    if situation == "불필요":
        option = st.selectbox('판단', ("중증질환 아님", '뇌출혈', '신생아', '중증화상', "뇌경색", "심근경색", "복부손상", "사지접합", "응급내시경", "응급투석", "조산산모"))
        if st.button('저장'):
            if option == "중증질환 아님":
#                result1 = df_er
                with tab2:
                    result1 = df_er.copy()
                    sorting = "응급실포화도"
                    result1 = df_er.sort_values(sorting, ascending=True)
                    result1 = result1.reset_index(drop=True)
            
                    st.write(option)
                    st.write("모든 병원을 응급실포화도순으로 출력합니다.")
#                     sorting = st.selectbox('정렬기준',('응급실포화도', '거리'))
#                         sorting = "응급실포화도"
#                         result1 = df_er.sort_values(sorting, ascending=True)
#                         result1 = result1.reset_index(drop=True)
# #                         st.write("데이터프레임")
#                         st.write(result1[["병원명", "거리", "응급실수", "수술실수", "응급실포화상태"]])

                        
                    
                    co1, co2, co3 = st.columns([0.7, 0.4, 1.0])
                    with co1:
                        st.write("병원선정")
                        for i in range(result1.shape[0]):
                            st.write("="*40)
                            if st.button(result1["병원명"][i]):
                                st.write("병원선정")
                    with co2:
                        st.write("응급실연락처")
                        for i in range(result1.shape[0]):
                            st.write("="*15)
                            if st.button(result1["응급실연락처"][i]):
                                with tab2:
                                    st.write(result1["병원명"][i], result1["응급실연락처"][i], "에 연결 중입니디.")
                    with co3:
#                         sorting = "응급실포화도"
#                         result1 = df_er.sort_values(sorting, ascending=True)
#                         result1 = result1.reset_index(drop=True)
                        st.write("데이터프레임")
                        st.write(result1[["병원명", "거리", "응급실수", "수술실수", "응급실포화상태"]])
# #                             url = f"https://map.naver.com/v5/directions/14364913.508788805,4179550.113085119,%EB%B6%80%EC%82%B0%EC%97%AD%20%EA%B2%BD%EB%B6%80%EC%84%A0(%EA%B3%A0%EC%86%8D%EC%B2%A0%EB%8F%84),13479631,PLACE_POI/14362166.744881283,4180223.5237070248,{result1["병원명"][i]},12131100,PLACE_POI/-/transit?c=14362539.3543570,4179682.5843453,14,0,0,0,dh"
#                         for i in range(result1.shape[0]):
#                                 if st.button("확정"):
#                                     st.write("길안내를 시작합니다.")
# #                                 with tab3:
# #                                     webbrowswer.open(url)
                                    
            else:
                result1 = df_er[df_er[option]=='Y']
                with tab2:
                    st.write(f'{option} 수술이 가능한 병원을 거리순으로 출력합니다.')
                    sorting = '거리'
                    result1 = result1.sort_values(sorting, ascending=True)
                    result1 = result1.reset_index(drop=True)
                    
                    co1, co2, co3 = st.columns([0.7, 0.4, 1.0])
                    with co1:
                        st.write("병원선정")
                        for i in range(result1.shape[0]):
                            st.write("="*40)
                            if st.button(result1["병원명"][i]):
                                st.write("병원선정")
                    with co2:
                        st.write("응급실연락처")
                        for i in range(result1.shape[0]):
                            st.write("="*15)
                            if st.button(result1["응급실연락처"][i]):
                                st.write("전화성공.")
                    with co3:
#                         sorting = "응급실포화도"
#                         result1 = df_er.sort_values(sorting, ascending=True)
#                         result1 = result1.reset_index(drop=True)
                        st.write("데이터프레임")
                        st.write(result1[["병원명", "거리", "응급실수", "수술실수", "응급실포화상태"]])
              
    else:
        chk1, chk2 = st.columns(2)
        with chk1:
            check1 = st.multiselect('통증/외상_복수선택가능', ['두통', '흉통', '복통', '요통', '골절', '탈구', '염좌', '열상', "찰과상", "타박상"])
        with chk2:
            check2 = st.multiselect('추가증상_복수선택가능', ["붓기", "호흡곤란", "기력없음", "어지럼증", "가슴답답함", "의식저하", "구토", "마비", "감각이상", "구역질", "식은땀", "이물질", "쇼크"])

        final_check += check1
        final_check += check2

        with st.expander('증상 보기') :
            for i in final_check:
                st.write(i)

        from sklearn.tree import DecisionTreeClassifier
        from sklearn.metrics import *

        disease = pd.read_csv("self.csv")
        patient = pd.DataFrame(index=[0], data=0, columns = disease.columns)
        patient = patient.drop(['수술명'], axis=1)
 
        for i in final_check:
            if i in patient.columns:
                patient.loc[0, i] = 1

        x = disease.drop(['수술명'], axis=1)
        y = disease['수술명']
        model = DecisionTreeClassifier()
        model.fit(x,y)

        if st.button('저장'):
            with tab2:
                pred = model.predict(patient)
                result = df_er[df_er[pred[0]]=='Y']
                st.write(f'필요한 수술은 {pred[0]}입니다.')
                st.write(f'{pred[0]} 수술이 가능한 병원을 거리순으로 출력합니다.')
                sorting = "거리"
                result1 = result.sort_values(sorting, ascending=True)
                result1 = result1.reset_index(drop=True)
                
                co1, co2, co3 = st.columns([0.7, 0.4, 1.0])
                with co1:
                    st.write("병원선정")
                    for i in range(result1.shape[0]):
                        st.write("="*40)
                        if st.button(result1["병원명"][i]):
                            st.write("병원선정")
                with co2:
                    st.write("응급실연락처")
                    for i in range(result1.shape[0]):
                        st.write("="*15)
                        if st.button(result1["응급실연락처"][i]):
                            st.write("전화성공.")
                with co3:
#                         sorting = "응급실포화도"
#                         result1 = df_er.sort_values(sorting, ascending=True)
#                         result1 = result1.reset_index(drop=True)
                    st.write("데이터프레임")
                    st.write(result1[["병원명", "거리", "응급실수", "수술실수", "응급실포화상태"]])

                
with tab3:
    empty1,con1,empty2 = st.columns([0.3,1.0,0.3])
    with empty1:
        empty() # 여백부분1
    with con1:
        st.image("지도.png")
    with empty2:
        empty() # 여백부분2




