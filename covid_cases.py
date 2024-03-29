#!/usr/bin/env python
# coding: utf-8

from covid import Covid
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
import pandas as pd
import requests
import json
import shutil

os.environ['TZ'] = 'US/Eastern'
if os.name != 'nt':
    time.tzset()

#keep country name in the same format
trans_jhu = ['United Kingdom','United Arab Emirates','Korea, South','China','Taiwan*']
trans_bbg = ['UK','UAE','South Korea','Mainland China','Taiwan']

#dictionary to translate country names
trans_en = ['US','United Kingdom','India','Brazil','Russia','Colombia','Peru','Mexico','Spain','Argentina','South Africa','France','Chile','Iran','Bangladesh','Iraq','Saudi Arabia','Turkey','Pakistan','Italy','Philippines','Germany','Portugal','Indonesia','Czechia','Poland','Ukraine','Malaysia','United Arab Emirates','Japan','Belgium','Netherlands','Korea, South','Vietnam','Austria','China','Australia','Taiwan*']
trans_cn = ['美国','英国','印度','巴西','俄罗斯','哥伦比亚','秘鲁','墨西哥','西班牙','阿根廷','南非','法国','智利','伊朗','孟加拉','伊拉克','沙特','土耳其','巴基斯坦','意大利','菲律宾','德国','葡萄牙','印尼','捷克','波兰','乌克兰','马来西亚','阿联酋','日本','比利时','荷兰','韩国','越南','奥地利','中国','澳大利亚','中国台湾']

def trans(x, orig, final):
    if len(orig) != len(final):
        print('Check length of the translation map!')
        return 0
    for i in range(len(orig)):
        x = x.replace(orig[i],final[i])
    return x

#get covid cases from Jhu
covid = Covid()
jhu = sorted(covid.get_data(), key = lambda i:i['confirmed'], reverse=True)


tmp = [[d['id'], d['country'], d['confirmed']] for d in jhu]
tmp=pd.DataFrame(tmp,columns=['id', 'country',time.strftime('%Y%m%d', time.localtime())])
tmp['id'] =pd.to_numeric(tmp['id'])
tmp.sort_values('id',inplace=True)
tmp.drop('id', axis=1, inplace=True)

path = "./data"
if not os.path.exists(path):
    os.mkdir(path)

if os.path.isfile('./data/data.csv'):
    jhu_data = pd.read_csv('./data/data.csv')
    jhu_data.to_csv('./data/data_bak.csv',index=0)
    
    #use the latest result as today's data
    if jhu_data.columns.values[2] == tmp.columns.values[1]:
        jhu_data = jhu_data.drop(jhu_data.columns.values[2], axis=1)
    
    #country id changed, can't merge with id anymore
    jhu_data = pd.merge(tmp, jhu_data, on=['country'])
    jhu_data.insert(0,'id',jhu_data.pop('id'))
    try:
        jhu_data.drop('id_x', axis=1, inplace=True)
    except:
        print('id seems the same.')

else:
    jhu_data = tmp
    
jhu_data.to_csv('./data/data.csv',index=0)

#keep only id, country and cases for two days
jhu_data = jhu_data.iloc[:,1:4]
jhu_data['new_cases'] = jhu_data.iloc[:,1] - jhu_data.iloc[:,2]
jhu_data.sort_values('new_cases',inplace=True, ascending=False)

#check whether we have missing dates, if so new_cases should be NA
if (datetime.strptime(jhu_data.columns.values[1],'%Y%m%d') - datetime.strptime(jhu_data.columns.values[2],'%Y%m%d')).days != 1:
    jhu_data['new_cases'] = pd.NA


bbgurl = 'https://www.bloomberg.com/graphics/covid-vaccine-tracker-global-distribution/?terminal=true'
try:
    header={
    'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-us) AppleWebKit/534.50 (KHTML, like Gecko) Version/5.1 Safari/534.50'
}
    rep = requests.get(bbgurl,headers = header)
    rep = BeautifulSoup(rep.text, 'html.parser').find("script", {"id": "dvz-data-cave"})
    vacc = json.loads(rep.next)
    vacc = [[d['name'], [d.get('noCompletedVaccinationPerCapita',None), d.get('noBoosterTotalPerCapita',None)]] for d in vacc['vaccination']['global']]
    vacc=dict(vacc)
    vacc_flag = True
except:
    vacc_flag = False

for num_country in [7,5]:
    jhu_us = jhu_data.loc[jhu_data['country'] == 'US']
    jhu_data = jhu_data.drop(jhu_data.loc[jhu_data['country'] == 'US'].index[0])
    jhu_data = pd.concat([jhu_us,jhu_data.iloc[0:(num_country - 1),:]])

    #start building sentence  
    date = time.strftime("%Y/%m/%d %H:%M",time.localtime(jhu[0]['last_update'] // 1000))
    
    printlist = list(jhu_data['country'])
    
    newcases = ["{:.1f}".format(x/10000) for x in list(jhu_data['new_cases'])]
    
    #above 5 million cases
    countrylist = [x for x in jhu if x['confirmed']>10000000]
    countrylist = [x['country'] for x in countrylist]

    extralist = [x for x in countrylist if x not in printlist]
    
    #get cases and deaths from jhu
    cases = ["{:.0f}".format(x/10000) for x in list(jhu_data[time.strftime('%Y%m%d', time.localtime())])]
    
    #get vaccine country list
    vacclist = [trans(x,trans_jhu,trans_bbg) for x in printlist]
    
    if vacc_flag:
        vaccnumber = list()
        boostnumber = list()
        for country in vacclist:
            if (vacc.get(country) == None) or (vacc.get(country)[0] == None):
                vaccnumber.append('NA')
            else:
                vaccnumber.append("{:.1f}".format(vacc.get(country)[0]*100))
            if (vacc.get(country) == None) or (vacc.get(country)[1] == None):
                boostnumber.append('NA')
            else:
                boostnumber.append("{:.1f}".format(vacc.get(country)[1]*100))
    else:
        vaccnumber = ['NA' for country in vacclist]
        boostnumber = ['NA' for country in vacclist]
        print('cannot get bbg vaccine number')
    
    printlist = [trans(x,trans_en,trans_cn) for x in printlist]
    extralist = [trans(x,trans_en,trans_cn) for x in extralist]
    
    words_time = '据约翰霍普金斯大学和彭博统计，截至美东时间%s月%s日下午%s时，' % (f'{int(date[5:7]):.0f}',f'{int(date[8:10]):.0f}',f"{int(date[11:13])-11:.0f}")
    words_country = ''
    words_newcases = '分别新增确诊'
    words_cases = '，累计确诊'
    words_vacc = '，疫苗接种完毕比率为'
    words_boost = '，疫苗加强针接种比率为'
    
    for i in range(len(printlist)):
        words_country += printlist[i] + '、'
        words_newcases += newcases[i] + '万例、'
        words_cases += cases[i] + '万例、'
        words_vacc += vaccnumber[i] + '%、'
        try:
            words_boost += boostnumber[i] + '%、'
        except:
            pass
    
    sentence = words_time + words_country[:-1] +  words_newcases[:-1] + words_cases[:-1] + words_vacc[:-1] + '。此外，' + '、'.join(extralist) + '累计确诊超过1000万例。' + '目前全球累计确诊%s亿例，累计死亡%s万例。' % (f"{covid.get_total_confirmed_cases()/100000000:.2f}", f"{covid.get_total_deaths()/10000:.0f}")
    
    sentence_boost = words_time + words_country[:-1] +  words_newcases[:-1] + words_cases[:-1] + words_boost[:-1] + '。此外，' + '、'.join(extralist) + '累计确诊超过1000万例。' + '目前全球累计确诊%s亿例，累计死亡%s万例。' % (f"{covid.get_total_confirmed_cases()/100000000:.2f}", f"{covid.get_total_deaths()/10000:.0f}")
    
    print(sentence)
    print(sentence_boost)


path = "./results"
if not os.path.exists(path):
    os.mkdir(path)
if len(os.listdir(path)) > 3:
    for file in os.listdir(path):
        if not file == "old":
            shutil.move(path + "/" + file, path + "/old")
with open("./results/" + time.strftime('%Y%m%d%H%M', time.localtime()) +".md", "w") as f_out:
    f_out.write(sentence)
