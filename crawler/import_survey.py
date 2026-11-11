#!/usr/bin/env python3
"""Import the hand-collected sources of the multi-agent survey (private repo) as link records.

Reads ../multi-agent-swarm-survey/sources/index.jsonl. X posts are re-read through api.fxtwitter.com
for their text, likes and quoted post (used for summaries and for grouping reactions).
Writes crawler/work/survey_items.jsonl. Only titles, links and metadata are published.
"""
import concurrent.futures as cf, json, os, re, time, urllib.request
from email.utils import parsedate_to_datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SURVEY = os.path.join(HERE, "..", "..", "multi-agent-swarm-survey")
CJK = re.compile(r"[぀-ヿ一-鿿＀-￯]")
TYPE = {"paper": "paper", "blog": "blog", "docs": "blog", "news": "blog", "wiki": "blog", "tweet": "post", "thread": "post", "x_article": "post",
        "repo": "code", "forum": "discussion", "video": "video"}
# Survey topics that pin down a category. The others (X threads, academic papers, societies and risks) are left to the rules and the LLM.
TOPIC2CAT = {"industry": "orch", "industry_fable52": "orch", "tooling_economics": "infra", "foundations": "found"}


def tweet(i):
    for k in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(f"https://api.fxtwitter.com/status/{i}", headers={"User-Agent": "multi-agent-reader/0.1"}), timeout=30) as r:
                return json.load(r).get("tweet")
        except Exception as ex:
            if getattr(ex, "code", None) == 404:
                return None
            time.sleep(2 * (k + 1))
    return None


def article_text(art):
    out = []
    def walk(n):
        if isinstance(n, dict):
            if isinstance(n.get("text"), str):
                out.append(n["text"])
            for v in n.values():
                walk(v)
        elif isinstance(n, list):
            for v in n:
                walk(v)
    walk(art)
    return " ".join(out)


def main():
    rows = [json.loads(l) for l in open(os.path.join(SURVEY, "sources", "index.jsonl"))]
    xs = {r["slug"]: re.search(r"x\.com/[^/]+/status/(\d+)", r["url_norm"]).group(1) for r in rows if re.search(r"x\.com/[^/]+/status/(\d+)", r["url_norm"])}
    with cf.ThreadPoolExecutor(8) as ex:
        tw = dict(zip(xs, ex.map(tweet, xs.values())))
    out = []
    for r in rows:
        url, typ = r["url"], TYPE.get(r.get("type"), "blog")
        title, abstract, quote, likes = r.get("title") or "", "", None, None
        if r["slug"] in xs:
            t = tw.get(r["slug"])
            if t:
                who = t["author"]["screen_name"]
                text = t.get("text") or ""
                art = t.get("article") or {}
                if art.get("title"):
                    text = (art["title"] + ". " + text + " " + article_text(art)).strip()
                clean = re.sub(r"\s+", " ", re.sub(r"https?://\S+", "", text)).strip()
                if clean:
                    title = f"@{who}: " + clean[:110] + ("…" if len(clean) > 110 else "")
                abstract = clean[:1500]
                quote = (t.get("quote") or {}).get("id")
                likes = t.get("likes")
                url = f"https://x.com/{who}/status/{xs[r['slug']]}"
                try:
                    r["date"] = parsedate_to_datetime(t["created_at"]).date().isoformat()
                except Exception:
                    pass
        if not title or CJK.search(title):
            title = re.sub(r"^https?://(www\.)?", "", url).rstrip("/")
        author = r.get("author") or ""
        author = "" if CJK.search(author) else re.sub(r"\s*\([^)]*\)", "", author).strip()
        cats = sorted({TOPIC2CAT[t] for t in r.get("topics", []) if t in TOPIC2CAT})
        out.append(dict(key="sv:" + r["slug"], type=typ, title=title.strip(), url=url, date=(r.get("date") or "")[:10], authors=[author] if author else [],
                        abstract=abstract, cat_hint=cats[0] if cats else None, survey_topics=r.get("topics", []), quote=f"x:{quote}" if quote else None,
                        likes=likes, via=["survey"]))
    with open(os.path.join(HERE, "work", "survey_items.jsonl"), "w") as f:
        for o in out:
            f.write(json.dumps(o, ensure_ascii=False) + "\n")
    print(len(out), "items;", sum(1 for s in xs if tw.get(s)), "of", len(xs), "X posts read")


if __name__ == "__main__":
    main()
