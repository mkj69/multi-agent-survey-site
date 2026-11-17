#!/usr/bin/env bash
# Weekly full pipeline, run from cron on the machine that has Codex.
#
# The daily GitHub Action can only use keyword rules: it drops every candidate the rules are unsure
# about (about a thousand a day) and writes no summaries. This script re-crawls the last few days and
# runs the whole pipeline — Codex judges relevance, writes one-sentence summaries and groups the X
# posts — then commits and pushes.
#
# Unlike crawler/daily.py this never clears the whole work directory: llm_cache.jsonl (verdicts
# already paid for) and survey_items.jsonl (the hand-checked sources) must survive between runs.
set -uo pipefail
cd "$(dirname "$0")/.." || exit 1
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
export HOME="${HOME:?}"
mkdir -p crawler/work
exec >>"crawler/work/weekly.log" 2>&1
exec 9>crawler/work/.weekly.lock
flock -n 9 || { echo "$(date -Is) another run holds the lock, skipping"; exit 0; }

say() { echo "$(date -Is) $*"; }
fail() { say "FAILED: $*"; exit 1; }
say "=== weekly run starting in $PWD"

git pull --rebase -q || fail "git pull"
since=$(python3 -c "
import datetime, json
d = json.load(open('data/items.json'))
print((datetime.date.fromisoformat(d['updated']) - datetime.timedelta(days=9)).isoformat())") || fail "read items.json"
say "crawling since $since"

rm -f crawler/work/oa_candidates.jsonl crawler/work/arxiv_candidates.jsonl \
      crawler/work/other_candidates.jsonl crawler/work/x_candidates.jsonl
python3 crawler/other.py --since "$since" &
python3 crawler/arxiv_recent.py --since "$since" &
python3 crawler/x_accounts.py --since "$since" &
python3 crawler/papers.py --since "$since" &
wait
say "crawl done: $(wc -l < crawler/work/x_candidates.jsonl 2>/dev/null || echo 0) X posts, \
$(wc -l < crawler/work/other_candidates.jsonl 2>/dev/null || echo 0) repos and threads, \
$(wc -l < crawler/work/arxiv_candidates.jsonl 2>/dev/null || echo 0) arXiv, \
$(wc -l < crawler/work/oa_candidates.jsonl 2>/dev/null || echo 0) OpenAlex"

python3 crawler/classify.py --llm --judge-all --workers 16 || fail "classify"
python3 crawler/build.py || fail "build"
python3 crawler/summarize.py || say "warning: summarize failed, keeping the summaries we have"
python3 crawler/reactions.py || say "warning: reactions failed, keeping the grouping we have"
python3 crawler/build.py || fail "second build"

git add -A data || fail "git add"
if git diff --cached --quiet; then
  say "no change, nothing to publish"
  exit 0
fi
n=$(python3 -c "import json; print(len(json.load(open('data/items.json'))['items']))")
git commit -q -m "Weekly catch-up $(date +%F): $n items

Re-crawled the last few days and ran the full pipeline, so the items the daily keyword-only job
left out are judged by Codex and every item has a summary.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>" || fail "git commit"
git pull --rebase -q || fail "git pull before push"
git push -q || fail "git push"
say "published, $n items"
