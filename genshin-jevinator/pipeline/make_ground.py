# -*- coding: utf-8 -*-
"""正解データを作る。出典は Project Amber のミラー gi.yatta.moe（公式データの抽出）。
  curl https://gi.yatta.moe/api/v2/en/avatar -o av_en.json
  curl https://gi.yatta.moe/api/v2/jp/avatar -o av_jp.json
日本語名も公式のものがそのまま取れるので、こちらで名前を考えない。
旅人・ドール（MAINACTOR）は元素を切り替える主人公なので外す。
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import datetime, json, os
HERE = os.path.dirname(os.path.abspath(__file__))
ELEM = {"Fire":"炎", "Water":"水", "Wind":"風", "Electric":"雷",
        "Grass":"草", "Ice":"氷", "Rock":"岩"}
WEAPON = {"WEAPON_SWORD_ONE_HAND":"片手剣", "WEAPON_CLAYMORE":"両手剣",
          "WEAPON_POLE":"長柄武器", "WEAPON_BOW":"弓", "WEAPON_CATALYST":"法器"}
REGION = {"MONDSTADT":"モンド", "LIYUE":"璃月", "INAZUMA":"稲妻", "SUMERU":"スメール",
          "FONTAINE":"フォンテーヌ", "NATLAN":"ナタ",
          "SNEZHNAYA":"スネージナヤ", "SNEZHNAYA_STAR":"スネージナヤ", "FATUI":"スネージナヤ",
          "NODKRAI":"ノドクライ", "NODKRAI_ZIBAI":"ノドクライ",
          "RANGER":"どこにも属さない", "OMNI_SCOURGE":"どこにも属さない",
          "HVISION":"どこにも属さない"}
BODY = {"LOLI":"幼い少女", "GIRL":"少女", "LADY":"大人の女性",
        "BOY":"少年", "MALE":"大人の男性"}

def main():
    en = json.load(open(os.path.join(HERE, "av_en.json"), encoding="utf-8"))["data"]["items"]
    jp = json.load(open(os.path.join(HERE, "av_jp.json"), encoding="utf-8"))["data"]["items"]
    g = {}
    for k, v in en.items():
        if v["region"] == "MAINACTOR":
            continue
        name = jp[k]["name"]
        g[name] = dict(en=v["name"], 元素=ELEM[v["element"]], 武器=WEAPON[v["weaponType"]],
                       地域=REGION[v["region"]], 星=v["rank"], 体型=BODY[v["bodyType"]],
                       誕生日=v.get("birthday"),
                       実装日=str(datetime.datetime.utcfromtimestamp(v["release"]).date()))
    json.dump(g, open(os.path.join(HERE, "ground.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"{len(g)}キャラ。最新: " +
          ", ".join(n for n, _ in sorted(g.items(), key=lambda x: x[1]['実装日'])[-5:]))

if __name__ == "__main__":
    main()
