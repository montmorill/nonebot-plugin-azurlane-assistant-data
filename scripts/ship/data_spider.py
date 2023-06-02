import os, json, re, pathlib
import time

import httpx
from bs4 import BeautifulSoup

from .ship_model import Ship
from ..utils import get_content


def ship_data():
    print("===开始同步\"舰船资料\"数据===")
    url_prefix = "https://wiki.biligame.com"
    cot = get_content("https://wiki.biligame.com/blhx/%E8%88%B0%E8%88%B9%E5%9B%BE%E9%89%B4")
    soup = BeautifulSoup(cot, "html.parser")

    # leng = len(soup.find_all("div", class_="jntj-1 divsort"))
    # if json.load(open(f"{str(pathlib.Path.cwd().parent)}/azurlane/ship.json", "r", encoding="utf-8"))["total_num"] == leng:
    #     print("===舰船资料无更新,跳过同步步骤===")
    #     return

    lst = soup.find_all("div", class_="jntj-1 divsort")

    slist = []
    for i, ship in enumerate(lst):
        print(f"正在同步第{i + 1}条数据, 共{len(lst)}条, 进度:{round((i + 1) / len(lst) * 100, 2)}%")
        alias = []
        for j in ship.find_all("span", class_="jntj-4"):
            pattern = re.compile(r">(?P<raw>.*?)<br/>(?P<now>.*?)<")
            match = re.search(pattern, str(j.contents[-1]))
            if match is None:
                name = j.text
                break
            name = match.group("now")
            alias.append(match.group("raw"))

        iname = ship.find("div", class_="jntj-3").find("img")["alt"]
        if iname.find("决战方案") != -1 or iname.find("海上传奇") != -1:
            rarity = 4
        elif iname.find("超稀有") != -1 or iname.find("最高方案") != -1:
            rarity = 3
        elif iname.find("精锐") != -1:
            rarity = 2
        elif iname.find("稀有") != -1:
            rarity = 1
        elif iname.find("普通") != -1:
            rarity = 0
        else:
            print(f"稀有度出错:{name}\n")
            pass

        wiki_url = ship.find("a")["href"]
        img_url = ship.find("div", class_="jntj-2").find("img")["src"]
        local_url = "img/ship_icon/" + name + ".png"

        def parse_wiki(soup_0):
            skin_lst_ = {}
            for item in soup_0.find("td", id="characters").find_all("div", class_="Contentbox2"):
                url = item.find("img").get("src")
                name_ = item.find("img").get("alt").split(".")[0]
                skin_lst_[name_] = url
            return skin_lst_

        try:
            wiki = get_content(url_prefix + wiki_url, range=40000)
        except httpx.RemoteProtocolError:
            wiki = get_content(url_prefix + wiki_url, range=40000)
        soup_ = BeautifulSoup(wiki, "html.parser")
        try:
            skin_lst = parse_wiki(soup_)
        except AttributeError:
            wiki = get_content(url_prefix + wiki_url)
            soup_ = BeautifulSoup(wiki, "html.parser")
            skin_lst = parse_wiki(soup_)

        ship = Ship(
            name=name,
            rarity=rarity,
            wiki_page=url_prefix + wiki_url,
            remote_icon_path=str(img_url),
            local_icon_path=str(local_url),
            alias=alias,
            skins_url=skin_lst
        )
        sdata = ship.json(ensure_ascii=False)
        slist.append(json.loads(sdata))
        time.sleep(0.1)

    with open(f"{str(pathlib.Path.cwd().parent)}/azurlane/ship.json", "w", encoding="utf-8") as f:
        json.dump({"total_num": leng, "data": slist}, f, ensure_ascii=False, indent=4)
    print("===舰船资料同步完成===")
