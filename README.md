# Multi-Agent Reader

A reading list and reader for work on multi-agent AI systems: agent swarms and how they scale,
orchestration of agent teams, collaboration and debate between LLM agents, agent societies and
emergent behaviour, multi-agent risks, protocols and frameworks, and the classic work these build on
(voting theory, parallel computing, multi-agent systems, MARL, swarm intelligence). Each item has a
one-sentence summary, and a timeline map shows the classic works and what each built on.

**Site:** https://mkj69.github.io/multi-agent-survey-site/ · **Map:** https://mkj69.github.io/multi-agent-survey-site/map.html

The repository stores links and metadata only (`data/items.json`). The site shows each work from
its original source: the PDF for papers, the post for X, the page for blogs, and the README for
GitHub and Hugging Face. Each item has a comment thread through GitHub Discussions.

The collection starts from the 1,000-odd hand-checked sources of the survey report and adds what a
crawl of OpenAlex, arXiv, GitHub, Hugging Face, Hacker News, Reddit and tracked X accounts finds.
It updates itself every day at 8:00 Chicago time: a GitHub Action (`crawler/daily.py`) looks for new
papers, repositories, posts and discussions and adds them. The update can be paused from the link at
the bottom of the site's list. The code that builds the collection is in `crawler/`.
