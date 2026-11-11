#!/usr/bin/env python3
"""Recent posts from tracked X accounts, read through the public api.fxtwitter.com (no login).

Usage: x_accounts.py --since YYYY-MM-DD
Keeps posts whose text matches the topic keywords. Output: crawler/work/x_candidates.jsonl
"""
import argparse, json, os, re, sys, time, urllib.request
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS = """theo omarsar0 METR_Evals Steve_Yegge steipete tobyordoxford factory addyosmani cognition badlogicgames OpenAI bcherny karpathy poteto
Kimi_Moonshot cursor_ai SakanaAILabs GergelyOrosz antigravity dair_ai mitchellh claudeai AnthropicAI ClaudeDevs dexhorthy GeoffreyHuntley rohanpaul_ai TheZvi
scaling01 mitsuhiko OfirPress aneeshpappu kjha02 polynoamial emollick OpenAIDevs swyx simonw doodlestein mntruell hardmaru ValsAI PrimeIntellect jyangballin
__eknight__ KyeGomezB gneubig alexandr_wang _Hao_Zhu leerob thdxr natashajaques maxhkw awhanjie CShorten30 lvwerra joon_s_pk chiyuanzhang_ jxmnop""".split()
TOPIC = re.compile(r"multi-?agent|sub-?agents?|agent (?:swarms?|teams?|fleets?|orchestrat\w*)|swarms? of agents|(?:parallel|many|thousands? of|hundreds of|\d[\d,]* ) ?(?:coding )?agents|"
                   r"orchestrat\w* .{0,20}agents|agents? (?:coordinat|collaborat|debat)\w*|generative agents|agent societ|agentic workflows?|gas town|dynamic workflows?|"
                   r"model context protocol|\bA2A\b|swarm scaling", re.I)


def get(url):
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "multi-agent-reader/0.1"}), timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(2 * (k + 1))
    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True)
    ap.add_argument("--out", default=os.path.join(HERE, "work", "x_candidates.jsonl"))
    a = ap.parse_args()
    out = {}
    for h in ACCOUNTS:
        cursor = None
        for page in range(4):
            d = get(f"https://api.fxtwitter.com/2/profile/{h}/statuses" + (f"?cursor={cursor}" if cursor else ""))
            rs = d.get("results") or []
            stop = False
            for t in rs:
                try:
                    day = parsedate_to_datetime(t["created_at"]).date().isoformat()
                except Exception:
                    continue
                if day < a.since:
                    stop = True
                    continue
                text = t.get("text") or ""
                if not TOPIC.search(text):
                    continue
                who = t["author"]["screen_name"]
                clean = re.sub(r"https?://\S+", "", text).strip()
                out[t["id"]] = dict(key="x:" + t["id"], type="post", title=f"@{who}: " + clean[:110] + ("…" if len(clean) > 110 else ""),
                                    url=f"https://x.com/{who}/status/{t['id']}", date=day, authors=["@" + who], abstract=clean[:600], via=[f"x:{h}"])
            cursor = (d.get("cursor") or {}).get("bottom")
            if stop or not cursor or not rs:
                break
        print(h, len(out), flush=True)
    with open(a.out, "w") as f:
        for r in out.values():
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print("DONE", len(out))


if __name__ == "__main__":
    main()
