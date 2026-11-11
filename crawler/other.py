#!/usr/bin/env python3
"""Collect non-paper candidates: GitHub repos, Hugging Face models/datasets/spaces,
Hacker News stories, Reddit posts. Output: crawler/work/other_candidates.jsonl.

Usage: other.py [--since YYYY-MM-DD]   (--since limits HN/Reddit/GitHub to newer items; used by the daily job)
"""
import argparse, json, os, re, subprocess, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
UA = {"User-Agent": "multi-agent-reader-crawler/0.1"}

GH_QUERIES = [
    "multi-agent framework", "multi-agent llm", "agent swarm", "swarm agents", "agent orchestration", "agent orchestrator", "subagents", "claude code subagents",
    "parallel coding agents", "coding agent team", "agent teams", "multi-agent debate", "generative agents", "agent society simulation", "llm social simulation",
    "model context protocol", "a2a protocol", "agent communication protocol", "mixture of agents", "autogen", "crewai", "langgraph multi-agent", "metagpt", "camel agents",
    "multi agent coding", "agent fleet", "agentic workflow",
]
HF_QUERIES = ["multi-agent", "multiagent", "agent-swarm", "multi-agent-debate", "generative-agents", "agent-society", "mixture-of-agents"]
TEXT_QUERIES = [
    "multi-agent", "multi agent", "multiagent", "agent swarm", "swarm of agents", "agent swarms", "subagents", "sub-agents", "parallel agents", "agent teams",
    "agent orchestration", "orchestrator agent", "multi-agent debate", "generative agents", "AutoGen", "CrewAI", "LangGraph", "MetaGPT", "ChatDev", "CAMEL agents",
    "Gas Town", "agent fleet", "parallel Claude Code", "multiple Claude Code", "Codex agents parallel", "dynamic workflows", "Model Context Protocol", "A2A protocol",
    "multi-agent research system", "swarm scaling", "10,000 agents", "1,000 agents",
]


def get(url, headers=UA, tries=5):
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=30) as r:
                return json.load(r)
        except Exception as ex:
            if getattr(ex, "code", None) in (404, 422):
                return None
            time.sleep(5 * (k + 1))
    return None


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    if r.returncode != 0:
        time.sleep(30)
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None)
    ap.add_argument("--out", default=os.path.join(WORK, "other_candidates.jsonl"))
    a = ap.parse_args()
    os.makedirs(WORK, exist_ok=True)
    out = {}

    def add(key, **kw):
        if key in out:
            out[key]["via"] = sorted(set(out[key]["via"] + kw["via"]))
        else:
            out[key] = kw

    # GitHub repositories (search API: 30 requests/min with a token)
    for q in GH_QUERIES:
        qq = q + (f" pushed:>={a.since}" if a.since else "")
        for page in range(1, 4):
            d = gh("search/repositories?" + urllib.parse.urlencode({"q": qq, "sort": "stars", "per_page": 100, "page": page}))
            items = (d or {}).get("items") or []
            for r in items:
                add("gh:" + r["full_name"].lower(), type="code", title=r["full_name"], url=r["html_url"], date=(r.get("created_at") or "")[:10],
                    authors=[r["owner"]["login"]], abstract=(r.get("description") or "")[:600], stars=r.get("stargazers_count"),
                    topics=r.get("topics") or [], via=[f"gh:{q}"])
            time.sleep(2.2)
            if len(items) < 100:
                break
        print("github", q, len(out), flush=True)

    # Hugging Face hub
    for q in HF_QUERIES:
        for kind, typ in (("models", "model"), ("datasets", "dataset"), ("spaces", "code")):
            d = get(f"https://huggingface.co/api/{kind}?" + urllib.parse.urlencode({"search": q, "limit": 200, "full": "false"})) or []
            for m in d:
                rid = m.get("id") or m.get("modelId")
                if not rid:
                    continue
                pre = "" if kind == "models" else kind + "/"
                add(f"hf:{kind}:{rid.lower()}", type=typ, title=rid, url=f"https://huggingface.co/{pre}{rid}", date=(m.get("createdAt") or "")[:10],
                    authors=[rid.split("/")[0]], abstract="", likes=m.get("likes"), downloads=m.get("downloads"), via=[f"hf:{q}"])
        print("hf", q, len(out), flush=True)

    # Hacker News (all time unless --since)
    since_ts = int(time.mktime(time.strptime(a.since, "%Y-%m-%d"))) if a.since else 0
    for q in TEXT_QUERIES:
        for page in range(0, 5):
            params = {"query": q, "tags": "story", "hitsPerPage": 100, "page": page}
            if since_ts:
                params["numericFilters"] = f"created_at_i>{since_ts}"
            d = get("https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode(params))
            hits = (d or {}).get("hits") or []
            for h in hits:
                add("hn:" + h["objectID"], type="discussion", title=h.get("title") or "", url=f"https://news.ycombinator.com/item?id={h['objectID']}",
                    date=(h.get("created_at") or "")[:10], authors=[h.get("author")], abstract="", points=h.get("points"),
                    comments=h.get("num_comments"), link=h.get("url"), via=[f"hn:{q}"])
            if len(hits) < 100:
                break
        print("hn", q, len(out), flush=True)

    # Reddit via the arctic-shift archive (title search). The archive is often slow; give up after repeated failures.
    fails = 0
    for q in TEXT_QUERIES:
        if fails >= 3:
            print("reddit archive not responding; skipped", flush=True)
            break
        params = {"title": q, "limit": 100, "sort": "desc"}
        if a.since:
            params["after"] = a.since
        d = get("https://arctic-shift.photon-reddit.com/api/posts/search?" + urllib.parse.urlencode(params), tries=2)
        fails = fails + 1 if d is None else 0
        for p in (d or {}).get("data") or []:
            add("rd:" + p["id"], type="discussion", title=p.get("title") or "", url="https://www.reddit.com" + (p.get("permalink") or ""),
                date=time.strftime("%Y-%m-%d", time.gmtime(p.get("created_utc") or 0)), authors=[p.get("author")], abstract=(p.get("selftext") or "")[:600],
                subreddit=p.get("subreddit"), points=p.get("score"), comments=p.get("num_comments"), link=p.get("url"), via=[f"reddit:{q}"])
        time.sleep(1)
        print("reddit", q, len(out), flush=True)

    with open(a.out, "w") as f:
        for k, v in out.items():
            f.write(json.dumps(dict(key=k, **v), ensure_ascii=False) + "\n")
    print("DONE", len(out), flush=True)


if __name__ == "__main__":
    main()
