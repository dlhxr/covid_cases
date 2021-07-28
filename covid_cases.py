#!/usr/bin/env python
# coding: utf-8

#取worldo新增病例数除美国前5的国家，并在jhu找到对应的累计病例，再同时汇报未提及的国家但累计确诊很高的。
#需先安装第三方covid包，本地可使用pip install covid命令

#print('为避免格式错误，请优先使用程序生成的语句，若程序出错请手工填写。')

from covid import Covid
import time
import json
import requests
from bs4 import BeautifulSoup
from selenium import webdriver

#keep country name in the same format
trans_jhu = ['US','United Kingdom','United Arab Emirates']
trans_worldo = ['USA','UK','UAE']
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
'''
#get vaccine numbers from BBG

browser = webdriver.Firefox()
browser.get('https://www.bloomberg.com/graphics/covid-vaccine-tracker-global-distribution/?terminal=true')

#click twice to load all countries
browser.find_elements_by_xpath('/html/body/div[5]/section[4]/div/figure[6]/div[2]/div[2]/button')[0].click()
browser.find_elements_by_xpath('/html/body/div[5]/section[4]/div/figure[6]/div[2]/div[2]/button')[0].click()

sourcePage = browser.page_source

soup = BeautifulSoup(sourcePage,"html.parser")

tbodies = soup.select('table tbody tr')

vacc = {}
for index,tbody in enumerate(tbodies):
    for i, td in enumerate(tbody.children):
        if i == 0:
            name = td.text
            numbers = []
        else:
            try:
                numbers.append(td.text)
            except:
                pass
    vacc[name] = numbers
'''
#get covid cases from Jhu
covid = Covid()
jhu = sorted(covid.get_data(), key = lambda i:i['confirmed'], reverse=True)

#get new cases from worldo
covidw = Covid(source="worldometers")
worldo = covidw.get_data()

#start building sentence

date = time.strftime("%Y/%m/%d %H:%M",time.localtime(jhu[1]['last_update'] // 1000 - 4 * 3600))
#date = time.strftime("%Y/%m/%d %H:%M",time.localtime(jhu[1]['last_update'] // 1000))

worldo_US = [x for x in worldo if x['country'] == 'USA'][0]
worldo = list(filter(lambda i:i['country'] not in ['World','North America','Asia','South America','Europe','Africa','Oceania', 'USA'], worldo))

worldo = sorted(worldo, key = lambda i:i['new_cases'], reverse=True)
worldolist = worldo[0:4]

printlist = [x['country'] for x in worldolist]

#add UK if it's not Top 4 since it reflects EU covid status
if 'UK' not in printlist:
    worldo_UK = [x for x in worldo if x['country'] == 'UK'][0]
    worldolist.append(worldo_UK)

worldolist.insert(0, worldo_US)

printlist = [x['country'] for x in worldolist]
printlist = [trans(x,trans_worldo,trans_jhu) for x in printlist]

newcases = ["{:.1f}".format(x['new_cases']/10000) for x in worldolist]

countrylist = [x for x in jhu if x['confirmed']>3000000]
countrylist = [x['country'] for x in countrylist]

extralist = [x for x in countrylist if x not in printlist]

#get cases and deaths from jhu
cases = list()
deaths = list()

for country in printlist:
    selected = [k for k in jhu if k['country'] == country]
    if selected != []:
        cases.append("{:.0f}".format(selected[0]['confirmed']/10000))
        deaths.append("{:.0f}".format(selected[0]['deaths']/10000))
    else:
        cases.append('NA')
        deaths.append('NA')
'''
#get vaccine number from bbg
vacclist = [trans(x,trans_jhu,trans_bbg) for x in printlist]

vaccnumber = list()
for country in vacclist:
    if vacc.get(country) == None:
        vaccnumber.append('NA')
    else:
        vaccnumber.append(vacc.get(country)[3])
'''

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
    #words_vacc += vaccnumber[i] + '%、'

sentence = words_time + words_country[:-1] +  words_newcases[:-1] + words_cases[:-1] + words_vacc[:-1] + '。此外，' + '、'.join(extralist) + '累计确诊超过300万例。' + '目前全球累计确诊%s亿例，累计死亡%s万例。' % (f"{covid.get_total_confirmed_cases()/100000000:.2f}", f"{covid.get_total_deaths()/10000:.0f}")

print(sentence)

import os
path = "./results"
if not os.path.exists(path):
    os.mkdir(path)
with open("./results/test.txt", "w") as f_out:
    f_out.write(sentence)

#print('请在生成数据后到对应网页再次人工核对数据准确性，尤其是美国数据，美国新增请使用worldo或者更合理的结果。')
#print('新增数据来源:https://www.worldometers.info/coronavirus/')
#print('累计确诊数据来源：https://coronavirus.jhu.edu/map.html')
#print('疫苗数据采用fully vaccinated栏，来源：https://www.bloomberg.com/graphics/covid-vaccine-tracker-global-distribution/?terminal=true')
