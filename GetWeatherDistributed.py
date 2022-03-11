# -*- coding:UTF-8 -*-
from glob import glob
from os import makedirs
import re
from threading import currentThread
from bs4 import BeautifulSoup
import datetime
import time
import random
import datetime
import json
import threading

from myscripts import spiderutils as MSU
from myscripts import mydateutils

successCities = []

def loadSuccessCity(sucCityPath):
    global successCities
    with open(sucCityPath, 'r', encoding='utf-8') as f1:
        successCities = f1.readlines()
    for i in range(len(successCities)):
        successCities[i] = successCities[i].replace('\n', '')


def getSuccessCities():
    global successCities
    return successCities


def get_min_valid_year(city_name_pinyin=None, base_url=None) -> str:
    return str(2011)


'''
    返回值是list，每个元素只精确到年月，以200011表示2000年11月
    包含起止月，即若起止日期分别为：202001、202003，则返回的日期list包含202001、202002、202003
'''


def generate_date_list(date_range_min: str, date_range_max: str) -> list:
    ret = []
    # 只需要精确到月，需要以   202110   的格式表示为2021年10月
    date_min_year_int = int(date_range_min[0:4])
    min_valid_year_str = get_min_valid_year()
    assert date_min_year_int >= int(min_valid_year_str), '年份必须大于等于' + str(min_valid_year_str) + ' 错误年份：' + str(
        date_min_year_int)
    date_min_month_int = int(date_range_min[4:])
    date_max_year_int = int(date_range_max[0:4])
    date_max_month_int = int(date_range_max[4:])

    # range是前闭后开的

    for year in range(date_min_year_int, date_max_year_int + 1):
        if year == date_min_year_int:
            # 是第一年
            for month in range(date_min_month_int, min(mydateutils.MONTH_COUNT_IN_A_YAER, date_max_month_int) + 1):
                if month < 10:
                    ret.append('' + str(year) + '0' + str(month))
                else:
                    ret.append('' + str(year) + str(month))
        elif year == date_max_year_int:
            # 是最后一年
            for month in range(1, date_max_month_int + 1):
                if month < 10:
                    ret.append('' + str(year) + '0' + str(month))
                else:
                    ret.append('' + str(year) + str(month))
        else:
            # 不是第一年，也不是最后一年
            for month in range(1, mydateutils.MONTH_COUNT_IN_A_YAER + 1):
                if month < 10:
                    ret.append('' + str(year) + '0' + str(month))
                else:
                    ret.append('' + str(year) + str(month))
    del date_min_month_int
    del date_max_month_int
    del date_min_year_int
    del date_max_year_int
    print('生成的日期列表：')
    print(str(ret))
    return ret


def generate_url_list(base_url, city_name_pinyin, date_range_min: str, date_range_max: str) -> list:
    ret = []
    date_list = generate_date_list(date_range_min, date_range_max)
    # url例子：
    # https://lishi.tianqi.com/zhengzhou/202109.html
    url_suffix = '.html'
    for date in date_list:
        ret.append(base_url + city_name_pinyin + '/' + date + url_suffix)
    return ret


def parseWeatherInfoFromTag(tag) -> dict:
    ret = {}
    # <li class="hide" >
    # 日期
    # 最高气温
    # 最低气温
    # 天气
    # 风向
    #     <div class="th200">2021-09-25 星期六 </div>
    #     <div class="th140">20℃</div>
    #     <div class="th140">18℃</div>
    #     <div class="th140">多云</div>
    #     <div class="th140">东北风 2级</div>
    #     <!-- <div class="th150"></div> -->
    # </li>
    divTagList = tag.select('div')
    ret['wdate'] = divTagList[0].text
    ret['max_temperature'] = divTagList[1].text
    ret['min_temperature'] = divTagList[2].text
    ret['weather_type'] = divTagList[3].text
    ret['wind_direction'] = divTagList[4].text
    del divTagList
    return ret


def crawl_thread(base_url, headers, city_name_obj, date_range_min, date_range_max, is_finished):
    # 要请求的地址
    # 生成所有的请求地址
    url_list = []
    city_name_pinyin = city_name_obj['cpinyin']
    url_list = generate_url_list(base_url, city_name_pinyin, date_range_min, date_range_max)
    # 保存相关
    url_list_len = len(url_list)
    for i in range(url_list_len):
        if random.randint(1, 30) % 2 == 1:
            time.sleep(7)
        try:
            site_url = url_list[i]
            # print('当前爬取网址' + site_url)
            response = MSU.getResponseWithHeaders(site_url, headers)
            htmlText = MSU.getHtmlFromResponse(response)
            print(htmlText)
            soup = BeautifulSoup(htmlText, 'html.parser')
            thruiTagList = soup.select('.thrui')
            # print(len(thruiTagList))
            if len(thruiTagList) == 0:
                print('网站未收录'+str(site_url[
                  site_url.index(city_name_pinyin) + len(city_name_pinyin) + 1:site_url.index('.html')]) +'的天气信息')
                continue
            thruiTag = thruiTagList[0]
            liTagList = thruiTag.select('li')
            li_tag_list_len = len(liTagList)
            if li_tag_list_len == 0:
                print('网站未收录'+str(site_url[
                  site_url.index(city_name_pinyin) + len(city_name_pinyin) + 1:site_url.index('.html')]) +'的天气信息')
                continue
            print('找到'+site_url[
                  site_url.index(city_name_pinyin) + len(city_name_pinyin) + 1:site_url.index('.html')] + '中' + str(
                li_tag_list_len) + '天的天气信息')
            for j in range(li_tag_list_len):
                liTag = liTagList[j]
                weather_info_dict = parseWeatherInfoFromTag(liTag)
                temps = str(weather_info_dict).replace("'", '"')
                obj_ = {}
                for key in list(weather_info_dict.keys()):
                    obj_[key] = weather_info_dict[key]
                for key in list(city_name_obj.keys()):
                    obj_[key] = city_name_obj[key]
                if is_finished == True and j == li_tag_list_len-1 and i == url_list_len-1:
                    obj_['flag'] = 1
                else:
                    obj_['flag'] = 0
                # print('发送到服务器的内容：\n' + str(obj_))
                url_ = getUrl('submit', getIsServer())
                submitTask(url_, obj_)

        except:
            print('出现异常')


def makeDirectory(logPath):
    import os
    print('>> 检查 ' + logPath + ' 目录是否存在')
    if False == os.path.exists(logPath):
        print('>> 目录 ' + logPath + ' 不存在,即将创建')
        os.mkdir(logPath)
        print('>> 创建完毕')
    else:
        print('>> 目录已存在')
    print('>> 检查完毕')
    print()


# 使用Server读取城市数据的代码：
def getAllCityWeatherFromServer():
    # 请求相关
    base_url = 'https://lishi.tianqi.com/'
    headers = getHeaders()

    while True:
        # 城市相关
        cityJson = getCity()
        if cityJson == 'over':
            break
            # ！！！注意，randint...是前闭后闭，range是前闭后开
        cityObj = cityJson
        print('当前城市：' + cityObj['cname'])
        time.sleep(1 + random.randint(1, 3))
        city_name_pinyin = cityObj['cpinyin']
        cityNameObj = {}
        cityNameObj['cpinyin'] = city_name_pinyin
        cityNameObj['cname'] = cityObj['cname']
        # 200101 - 202001
        # date_range_list = [['201101', '201612'], ['201701', '202110']]
        date_range_list = [['201101', '202110']]
        is_finished = False
        date_range_list_len = len(date_range_list)
        for i in range(date_range_list_len):
            date_range_min = date_range_list[i][0]
            date_range_max = date_range_list[i][1]
            if i == date_range_list_len - 1:
                is_finished = True
            crawl_thread(base_url
                         , headers
                         , cityNameObj
                         , date_range_min
                         , date_range_max
                         , is_finished)
            print(cityObj['cname'] + ' 已完成\n')


def main():
    # getOneCityWeather()
    # getAllCityWeather()
    getAllCityWeatherFromServer()


def getHeaders():
    headers = {
        'Cookie': '换成自己从浏览器中复制来的cookie值'
        , 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.71 Safari/537.36 Edg/94.0.992.38'
        , 'Referer': 'https://lishi.tianqi.com/zhengzhou/201109.html'
        , 'sec-ch-ua-platform': '"Windows"'
        , 'Sec-Fetch-Dest': 'document'
        , 'Host': 'lishi.tianqi.com'
    }
    return headers


def getCity():
    cityNameList = []
    headers = getHeaders()
    response = MSU.getResponseWithHeaders(
        # '47.111.160.76:'
        getUrl('fetch', getIsServer()),
        {}
    )
    text = MSU.getHtmlFromResponse(response)
    # print('此次要爬取的城市是：' + text)
    cityObj = json.loads(text)
    # [
    #     {
    #         'name':'大连',
    #         'pinyin':'dalian'
    #     },{
    #         'name':'沈阳',
    #         'pinyin':'shenyang'
    #     }
    # ]
    return cityObj


def parseDictToUrl(url, dictObj):
    url += '?'
    keys = list(dictObj.keys())
    # print(keys)
    len_ = len(dictObj)
    for i in range(len_):
        url += keys[i] + '=' + str(dictObj[keys[i]])
        if i != len_ - 1:
            url += '&'
    # print(url)
    return url


def getUrl(url_type: str, is_server: bool):
    ret = None

    if is_server == True:
        ret = 'http://47.111.160.76:8080/'
    else:
        ret = 'http://localhost:8080/'
    if url_type == 'submit':
        ret = ret + 'submit';
    elif url_type == 'fetch':
        ret = ret + 'fetch'

    return ret


# 记得taskResultDict一定要是字典类型
def submitTask(rootUrl, taskResultDict: dict):
    url = parseDictToUrl(rootUrl, taskResultDict)
    # print('请求地址：')
    # print(url)
    rs = MSU.getResponseWithHeaders(url, {})
    # print(MSU.getHtmlFromResponse(rs))


def test():
    # # # 城市相关
    # # getCity()
    # submitTask(getUrl('submit', False),
    #            {'wdate': '2011-06-01  ', 'max_temperature': '21℃', 'min_temperature': '13℃', 'weather_type': '阵雨~多云',
    #             'wind_direction': '北风~东南风 3-4级~微风', 'cpinyin': 'daqing', 'cname': '大庆', 'flag': 0})
    pass


def getIsServer():
    # ret = False
    ret = True
    return ret


main()
# test()
