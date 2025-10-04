import base64
import json
from typing import Any

import requests

COMMON_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "sec-ch-ua": "\"Not;A=Brand\";v=\"99\", \"Microsoft Edge\";v=\"139\", \"Chromium\";v=\"139\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0"
}


def get_captcha_data():
    """获取验证码数据"""
    params = {
        "aid": '199999761',
        "protocol": "https",
        "accver": "1",
        "showtype": "popup",
        "ua": base64.b64encode(COMMON_HEADERS['user-agent'].encode()).decode(),
        "noheader": "1",
        "fb": "1",
        "aged": "0",
        "enableAged": "0",
        "enableDarkMode": "0",
        "grayscale": "1",
        "clientype": "2",
        "cap_cd": "",
        "uid": "",
        "lang": "zh-cn",
        "entry_url": "https://turing.captcha.gtimg.com/1/template/drag_ele.html",
        "elder_captcha": "0",
        "js": "/tcaptcha-frame.97a921e6.js",
        "login_appid": "",
        "wb": "1",
        "subsid": "9",
        "callback": "",
        "sess": ""
    }

    try:
        # 获取验证码配置
        response = requests.get(
            f"https://turing.captcha.qcloud.com/cap_union_prehandle",
            params=params,
            headers=COMMON_HEADERS
        )
        response.raise_for_status()

        # 解析JSON数据
        json_str = response.text.strip()[1:-1]  # 移除括号
        data = json.loads(json_str)

        return data
    except Exception as e:
        print(f"获取验证码失败: {e}")
        return None


def get_captcha_images(data) -> tuple[bytes | Any, bytes | Any] | tuple[None, None]:
    # 获取图片URL
    bg_url = "https://turing.captcha.qcloud.com" + data["data"]["dyn_show_info"]["bg_elem_cfg"]["img_url"]
    sprite_url = "https://turing.captcha.qcloud.com" + data["data"]["dyn_show_info"]["sprite_url"]
    try:
        # 下载图片
        return (
            requests.get(bg_url, headers=COMMON_HEADERS).content,
            requests.get(sprite_url, headers=COMMON_HEADERS).content
        )
    except Exception as e:
        raise Exception(f"获取验证码图片失败: {e}")


if __name__ == '__main__':
    bg_img, sprite_img = get_captcha_images(get_captcha_data())
