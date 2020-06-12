import datetime
import os
import time
import traceback

import json
import requests
from api import GetInfo, Login
from django.http import HttpResponse, JsonResponse
from info.models import Students

with open('config.json', mode='r', encoding='utf-8') as f:
    config = json.loads(f.read())
base_url = config["base_url"]


def index(request):
    return HttpResponse('info_index here')


def cacheData(xh, filename):
    docurl = 'data/' + str(xh)[0:2] + '/' + str(xh) + '/'
    fileurl = docurl + str(filename) + '.json'
    if not os.path.exists(docurl):
        os.makedirs(docurl)
    else:
        if not os.path.exists(fileurl):
            return
        else:
            with open(fileurl, mode='r', encoding='utf-8') as o:
                result = json.loads(o.read())
                return result


def newData(xh, filename, content):
    docurl = 'data/' + str(xh)[0:2] + '/' + str(xh) + '/'
    fileurl = docurl + str(filename) + '.json'
    if not os.path.exists(docurl):
        os.makedirs(docurl)
        with open(fileurl, mode='w', encoding='utf-8') as n:
            n.write(content)
    else:
        with open(fileurl, mode='w', encoding='utf-8') as n:
            n.write(content)
    # if not os.path.exists(fileurl):
    #     with open(fileurl, mode='w', encoding='utf-8') as n:
    #         n.write(content)


def writeLog(content):
    date = datetime.datetime.now().strftime('%Y-%m-%d')
    filename = 'mylogs/' + date + '.log'
    if not os.path.exists(filename):
        with open(filename, mode='w', encoding='utf-8') as n:
            n.write('【%s】的日志记录' % date)
    with open(filename, mode='a', encoding='utf-8') as l:
        l.write('\n%s' % content)


def update_cookies(xh, pswd):
    try:
        stu = Students.objects.get(studentId=int(xh))
        startTime = time.time()
        content = ('【%s】[%s]更新cookies' % (datetime.datetime.now().strftime('%H:%M:%S'), stu.name))
        writeLog(content)
        # print('原cookies：')
        # print('{JSESSIONID:%s,route:%s}' % (stu.JSESSIONID,stu.route))
        lgn = Login(base_url=base_url)
        lgn.login(xh, pswd)
        if lgn.runcode == 1:
            cookies = lgn.cookies
            # person = GetInfo(base_url=base_url, cookies=cookies)
            NJSESSIONID = requests.utils.dict_from_cookiejar(cookies)["JSESSIONID"]
            nroute = requests.utils.dict_from_cookiejar(cookies)["route"]
            updateTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            Students.objects.filter(studentId=int(xh)).update(JSESSIONID=NJSESSIONID, route=nroute,
                                                              updateTime=updateTime)
            endTime = time.time()
            spendTime = endTime - startTime
            # print('新cookies:')
            content = ('【%s】更新cookies成功，耗时%.2fs' % (datetime.datetime.now().strftime('%H:%M:%S'), spendTime))
            writeLog(content)
            person = GetInfo(base_url=base_url, cookies=cookies)
            pinfo = person.get_pinfo()
            # print(pinfo)
            filename = ('Pinfo')
            newData(xh, filename, json.dumps(pinfo, ensure_ascii=False))
            # print(requests.utils.dict_from_cookiejar(cookies))
            return cookies
        else:
            content = ('【%s】[%s]更新cookies时网络或其他错误！' % (datetime.datetime.now().strftime('%H:%M:%S'), xh))
            writeLog(content)
            return HttpResponse(json.dumps({'err':'网络或token问题'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
    except Exception as e:
        ServerChan = config["ServerChan"]
        text = "更新cookies未知错误"
        if ServerChan == "none":
            print(str(e))
            return HttpResponse(json.dumps({'err':'更新cookies未知错误'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
        else:
            requests.get(ServerChan + 'text=' + text + '&desp=' + str(e) + '\n' + str(xh) + '\n' + str(pswd))
            return HttpResponse(json.dumps({'err':'更新cookies未知错误'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")


def get_pinfo(request):
    if request.method == 'POST':
        if request.POST:
            xh = request.POST.get("xh")
            pswd = request.POST.get("pswd")
        else:
            return HttpResponse(json.dumps({'err':'请提交正确的post数据'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
        if Students.objects.filter(studentId=int(xh)):
            stu = Students.objects.get(studentId=int(xh))
            refreshTimes = int(stu.refreshTimes)
            try:
                startTime = time.time()
                lgn = Login(base_url=base_url)
                lgn.login(xh, pswd)
                if lgn.runcode == 1:
                    cookies = lgn.cookies
                    person = GetInfo(base_url=base_url, cookies=cookies)
                    pinfo = person.get_pinfo()
                    JSESSIONID = requests.utils.dict_from_cookiejar(cookies)["JSESSIONID"]
                    route = requests.utils.dict_from_cookiejar(cookies)["route"]
                    refreshTimes += 1
                    updateTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    Students.objects.filter(studentId=int(xh)).update(JSESSIONID=JSESSIONID, route=route,
                                                                      refreshTimes=refreshTimes, updateTime=updateTime)
                    endTime = time.time()
                    spendTime = endTime - startTime
                    print('【%s】登录了' % pinfo["name"])
                    content = ('【%s】[%s]第%d次登录了，耗时%.2fs' % (
                        datetime.datetime.now().strftime('%H:%M:%S'), pinfo["name"], refreshTimes, spendTime))
                    writeLog(content)
                    filename = ('Pinfo')
                    newData(xh, filename, json.dumps(pinfo, ensure_ascii=False))
                    return HttpResponse(json.dumps(pinfo, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
                elif lgn.runcode == 2:
                    content = ('【%s】[%s]在登录时学号或者密码错误！' % (datetime.datetime.now().strftime('%H:%M:%S'), xh))
                    writeLog(content)
                    return HttpResponse(json.dumps({'err':'学号或者密码错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
                else:
                    content = ('【%s】[%s]在登录时网络或其它错误！' % (datetime.datetime.now().strftime('%H:%M:%S'), xh))
                    writeLog(content)
                    return HttpResponse(json.dumps({'err':'网络或token问题'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
            except Exception as e:
                print(e)
                content = ('【%s】[%s]登录时出错' % (datetime.datetime.now().strftime('%H:%M:%S'), xh))
                writeLog(content)
                ServerChan = config["ServerChan"]
                text = "登录未知错误"
                if ServerChan == "none":
                    print(str(e))
                    return HttpResponse(json.dumps({'err':'登录未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
                else:
                    requests.get(ServerChan + 'text=' + text + '&desp=' + str(e) + '\n' + str(xh) + '\n' + str(pswd))
                    return HttpResponse(json.dumps({'err':'登录未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
        else:
            try:
                startTime = time.time()
                lgn = Login(base_url=base_url)
                lgn.login(xh, pswd)
                if lgn.runcode == 1:
                    cookies = lgn.cookies
                    person = GetInfo(base_url=base_url, cookies=cookies)
                    pinfo = person.get_pinfo()
                    JSESSIONID = requests.utils.dict_from_cookiejar(cookies)["JSESSIONID"]
                    route = requests.utils.dict_from_cookiejar(cookies)["route"]
                    updateTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    newstu = Students.create(int(pinfo["studentId"]), pinfo["name"], pinfo["collegeName"],
                                             pinfo["majorName"], pinfo["className"], pinfo["phoneNumber"],
                                             pinfo["birthDay"], JSESSIONID, route, updateTime)
                    newstu.save()
                    endTime = time.time()
                    spendTime = endTime - startTime
                    print('【%s】第一次登录' % pinfo["name"])
                    content = ('【%s】[%s]第一次登录，耗时%.2fs' % (
                        datetime.datetime.now().strftime('%H:%M:%S'), pinfo["name"], spendTime))
                    writeLog(content)
                    filename = ('Pinfo')
                    newData(xh, filename, json.dumps(pinfo, ensure_ascii=False))
                    return HttpResponse(json.dumps(pinfo, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
                elif lgn.runcode == 2:
                    content = ('【%s】[%s]在第一次登录时学号或者密码错误！' % (datetime.datetime.now().strftime('%H:%M:%S'), xh))
                    writeLog(content)
                    return HttpResponse(json.dumps({'err':'学号或者密码错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
                else:
                    content = ('【%s】[%s]在第一次登录时网络或其它错误！' % (datetime.datetime.now().strftime('%H:%M:%S'), xh))
                    writeLog(content)
                    return HttpResponse(json.dumps({'err':'网络或token问题'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
            except Exception as e:
                # print(e)
                content = ('【%s】[%s]第一次登录时出错' % (datetime.datetime.now().strftime('%H:%M:%S'), xh))
                writeLog(content)
                ServerChan = config["ServerChan"]
                text = "登录未知错误"
                if ServerChan == "none":
                    print(str(e))
                    return HttpResponse(json.dumps({'err':'登录未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
                else:
                    requests.get(ServerChan + 'text=' + text + '&desp=' + str(e) + '\n' + str(xh) + '\n' + str(pswd))
                    return HttpResponse(json.dumps({'err':'登录未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
    else:
        return HttpResponse(json.dumps({'err':'请使用post并提交正确数据'}, ensure_ascii=False),
                            content_type="application/json,charset=utf-8")


def get_message(request):
    if request.method == 'POST':
        if request.POST:
            xh = request.POST.get("xh")
            pswd = request.POST.get("pswd")
        else:
            return HttpResponse(json.dumps({'err':'请提交正确的post数据'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
        if not Students.objects.filter(studentId=int(xh)):
            content = ('【%s】[%s]未登录访问消息' % (datetime.datetime.now().strftime('%H:%M:%S'), xh))
            writeLog(content)
            return HttpResponse(json.dumps({'err':'还未登录'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
        else:
            stu = Students.objects.get(studentId=int(xh))
        try:
            startTime = time.time()
            print('【%s】查看了消息' % stu.name)
            JSESSIONID = str(stu.JSESSIONID)
            route = str(stu.route)
            cookies_dict = {
                'JSESSIONID': JSESSIONID,
                'route': route
            }
            cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            person = GetInfo(base_url=base_url, cookies=cookies)
            message = person.get_message()
            endTime = time.time()
            spendTime = endTime - startTime
            content = ('【%s】[%s]访问了消息，耗时%.2fs' % (datetime.datetime.now().strftime('%H:%M:%S'), stu.name, spendTime))
            writeLog(content)
            return HttpResponse(json.dumps(message, ensure_ascii=False), content_type="application/json,charset=utf-8")
        except Exception as e:
            print(e)
            content = ('【%s】[%s]访问消息出错' % (datetime.datetime.now().strftime('%H:%M:%S'), stu.name))
            writeLog(content)
            if str(e) != 'Expecting value: line 5 column 1 (char 9)':
                ServerChan = config["ServerChan"]
                text = "消息错误"
                if ServerChan == "none":
                    print(str(e))
                    return HttpResponse(json.dumps({'err':'消息未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
                else:
                    requests.get(ServerChan + 'text=' + text + '&desp=' + str(e) + '\n' + str(xh) + '\n' + str(pswd))
                    return HttpResponse(json.dumps({'err':'消息未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
            sta = update_cookies(xh, pswd)
            person = GetInfo(base_url=base_url, cookies=sta)
            message = person.get_message()
            return HttpResponse(json.dumps(message, ensure_ascii=False), content_type="application/json,charset=utf-8")
    else:
        return HttpResponse(json.dumps({'err':'请使用post并提交正确数据'}, ensure_ascii=False),
                            content_type="application/json,charset=utf-8")


def get_study(request):
    if request.method == 'POST':
        if request.POST:
            xh = request.POST.get("xh")
            pswd = request.POST.get("pswd")
            refresh = request.POST.get("refresh")
        else:
            return HttpResponse(json.dumps({'err':'请提交正确的post数据'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
        if not Students.objects.filter(studentId=int(xh)):
            content = ('【%s】[%s]未登录访问学业情况' % (datetime.datetime.now().strftime('%H:%M:%S'), xh))
            writeLog(content)
            return HttpResponse(json.dumps({'err':'还未登录'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
        else:
            stu = Students.objects.get(studentId=int(xh))
        if refresh == "no":
            filename = ('Study')
            cache = cacheData(xh, filename)
            if cache is not None:
                # print('cache')
                print('【%s】查看了学业缓存' % stu.name)
                return HttpResponse(json.dumps(cache, ensure_ascii=False),
                                    content_type="application/json,charset=utf-8")
            else:
                pass
        try:
            startTime = time.time()
            print('【%s】查看了学业情况' % stu.name)
            JSESSIONID = str(stu.JSESSIONID)
            route = str(stu.route)
            cookies_dict = {
                'JSESSIONID': JSESSIONID,
                'route': route
            }
            cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            person = GetInfo(base_url=base_url, cookies=cookies)
            study = person.get_study(xh)
            if study.get("err") == 'Connect Timeout':
                sta = update_cookies(xh, pswd)
                person = GetInfo(base_url=base_url, cookies=sta)
                study = person.get_study(xh)
                gpa = str(study["gpa"])
                Students.objects.filter(studentId=int(xh)).update(gpa=gpa)
                filename = ('Study')
                newData(xh, filename, json.dumps(study, ensure_ascii=False))
                return HttpResponse(json.dumps(study, ensure_ascii=False),
                                    content_type="application/json,charset=utf-8")
            endTime = time.time()
            spendTime = endTime - startTime
            content = ('【%s】[%s]访问了学业情况，耗时%.2fs' % (datetime.datetime.now().strftime('%H:%M:%S'), stu.name, spendTime))
            writeLog(content)
            gpa = str(study["gpa"])
            Students.objects.filter(studentId=int(xh)).update(gpa=gpa)
            filename = ('Study')
            newData(xh, filename, json.dumps(study, ensure_ascii=False))
            return HttpResponse(json.dumps(study, ensure_ascii=False), content_type="application/json,charset=utf-8")
        except Exception as e:
            print(e)
            content = ('【%s】[%s]访问学业情况出错' % (datetime.datetime.now().strftime('%H:%M:%S'), stu.name))
            writeLog(content)
            if str(e) != 'list index out of range':
                ServerChan = config["ServerChan"]
                text = "学业错误"
                if ServerChan == "none":
                    print(str(e))
                    return HttpResponse(json.dumps({'err':'学业未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
                else:
                    requests.get(ServerChan + 'text=' + text + '&desp=' + str(e) + '\n' + str(xh) + '\n' + str(pswd))
                    return HttpResponse(json.dumps({'err':'学业未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
            sta = update_cookies(xh, pswd)
            person = GetInfo(base_url=base_url, cookies=sta)
            study = person.get_study(xh)
            gpa = str(study["gpa"])
            Students.objects.filter(studentId=int(xh)).update(gpa=gpa)
            filename = ('Study')
            newData(xh, filename, json.dumps(study, ensure_ascii=False))
            return HttpResponse(json.dumps(study, ensure_ascii=False), content_type="application/json,charset=utf-8")
    else:
        return HttpResponse(json.dumps({'err':'请使用post并提交正确数据'}, ensure_ascii=False),
                            content_type="application/json,charset=utf-8")


def get_grade(request):
    if request.method == 'POST':
        if request.POST:
            xh = request.POST.get("xh")
            pswd = request.POST.get("pswd")
            year = request.POST.get("year")
            term = request.POST.get("term")
            refresh = request.POST.get("refresh")
        else:
            return HttpResponse(json.dumps({'err':'请提交正确的post数据'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
        if not Students.objects.filter(studentId=int(xh)):
            content = ('【%s】[%s]未登录访问成绩' % (datetime.datetime.now().strftime('%H:%M:%S'), xh))
            writeLog(content)
            return HttpResponse(json.dumps({'err':'还未登录'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
        else:
            stu = Students.objects.get(studentId=int(xh))
        if refresh == "no":
            filename = ('Grades-%s%s' % (str(year), str(term)))
            cache = cacheData(xh, filename)
            if cache is not None:
                # print('cache')
                print('【%s】查看了%s-%s的成绩缓存' % (stu.name, year, term))
                return HttpResponse(json.dumps(cache, ensure_ascii=False),
                                    content_type="application/json,charset=utf-8")
            else:
                pass
        try:
            startTime = time.time()
            print('【%s】查看了%s-%s的成绩' % (stu.name, year, term))
            JSESSIONID = str(stu.JSESSIONID)
            route = str(stu.route)
            cookies_dict = {
                'JSESSIONID': JSESSIONID,
                'route': route
            }
            cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            person = GetInfo(base_url=base_url, cookies=cookies)
            grade = person.get_grade(year, term)
            endTime = time.time()
            spendTime = endTime - startTime
            content = ('【%s】[%s]访问了%s-%s的成绩，耗时%.2fs' % (
                datetime.datetime.now().strftime('%H:%M:%S'), stu.name, year, term, spendTime))
            writeLog(content)
            
            filename = ('Grades-%s%s' % (str(year), str(term)))
            newData(xh, filename, json.dumps(grade, ensure_ascii=False))
            # print('write')

            return HttpResponse(json.dumps(grade, ensure_ascii=False), content_type="application/json,charset=utf-8")
        except Exception as e:
            # print(e)
            content = ('【%s】[%s]访问成绩出错' % (datetime.datetime.now().strftime('%H:%M:%S'), stu.name))
            writeLog(content)
            if str(e) != 'Expecting value: line 4 column 1 (char 6)':
                ServerChan = config["ServerChan"]
                text = "成绩错误"
                if ServerChan == "none":
                    print(str(e))
                    return HttpResponse(json.dumps({'err':'成绩未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
                else:
                    requests.get(ServerChan + 'text=' + text + '&desp=' + str(e) + '\n' + str(xh) + '\n' + str(pswd))
                    return HttpResponse(json.dumps({'err':'成绩未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
            sta = update_cookies(xh, pswd)
            person = GetInfo(base_url=base_url, cookies=sta)
            grade = person.get_grade(year, term)

            filename = ('Grades-%s%s' % (str(year), str(term)))
            newData(xh, filename, json.dumps(grade, ensure_ascii=False))

            return HttpResponse(json.dumps(grade, ensure_ascii=False), content_type="application/json,charset=utf-8")
    else:
        return HttpResponse(json.dumps({'err':'请使用post并提交正确数据'}, ensure_ascii=False),
                            content_type="application/json,charset=utf-8")


def get_schedule(request):
    if request.method == 'POST':
        if request.POST:
            xh = request.POST.get("xh")
            pswd = request.POST.get("pswd")
            year = request.POST.get("year")
            term = request.POST.get("term")
            refresh = request.POST.get("refresh")
        else:
            return HttpResponse(json.dumps({'err':'请提交正确的post数据'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
        if not Students.objects.filter(studentId=int(xh)):
            content = ('【%s】[%s]未登录访问课程' % (datetime.datetime.now().strftime('%H:%M:%S'), xh))
            writeLog(content)
            return HttpResponse(json.dumps({'err':'还未登录'}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
        else:
            stu = Students.objects.get(studentId=int(xh))
        if refresh == "no":
            filename = ('Schedules-%s%s' % (str(year), str(term)))
            cache = cacheData(xh, filename)
            if cache is not None:
                # print('cache')
                print('【%s】查看了%s-%s的课表缓存' % (stu.name, year, term))
                return HttpResponse(json.dumps(cache, ensure_ascii=False),
                                    content_type="application/json,charset=utf-8")
            else:
                pass
        try:
            startTime = time.time()
            print('【%s】查看了%s-%s的课程' % (stu.name, year, term))
            JSESSIONID = str(stu.JSESSIONID)
            route = str(stu.route)
            cookies_dict = {
                'JSESSIONID': JSESSIONID,
                'route': route
            }
            cookies = requests.utils.cookiejar_from_dict(cookies_dict)
            person = GetInfo(base_url=base_url, cookies=cookies)
            schedule = person.get_schedule(year, term)
            endTime = time.time()
            spendTime = endTime - startTime
            content = ('【%s】[%s]访问了%s-%s的课程，耗时%.2fs' % (
                datetime.datetime.now().strftime('%H:%M:%S'), stu.name, year, term, spendTime))
            writeLog(content)

            filename = ('Schedules-%s%s' % (str(year), str(term)))
            newData(xh, filename, json.dumps(schedule, ensure_ascii=False))
            # print('write')

            return HttpResponse(json.dumps(schedule, ensure_ascii=False), content_type="application/json,charset=utf-8")
        except Exception as e:
            print(e)
            traceback.print_exc()
            content = ('【%s】[%s]访问课程出错' % (datetime.datetime.now().strftime('%H:%M:%S'), stu.name))
            writeLog(content)
            if str(e) != 'Expecting value: line 4 column 1 (char 6)':
                ServerChan = config["ServerChan"]
                text = "课程错误"
                if ServerChan == "none":
                    print(str(e))
                    return HttpResponse(json.dumps({'err':'课程未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
                else:
                    requests.get(ServerChan + 'text=' + text + '&desp=' + str(e) + '\n' + str(xh) + '\n' + str(pswd))
                    return HttpResponse(json.dumps({'err':'课程未知错误'}, ensure_ascii=False),
                                        content_type="application/json,charset=utf-8")
            sta = update_cookies(xh, pswd)
            person = GetInfo(base_url=base_url, cookies=sta)
            schedule = person.get_schedule(year, term)
            
            filename = ('Schedules-%s%s' % (str(year), str(term)))
            newData(xh, filename, json.dumps(schedule, ensure_ascii=False))

            return HttpResponse(json.dumps(schedule, ensure_ascii=False), content_type="application/json,charset=utf-8")
    else:
        return HttpResponse(json.dumps({'err':'请使用post并提交正确数据'}, ensure_ascii=False),
                            content_type="application/json,charset=utf-8")

def joinDetail(request):
    type = request.GET.get("type")
    allUsers = Students.objects.filter().all().count()
    if type == 'college':
        detail = [{
            'collegeName': i["collegeName"],
            'collegeNum': Students.objects.filter(collegeName=i["collegeName"]).count()
        } for i in Students.objects.values('collegeName').distinct().order_by('collegeName')]
        ndetail = sorted(detail,key=lambda keys:keys['collegeNum'], reverse=True)
        res = {
            'allUsers': allUsers,
            'collegeNum': int(Students.objects.values('collegeName').distinct().order_by('collegeName').count()),
            'detail': ndetail
        }
    elif type == 'major':
        detail = [{
            'majorName': i["majorName"],
            'majorNum': Students.objects.filter(majorName=i["majorName"]).count()
        } for i in Students.objects.values('majorName').distinct().order_by('majorName')]
        ndetail = sorted(detail,key=lambda keys:keys['majorNum'], reverse=True)
        res = {
            'allUsers': allUsers,
            'majorNum': int(Students.objects.values('majorName').distinct().order_by('majorName').count()),
            'detail': ndetail
        }
    elif type == 'class':
        detail = [{
            'className': i["className"],
            'classNum': Students.objects.filter(className=i["className"]).count()
        } for i in Students.objects.values('className').distinct().order_by('className')]
        ndetail = sorted(detail,key=lambda keys:keys['classNum'], reverse=True)
        res = {
            'allUsers': allUsers,
            'classNum': int(Students.objects.values('className').distinct().order_by('className').count()),
            'detail': ndetail
        }
    return HttpResponse(json.dumps(res, ensure_ascii=False),
                        content_type="application/json,charset=utf-8")

def get_position(request):
    #print(request)
    xh = request.GET.get("xh")
    if xh is None:
        return HttpResponse(json.dumps({'err':'参数不全'}, ensure_ascii=False),
                            content_type="application/json,charset=utf-8")
    if not Students.objects.filter(studentId=int(xh)):
        return HttpResponse(json.dumps({'err':'还未登录'}, ensure_ascii=False),
                            content_type="application/json,charset=utf-8")
    else:
        stu = Students.objects.get(studentId=int(xh))
        majorName = stu.majorName
        className = stu.className
        if stu.gpa == "init":
            gpa = "init"
            return HttpResponse(json.dumps({'gpa': gpa,'majorCount':0,'classCount':0}, ensure_ascii=False),
                                content_type="application/json,charset=utf-8")
        else:
            gpa = float(stu.gpa)
        majorCount = 1
        classCount = 1
        for m in Students.objects.filter(majorName=majorName).all().order_by('-gpa'):
            if m.gpa == "init" or str(m.studentId)[0:2] != xh[0:2]:
                pass
            elif gpa >= float(m.gpa):
                break
            else:
                majorCount += 1
        for c in Students.objects.filter(className=className).all().order_by('-gpa'):
            if m.gpa == "init":
                pass
            elif gpa >= float(m.gpa):
                break
            else:
                classCount += 1
        return HttpResponse(json.dumps({'gpa': gpa,'majorCount':majorCount,'classCount':classCount}, ensure_ascii=False),
                            content_type="application/json,charset=utf-8")

