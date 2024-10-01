import json
import hashlib
import os
import re
import time
import asyncio
import aiohttp
import uuid
from rich import print_json
from urllib.parse import urlparse, parse_qs



""" 
目前 PikPak 官方已经禁止给新注册的临时邮箱账号免费会员，但主流邮箱的新旧账号和临时邮箱旧账号仍然可以获取免费会员，具体为：
（1）临时邮箱新账号注册无法获取免费会员，也无法通过做任务和受邀请（填写邀请码）获取免费会员，同时也无法给其他邀请用户免费会员。
（2）临时邮箱旧账号可以通过主流邮箱注册新账号并填写邀请码以获得免费会员
（3）主流邮箱注册新账号可通过做任务和受邀请获取免费会员

PikPak 更新政策：目前完成邀请后无法立刻获取会员，PikPak 需在 24 小时内确认邀请的有效性，确认有效才会给予邀请奖励

经测试，目前邮箱注册时，如果验证注册账号为临时邮箱，那么需要进行 Google 验证；而主流邮箱则不需要

主流邮箱包括：gmail.com、outlook.com 等（只要不进行 Google 验证 即可证明是主流邮箱
提示：目前发现 Proton Mail 邮箱（如：@proton.me）不被 PikPak 认定为主流邮箱 ）


脚本使用：
pip install -r requirements.txt
python main.py
"""

DEBUG_MODE = False  # Debug模式，是否打印请求返回信息
USE_TEMP_EMAIL = False  # 是否使用临时邮箱（临时邮箱自动生成邮箱账号和验证邮箱验证码，非临时邮箱需要手动输入邮箱账号和邮箱验证码进行注册）
INVITE_CODE = os.getenv("INVITE_CODE") or input("请输入邀请码: ")
CUSTOM_PASSWORD = "xtn#123_n666"  # 注册新账号默认密码
# PROXY = input('请输入代理，如不需要直接回车:')  # 代理，如果多次出现IP问题可尝试将自己所用的魔法设置为代理。例如：使用clash则设置为 'http://127.0.0.1:7890'
PROXY = "http://127.0.0.1:10809"
PUSH_MSG = ""
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN") or ""


def log_debug(log_str, obj=None):
    if DEBUG_MODE:
        print(log_str)
        if obj is not None:
            print_json(json.dumps(obj, indent=4))


# 检查变量
def check_env():
    invite_code_list = []
    if not INVITE_CODE:
        print("请按照文档设置INVITE_CODE环境变量")
        raise Exception("请按照文档设置INVITE_CODE环境变量")
    else:
        if "@" in INVITE_CODE:
            invite_code_list = INVITE_CODE.split("@")
        elif "\n" in INVITE_CODE:
            invite_code_list = INVITE_CODE.split("\n")
        else:
            invite_code_list.append(INVITE_CODE)
        return invite_code_list


# 推送
async def push(content):
    url = "http://www.pushplus.plus/send"
    data = {
        "token": PUSHPLUS_TOKEN,
        "title": "PikPak邀请通知",
        "content": content,
    }
    headers = {"Content-Type": "application/json"}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url, headers=headers, data=json.dumps(data)
            ) as response:
                response_data = await response.json()
                if response_data["code"] == 200:
                    print("推送成功")
                else:
                    print(f'推送失败，{response_data["msg"]}')
    except Exception as e:
        print(e)


# 滑块数据加密
def r(e, t):
    n = t - 1
    if n < 0:
        n = 0
    r = e[n]
    u = r["row"] // 2 + 1
    c = r["column"] // 2 + 1
    f = r["matrix"][u][c]
    l = t + 1
    if l >= len(e):
        l = t
    d = e[l]
    p = l % d["row"]
    h = l % d["column"]
    g = d["matrix"][p][h]
    y = e[t]
    m = 3 % y["row"]
    v = 7 % y["column"]
    w = y["matrix"][m][v]
    b = i(f) + o(w)
    x = i(w) - o(f)
    return [s(a(i(f), o(f))), s(a(i(g), o(g))), s(a(i(w), o(w))), s(a(b, x))]


def i(e):
    return int(e.split(",")[0])


def o(e):
    return int(e.split(",")[1])


def a(e, t):
    return str(e) + "^⁣^" + str(t)


def s(e):
    t = 0
    n = len(e)
    for r in range(n):
        t = u(31 * t + ord(e[r]))
    return t


def u(e):
    t = -2147483648
    n = 2147483647
    if e > n:
        return t + (e - n) % (n - t + 1) - 1
    if e < t:
        return n - (t - e) % (n - t + 1) + 1
    return e


def c(e, t):
    return s(e + "⁣" + str(t))


def img_jj(e, t, n):
    return {"ca": r(e, t), "f": c(n, t)}


def md5(input_string):
    return hashlib.md5(input_string.encode()).hexdigest()


async def get_sign(xid, t):
    e = [
        {"alg": "md5", "salt": "KHBJ07an7ROXDoK7Db"},
        {"alg": "md5", "salt": "G6n399rSWkl7WcQmw5rpQInurc1DkLmLJqE"},
        {"alg": "md5", "salt": "JZD1A3M4x+jBFN62hkr7VDhkkZxb9g3rWqRZqFAAb"},
        {"alg": "md5", "salt": "fQnw/AmSlbbI91Ik15gpddGgyU7U"},
        {"alg": "md5", "salt": "/Dv9JdPYSj3sHiWjouR95NTQff"},
        {"alg": "md5", "salt": "yGx2zuTjbWENZqecNI+edrQgqmZKP"},
        {"alg": "md5", "salt": "ljrbSzdHLwbqcRn"},
        {"alg": "md5", "salt": "lSHAsqCkGDGxQqqwrVu"},
        {"alg": "md5", "salt": "TsWXI81fD1"},
        {"alg": "md5", "salt": "vk7hBjawK/rOSrSWajtbMk95nfgf3"},
    ]
    md5_hash = f"YvtoWO6GNHiuCl7xundefinedmypikpak.com{xid}{t}"
    for item in e:
        md5_hash += item["salt"]
        md5_hash = md5(md5_hash)
    return md5_hash


async def get_mail():
    if USE_TEMP_EMAIL:
        json_data = {"min_name_length": 10, "max_name_length": 10}
        url = "https://api.internal.temp-mail.io/api/v3/email/new"
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=json_data, ssl=False) as response:
                response_data = await response.json()
                mail = response_data["email"]
            return mail
    else:
        return input("请输入注册邮箱：")


# 获取邮箱的验证码内容
async def get_code(mail, max_retries=10, delay=1):
    if USE_TEMP_EMAIL:
        retries = 0
        while retries < max_retries:
            url = f"https://api.internal.temp-mail.io/api/v3/email/{mail}/messages"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    html = await response.json()
                    if html:
                        text = (html[0])["body_text"]
                        code = re.search("\\d{6}", text).group()
                        print(f"获取邮箱验证码:{code}")
                        return code
                    else:
                        time.sleep(delay)
                        retries += 1
        print("获取邮箱邮件内容失败，未收到邮件...")
        return None
    else:
        return input("请输入邮件验证码：")


def save_image(img_data, img_path):
    if not os.path.exists(os.path.dirname(img_path)):
        os.makedirs(os.path.dirname(img_path))
    with open(img_path, "wb") as f:
        f.write(img_data)


async def get_new_token(result, xid, captcha):
    traceid = result["traceid"]
    pid = result["pid"]
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://user.mypikpak.com/credit/v1/report?deviceid={xid}&captcha_token={captcha}&type"
            f"=pzzlSlider&result=0&data={pid}&traceid={traceid}",
            ssl=False,
            proxy=PROXY,
        ) as response2:
            response_data = await response2.json()
            log_debug("获取验证TOKEN:", response_data)
            return response_data


# 发送邮箱验证码
async def send_verify_code(captcha_token, xid, mail):
    url = "https://user.mypikpak.com/v1/auth/verification"
    body = {
        "email": mail,
        "target": "ANY",
        "usage": "REGISTER",
        "locale": "zh-CN",
        "client_id": "YvtoWO6GNHiuCl7x",
    }
    headers = {
        "host": "user.mypikpak.com",
        "content-length": str(len(json.dumps(body))),
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "referer": "https://pc.mypikpak.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "MainWindow Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "PikPak/2.3.2.4101 Chrome/100.0.4896.160 Electron/18.3.15 Safari/537.36",
        "accept-language": "zh-CN",
        "content-type": "application/json",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "x-captcha-token": captcha_token,
        "x-client-id": "YvtoWO6GNHiuCl7x",
        "x-client-version": "2.3.2.4101",
        "x-device-id": xid,
        "x-device-model": "electron%2F18.3.15",
        "x-device-name": "PC-Electron",
        "x-device-sign": "wdi10.ce6450a2dc704cd49f0be1c4eca40053xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "x-net-work-type": "NONE",
        "x-os-version": "Win32",
        "x-platform-version": "1",
        "x-protocol-version": "301",
        "x-provider-name": "NONE",
        "x-sdk-version": "6.0.0",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json=body, headers=headers, ssl=False, proxy=PROXY
        ) as response:
            response_data = await response.json()
            log_debug("发送验证码:", response_data)
            return response_data


# 验证邮箱验证码
async def verify_code(xid, verification_id, code):
    url = "https://user.mypikpak.com/v1/auth/verification/verify"
    body = {
        "verification_id": verification_id,
        "verification_code": code,
        "client_id": "YvtoWO6GNHiuCl7x",
    }
    headers = {
        "host": "user.mypikpak.com",
        "content-length": str(len(json.dumps(body))),
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "referer": "https://pc.mypikpak.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "MainWindow Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "PikPak/2.3.2.4101 Chrome/100.0.4896.160 Electron/18.3.15 Safari/537.36",
        "accept-language": "zh-CN",
        "content-type": "application/json",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "x-client-id": "YvtoWO6GNHiuCl7x",
        "x-client-version": "2.3.2.4101",
        "x-device-id": xid,
        "x-device-model": "electron%2F18.3.15",
        "x-device-name": "PC-Electron",
        "x-device-sign": "wdi10.ce6450a2dc704cd49f0be1c4eca40053xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "x-net-work-type": "NONE",
        "x-os-version": "Win32",
        "x-platform-version": "1",
        "x-protocol-version": "301",
        "x-provider-name": "NONE",
        "x-sdk-version": "6.0.0",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json=body, headers=headers, ssl=False, proxy=PROXY
        ) as response:
            response_data = await response.json()
            log_debug("验证码验证结果:", response_data)
            return response_data


# 注册账号
async def signup(xid, mail, code, verification_token):
    url = "https://user.mypikpak.com/v1/auth/signup"
    body = {
        "email": mail,
        "verification_code": code,
        "verification_token": verification_token,
        "password": CUSTOM_PASSWORD,
        "client_id": "YvtoWO6GNHiuCl7x",
    }
    headers = {
        "host": "user.mypikpak.com",
        "content-length": str(len(json.dumps(body))),
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "referer": "https://pc.mypikpak.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "MainWindow Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "PikPak/2.3.2.4101 Chrome/100.0.4896.160 Electron/18.3.15 Safari/537.36",
        "accept-language": "zh-CN",
        "content-type": "application/json",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "x-client-id": "YvtoWO6GNHiuCl7x",
        "x-client-version": "2.3.2.4101",
        "x-device-id": xid,
        "x-device-model": "electron%2F18.3.15",
        "x-device-name": "PC-Electron",
        "x-device-sign": "wdi10.ce6450a2dc704cd49f0be1c4eca40053xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "x-net-work-type": "NONE",
        "x-os-version": "Win32",
        "x-platform-version": "1",
        "x-protocol-version": "301",
        "x-provider-name": "NONE",
        "x-sdk-version": "6.0.0",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json=body, headers=headers, ssl=False, proxy=PROXY
        ) as response:
            response_data = await response.json()
            log_debug("注册结果:", response_data)
            return response_data


# 二次安全验证
async def init1(xid, access_token, sub, sign, t):
    url = "https://user.mypikpak.com/v1/shield/captcha/init"
    body = {
        "client_id": "YvtoWO6GNHiuCl7x",
        "action": "POST:/vip/v1/activity/invite",
        "device_id": xid,
        "captcha_token": access_token,
        "meta": {
            "captcha_sign": "1." + sign,
            "client_version": "undefined",
            "package_name": "mypikpak.com",
            "user_id": sub,
            "timestamp": t,
        },
    }
    headers = {
        "host": "user.mypikpak.com",
        "content-length": str(len(json.dumps(body))),
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN",
        "referer": "https://pc.mypikpak.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "MainWindow Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "PikPak/2.3.2.4101 Chrome/100.0.4896.160 Electron/18.3.15 Safari/537.36",
        "content-type": "application/json",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "x-client-id": "YvtoWO6GNHiuCl7x",
        "x-client-version": "2.3.2.4101",
        "x-device-id": xid,
        "x-device-model": "electron%2F18.3.15",
        "x-device-name": "PC-Electron",
        "x-device-sign": "wdi10.ce6450a2dc704cd49f0be1c4eca40053xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "x-net-work-type": "NONE",
        "x-os-version": "Win32",
        "x-platform-version": "1",
        "x-protocol-version": "301",
        "x-provider-name": "NONE",
        "x-sdk-version": "6.0.0",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json=body, headers=headers, ssl=False, proxy=PROXY
        ) as response:
            response_data = await response.json()
            log_debug("二次安全验证:", response_data)
            return response_data


async def invite(access_token, captcha_token, xid):
    url = "https://api-drive.mypikpak.com/vip/v1/activity/invite"
    body = {"apk_extra": {"invite_code": ""}}
    headers = {
        "host": "api-drive.mypikpak.com",
        "content-length": str(len(json.dumps(body))),
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN",
        "authorization": "Bearer " + access_token,
        "referer": "https://pc.mypikpak.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) PikPak/2.3.2.4101 "
        "Chrome/100.0.4896.160 Electron/18.3.15 Safari/537.36",
        "content-type": "application/json",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "x-captcha-token": captcha_token,
        "x-client-id": "YvtoWO6GNHiuCl7x",
        "x-client-version": "2.3.2.4101",
        "x-device-id": xid,
        "x-system-language": "zh-CN",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json=body, headers=headers, ssl=False, proxy=PROXY
        ) as response:
            response_data = await response.json()
            log_debug("获取邀请:", response_data)
            return response_data


# 三次安全验证
async def init2(xid, access_token, sub, sign, t):
    url = "https://user.mypikpak.com/v1/shield/captcha/init"
    body = {
        "client_id": "YvtoWO6GNHiuCl7x",
        "action": "POST:/vip/v1/order/activation-code",
        "device_id": xid,
        "captcha_token": access_token,
        "meta": {
            "captcha_sign": "1." + sign,
            "client_version": "undefined",
            "package_name": "mypikpak.com",
            "user_id": sub,
            "timestamp": t,
        },
    }
    headers = {
        "host": "user.mypikpak.com",
        "content-length": str(len(json.dumps(body))),
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN",
        "referer": "https://pc.mypikpak.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "MainWindow Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "PikPak/2.3.2.4101 Chrome/100.0.4896.160 Electron/18.3.15 Safari/537.36",
        "content-type": "application/json",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "x-client-id": "YvtoWO6GNHiuCl7x",
        "x-client-version": "2.3.2.4101",
        "x-device-id": xid,
        "x-device-model": "electron%2F18.3.15",
        "x-device-name": "PC-Electron",
        "x-device-sign": "wdi10.ce6450a2dc704cd49f0be1c4eca40053xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "x-net-work-type": "NONE",
        "x-os-version": "Win32",
        "x-platform-version": "1",
        "x-protocol-version": "301",
        "x-provider-name": "NONE",
        "x-sdk-version": "6.0.0",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json=body, headers=headers, ssl=False, proxy=PROXY
        ) as response:
            response_data = await response.json()
            log_debug("三次安全验证:", response_data)
            return response_data


# 通过邀请码进行邀请
async def activation_code(access_token, captcha, xid, in_code):
    url = "https://api-drive.mypikpak.com/vip/v1/order/activation-code"
    body = {"activation_code": in_code, "page": "invite"}
    headers = {
        "host": "api-drive.mypikpak.com",
        "content-length": str(len(json.dumps(body))),
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN",
        "authorization": "Bearer " + access_token,
        "referer": "https://pc.mypikpak.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) PikPak/2.3.2.4101 "
        "Chrome/100.0.4896.160 Electron/18.3.15 Safari/537.36",
        "content-type": "application/json",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "x-captcha-token": captcha,
        "x-client-id": "YvtoWO6GNHiuCl7x",
        "x-client-version": "2.3.2.4101",
        "x-device-id": xid,
        "x-system-language": "zh-CN",
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=body, headers=headers, ssl=False, proxy=PROXY
                ) as response:
                    response_data = await response.json()
                    log_debug("填写邀请:", response_data)
                    return response_data
        except Exception as error:
            print("Error:", error)
            raise error


# 初始安全验证（验证是否为临时邮箱）
async def init_and_get_captcha_token(xid, mail):

    url = "https://user.mypikpak.com/v1/shield/captcha/init"
    body = {
        "client_id": "YvtoWO6GNHiuCl7x",
        "action": "POST:/v1/auth/verification",
        "device_id": xid,
        "captcha_token": "",
        "meta": {"email": mail},
    }
    headers = {
        "host": "user.mypikpak.com",
        "content-length": str(len(json.dumps(body))),
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "referer": "https://pc.mypikpak.com",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "cross-site",
        "user-agent": "MainWindow Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "PikPak/2.3.2.4101 Chrome/100.0.4896.160 Electron/18.3.15 Safari/537.36",
        "accept-language": "zh-CN",
        "content-type": "application/json",
        "sec-ch-ua": '" Not A;Brand";v="99", "Chromium";v="100"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "x-client-id": "YvtoWO6GNHiuCl7x",
        "x-client-version": "2.3.2.4101",
        "x-device-id": xid,
        "x-device-model": "electron%2F18.3.15",
        "x-device-name": "PC-Electron",
        "x-device-sign": "wdi10.ce6450a2dc704cd49f0be1c4eca40053xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "x-net-work-type": "NONE",
        "x-os-version": "Win32",
        "x-platform-version": "1",
        "x-protocol-version": "301",
        "x-provider-name": "NONE",
        "x-sdk-version": "6.0.0",
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json=body, headers=headers, ssl=False, proxy=PROXY
        ) as response:
            response_data = await response.json()

            # 目前只要是临时邮箱，都会包含 Google 验证的 url
            # 临时邮箱初始化也会获得一个临时的 captcha_token，但这个 captcha_token 不能直接用于发送验证码，需要进行 Google 验证后获得的新 captcha_token 才有效
            if response_data.get("url"):  # 直接用response_data["url"]会在没有字段时报错
                log_debug("初始安全验证:", response_data)
                reCaptcha_url = (
                    response_data["url"]
                    + "&redirect_uri=https%3A%2F%2Fmypikpak.com%2Floading&state=getcaptcha"
                    + str(round(time.time() * 1000))
                )
                print("请复制网址到浏览器进行谷歌验证：")
                print(reCaptcha_url)
                captcha_url = urlparse(input("请复制通过验证后的网址在此处："))
                # captcha_token_info = await get_new_token(captcha_url, xid, Init['captcha_token'])
                captcha_token = parse_qs(captcha_url.query).get("captcha_token", [""])[
                    0
                ]
                return captcha_token

            # 如果是主流邮箱则不需要进行 Google 验证，获得的 captcha_token 可以直接用于发送验证码
            if response_data.get("captcha_token"):
                return response_data["captcha_token"]

            print("邮箱或者IP频繁,请更换IP或者稍后重试......")
            raise Exception(response_data.get("error_description", "Unknown error"))


async def main(incode):
    global PUSH_MSG
    try:
        start_time = time.time()
        xid = str(uuid.uuid4()).replace("-", "")
        mail = await get_mail()
        # 初始安全验证（验证是否为临时邮箱）
        captcha_token = await init_and_get_captcha_token(xid, mail)
        # 发送邮箱验证码
        verification_id = await send_verify_code(captcha_token, xid, mail)
        code = await get_code(mail)
        # 验证邮箱验证码
        verification_response = await verify_code(
            xid, verification_id["verification_id"], code
        )
        # 注册账号
        signup_response = await signup(
            xid, mail, code, verification_response["verification_token"]
        )
        current_time = str(int(time.time()))
        sign = await get_sign(xid, current_time)
        # 二次安全验证
        init1_response = await init1(
            xid,
            signup_response["access_token"],
            signup_response["sub"],
            sign,
            current_time,
        )
        await invite(
            signup_response["access_token"], init1_response["captcha_token"], xid
        )
        # 三次安全验证
        init2_response = await init2(
            xid,
            signup_response["access_token"],
            signup_response["sub"],
            sign,
            current_time,
        )
        # 通过邀请码进行邀请
        activation = await activation_code(
            signup_response["access_token"],
            init2_response["captcha_token"],
            xid,
            incode,
        )
        end_time = time.time()
        run_time = f"{(end_time - start_time):.2f}"
        if activation["add_days"] == 5:
            print(f"邀请码: {incode} ==> 邀请成功, 用时: {run_time} 秒")
            print(f"邮箱: {mail}")
            print(f"密码: {CUSTOM_PASSWORD}")
            PUSH_MSG += f"邀请码: {incode} ==> 邀请成功\n邮箱: {mail}\n密码: {CUSTOM_PASSWORD}\n"
            return
        elif activation["add_days"] == 0 and activation['result'] == 'ACCEPTED':
            print(f"邀请码: {incode} ==> 邀请处理完成，PikPak 需在 24 小时内确认邀请的有效性，确认有效才会给予邀请奖励！用时: {run_time} 秒")
            print(f"邮箱: {mail}")
            print(f"密码: {CUSTOM_PASSWORD}")
            PUSH_MSG += f"邀请码: {incode} ==> 邀请处理完成，PikPak 需在 24 小时内确认邀请的有效性，确认有效才会给予邀请奖励！\n邮箱: {mail}\n密码: {CUSTOM_PASSWORD}\n"
            return
        else:
            print(f"邀请码: {incode} ==> 邀请失败, 用时: {run_time} 秒")
            print(f"邮箱: {mail}")
            print(f"密码: {CUSTOM_PASSWORD}")
            PUSH_MSG += f"邀请码: {incode} ==> 邀请失败\n"
        # input('按回车键再次邀请!!!')
        await main(incode)
    except Exception as e:
        if "环境变量" in str(e):
            return
        print(f"异常捕获:{e}")
        PUSH_MSG += f"邀请异常:{e}\n"
        # print('请检查网络环境,(开启科学上网)重试!!!')
        # input('按回车键重试!!!')
        # await main()


async def run():
    global PUSH_MSG
    invite_code_list = check_env()
    for i in range(len(invite_code_list)):
        print(f"=========正在邀请第 {i + 1} 个邀请码=========")
        PUSH_MSG += f"=========第 {i + 1} 个邀请码=========\n"
        invite_code = invite_code_list[i]
        await main(invite_code)
    input("按回车退出>>")
    
    if PUSHPLUS_TOKEN:
        await push(PUSH_MSG)


asyncio.run(run())
