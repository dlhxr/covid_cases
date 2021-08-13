#!/usr/bin/env python
# coding: utf-8

from covid import Covid
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
import pandas as pd
import requests
import json

os.environ['TZ'] = 'US/Eastern'
if os.name != 'nt':
    time.tzset()

#keep country name in the same format
trans_jhu = ['US','United Kingdom','United Arab Emirates']
trans_bbg = ['U.S.','U.K.','UAE']

#dictionary to translate country names
trans_en = ['US','United Kingdom','India','Brazil','Russia','Colombia','Peru','Mexico','Spain','Argentina','South Africa','France','Chile','Iran','Bangladesh','Iraq','Saudi Arabia','Turkey','Pakistan','Italy','Philippines','Germany','Portugal','Indonesia','Czechia','Poland','Ukraine','Malaysia','United Arab Emirates']
trans_cn = ['美国','英国','印度','巴西','俄罗斯','哥伦比亚','秘鲁','墨西哥','西班牙','阿根廷','南非','法国','智利','伊朗','孟加拉','伊拉克','沙特','土耳其','巴基斯坦','意大利','菲律宾','德国','葡萄牙','印尼','捷克','波兰','乌克兰','马来西亚','阿联酋']

def trans(x, orig, final):
    if len(orig) != len(final):
        print('Check length of the translation map!')
        return 0
    for i in range(len(orig)):
        x = x.replace(orig[i],final[i])
    return x

#get vaccine numbers from BBG

url = 'https://www.bloomberg.com/graphics/covid-vaccine-tracker-global-distribution/'
header={
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36',
        'authority': 'www.bloomberg.com',
        'cache-control': 'max-age=0',
        'sec-ch-ua': '"Google Chrome";v="87", " Not;A Brand";v="99", "Chromium";v="87"',
        'sec-ch-ua-mobile': '?0',
        'upgrade-insecure-requests': '1',
        'sec-fetch-site': 'none',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-user': '?1',
        'sec-fetch-dest': 'document'
    }

rep = requests.get(url,headers = header)
rep = BeautifulSoup(rep.text, 'html.parser').find("script", {"id": "dvz-data-cave"})
vacc = json.loads(rep.next)
vacc = [[d['name'], d.get('noCompletedVaccinationPerCapita',None)] for d in vacc['vaccination']['global']]
vacc=dict(vacc)

#get covid cases from Jhu
covid = Covid()
jhu = sorted(covid.get_data(), key = lambda i:i['confirmed'], reverse=True)


tmp = [[d['id'], d['country'], d['confirmed']] for d in jhu]
tmp=pd.DataFrame(tmp,columns=['id', 'country',time.strftime('%Y%m%d', time.localtime())])
tmp['id'] =pd.to_numeric(tmp['id'])
tmp.sort_values("id",inplace=True)

path = "./data"
if not os.path.exists(path):
    os.mkdir(path)

if os.path.isfile('./data/data.csv'):
    jhu_data = pd.read_csv('./data/data.csv')
    jhu_data.to_csv('./data/data_bak.csv',index=0)
    
    #use the latest result as today's data
    if jhu_data.columns.values[2] == tmp.columns.values[2]:
        jhu_data = jhu_data.drop(jhu_data.columns.values[2], axis=1)
    
    jhu_data = pd.merge(tmp, jhu_data, on=['id','country'])

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

jhu_us = jhu_data.loc[jhu_data['country'] == 'US']
jhu_data = jhu_data.drop(jhu_data.loc[jhu_data['country'] == 'US'].index[0])
jhu_data = jhu_us.append(jhu_data.iloc[0:4,:])

#start building sentence

date = time.strftime("%Y/%m/%d %H:%M",time.localtime(jhu[0]['last_update'] // 1000))

printlist = list(jhu_data['country'])

newcases = ["{:.1f}".format(x/10000) for x in list(jhu_data['new_cases'])]

#above 4 million cases
countrylist = [x for x in jhu if x['confirmed']>4000000]
countrylist = [x['country'] for x in countrylist]

extralist = [x for x in countrylist if x not in printlist]

#get cases and deaths from jhu
cases = ["{:.0f}".format(x/10000) for x in list(jhu_data[time.strftime('%Y%m%d', time.localtime())])]

#get vaccine number from bbg
vacclist = [trans(x,trans_jhu,trans_bbg) for x in printlist]

vaccnumber = list()
for country in vacclist:
    if vacc.get(country) == None:
        vaccnumber.append('NA')
    else:
        vaccnumber.append("{:.1%}".format(vacc.get(country)))

printlist = [trans(x,trans_en,trans_cn) for x in printlist]
extralist = [trans(x,trans_en,trans_cn) for x in extralist]

words_time = '据约翰霍普金斯大学和彭博统计，截至美东时间%s月%s日下午%s时，' % (f'{int(date[5:7]):.0f}',f'{int(date[8:10]):.0f}',f"{int(date[11:13])-11:.0f}")
words_country = ''
words_newcases = '分别新增确诊'
words_cases = '，累计确诊'
words_vacc = '，疫苗接种完毕比率为'

for i in range(len(printlist)):
    words_country += printlist[i] + '、'
    words_newcases += newcases[i] + '万例、'
    words_cases += cases[i] + '万例、'
    words_vacc += vaccnumber[i] + '%、'

sentence = words_time + words_country[:-1] +  words_newcases[:-1] + words_cases[:-1] + words_vacc[:-1] + '。此外，' + '、'.join(extralist) + '累计确诊超过400万例。' + '目前全球累计确诊%s亿例，累计死亡%s万例。' % (f"{covid.get_total_confirmed_cases()/100000000:.2f}", f"{covid.get_total_deaths()/10000:.0f}")

print(sentence)

path = "./results"
if not os.path.exists(path):
    os.mkdir(path)
with open("./results/" + time.strftime('%Y%m%d%H%M', time.localtime()) +".md", "w") as f_out:
    f_out.write(sentence)
