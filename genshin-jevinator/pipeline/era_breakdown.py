# -*- coding: utf-8 -*-
"""「98問ぜんぶJev」の表が外すのは、Jevが知らない新しいキャラなのかを確かめる。"""
import asyncio, sys
import typesafe_sdk as ts
from gdata import GROUND, CHARS
from gautoplay import run

async def main():
    c = ts.AsyncTypeSafeClient(); sem = asyncio.Semaphore(16)
    old = [n for n in CHARS if GROUND[n]["実装日"] < "2024-10-01"]
    new = [n for n in CHARS if GROUND[n]["実装日"] >= "2024-10-01"]
    for label, path in [("公式データ＋Jev", "table_hybrid.json"), ("98問ぜんぶJev", "table_jev.json")]:
        for era, group in [(f"2024年9月まで({len(old)}人)", old), (f"2024年10月以降({len(new)}人)", new)]:
            await run(c, sem, path, f"{label} / {era}", group)
    await c.aclose()

if __name__ == "__main__":
    asyncio.run(main())

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))