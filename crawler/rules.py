"""Keyword rules for relevance, categories and tags. Used by the daily job (no LLM) and as a
first pass before the LLM pass in the initial build."""
import json, os, re

I = re.I
LLM = r"(?:llms?|large language models?|language models?|gpt|claude|agentic)"
CAT = {
    "scale": [r"(?:agent|swarm)[- ]scaling", r"scaling (?:up )?(?:llm[- ]based |llm[- ]driven )?(?:multi[- ]?agent|agent (?:swarms?|teams?|systems?|count)|the number of agents|(?:ai |llm |language )?agents\b)",
              r"more agents is all you need", r"swarm scaling", r"agent swarms?", r"swarms? of (?:llm |ai |coding )?agents", r"(?:thousands?|hundreds?|10,?000|1,?000) (?:of )?(?:parallel |coding |ai |llm )?agents",
              r"parallel (?:coding |llm |ai )?agents", r"many-agent", r"science of scaling agent", r"number of agents", r"more llm calls", r"compound (?:ai|inference) systems?",
              r"effective team size", r"ringelmann", r"agent scaling", r"(?:llm|language[- ]model|ai|agent|coding) swarms?",
              r"\bswarms?\b.{0,40}(?:llms?|language models?|agents)", r"(?:\d[\d,]*|thousands?|hundreds?) (?:of )?(?:[\w-]+ )?(?:llm |ai |language[- ]model )?agents\b"],
    "orch": [r"orchestrat\w* .{0,30}agents|(?:agent|multi[- ]?agent) orchestrat", r"sub-?agents?", r"agent teams?", r"(?:lead|manager|supervisor|planner|orchestrator)[- ](?:agent|worker)s?",
             r"(?:coding|software(?: engineering)?) (?:agent )?(?:teams|swarms|fleets)", r"multi[- ]?agent (?:software|coding|code generation|programming)", r"hierarchical (?:multi-?)?agents?",
             r"agentic workflows?", r"\bchatdev\b", r"\bmetagpt\b", r"magentic-one", r"long-running (?:autonomous )?(?:coding )?agents?", r"agent (?:harness|scaffold)",
             r"multi[- ]?agent research system", r"don'?t build multi[- ]?agents"],
    "collab": [LLM + r"[- ](?:based |driven |powered )?multi[- ]?agent", r"multi[- ]?agent (?:llms?|large language models?|language models?)", r"multi[- ]?agent (?:debate|discussion|deliberation)",
               r"(?:llm|language model) (?:agents? )?debat", r"society of minds?", r"mixture[- ]of[- ]agents", r"communicative agents", r"role-?play\w* .{0,25}(?:agents|society)",
               r"why do multi[- ]?agent", r"multi[- ]?agent (?:collaboration|cooperation|coordination|reasoning|conversation)", r"(?:collaborat|coordinat)\w* (?:of |among |between )?(?:llm|language model|ai) agents",
               r"agentverse", r"\bautogen\b", r"\bcamel\b"],
    "society": [r"generative agents", r"agent societ(?:y|ies)", r"(?:llm|language model|generative|ai) agents? .{0,20}(?:social )?simulat", r"simulat\w* .{0,30}(?:with|using|by) (?:llms?|large language models?|generative agents)",
                r"emergent (?:communication|social|cooperation|collusion|norms?)", r"(?:llm|language model) agents? .{0,30}(?:cooperat|negotiat|bargain|games?|econom|markets?|auctions?)",
                r"silicon (?:samples?|subjects?|crowds?)", r"societ(?:y|ies) of (?:[\w-]+ )*agents", r"populations? of (?:llms?|language models?|(?:llm |ai )?agents)", r"artificial societ", r"agentic markets?", r"agent economy"],
    "risk": [r"multi[- ]?agent (?:risks?|safety|security|attacks?|threats?|vulnerabilit)", r"collu(?:de|des|sion|sive)", r"cascad\w* .{0,25}(?:agents?|multi[- ]?agent)", r"prompt infection",
             r"(?:attack|poison|jailbreak|inject)\w* .{0,30}multi[- ]?agent", r"(?:hallucination|error) (?:snowball|propagation)", r"malicious (?:ai )?swarms?", r"agent-to-agent (?:attacks?|threats?)",
             r"unsanctioned coordination", r"steganograph\w* .{0,30}agents"],
    "infra": [r"model context protocol", r"\bMCP\b", r"agent[- ]to[- ]agent protocol", r"\bA2A\b", r"agent (?:communication |interoperability )?protocols?", r"agent communication language",
              r"\bKQML\b", r"\bFIPA\b", r"\bcrewai\b", r"\blanggraph\b", r"multi[- ]?agent (?:framework|platform|library|toolkit|serving|infrastructure)", r"agent(?:ic)? (?:infrastructure|economics)",
              r"cost of (?:multi-?)?agents?", r"kv cache .{0,30}agents"],
    "found": [r"multi[- ]?agent reinforcement learning", r"\bMARL\b", r"swarm intelligence", r"swarm robotics", r"particle swarm", r"ant colony", r"\bboids\b", r"flocking",
              r"contract net", r"belief-desire-intention", r"\bBDI\b", r"collective intelligence", r"wisdom of (?:the )?crowds?", r"condorcet", r"society of mind", r"blackboard (?:system|architecture)",
              r"distributed (?:artificial intelligence|problem solving)", r"multi[- ]?agent systems?", r"amdahl", r"emergent tool use", r"markov games?"],
}
TAGS = {
    "agent-count scaling": r"number of agents|agent[- ]count|more agents|scaling (?:the )?(?:number|team)|team size|agent scaling|swarm scaling",
    "parallel agents": r"parallel",
    "speed vs capability": r"wall-?clock|latency|speed|faster",
    "large runs": r"thousands? of agents|1,?000|10,?000|hundreds of agents|swarm",
    "scaling laws": r"scaling laws?|power law|predictable",
    "test-time compute": r"test-time|inference(?:-time)? compute|best-of-n|more llm calls",
    "critique": r"critiqu|overvalu|rethink|fail|limits?\b|myth|not all you need|stop ",
    "benchmark": r"benchmark|bench\b|evaluation suite",
    "lead and subagents": r"sub-?agents?|orchestrat|lead agent|manager|supervisor",
    "coding agent teams": r"coding|software|code generation|programming|pull requests?",
    "workflows": r"workflows?",
    "context isolation": r"context (?:isolation|window|management)",
    "verification": r"verif|tests?\b|checker",
    "human oversight": r"human[- ](?:in|on)[- ]the[- ]loop|oversight|review",
    "harness design": r"harness|scaffold",
    "case study": r"case study|lessons|how we built|in practice",
    "debate": r"debat",
    "role-playing": r"role-?play|personas?",
    "voting and ensembles": r"vot(?:e|ing)|ensemble|majority|mixture[- ]of[- ]agents|self-consistency",
    "communication topology": r"topolog|communication (?:graph|structure|network)|sparse communication",
    "failure analysis": r"fail|taxonomy of (?:errors|failures)",
    "heterogeneous models": r"heterogene|divers",
    "trained coordination": r"reinforcement learning|\brl\b|train(?:ed|ing) (?:to )?(?:coordinat|cooperat|collaborat)",
    "generative agents": r"generative agents",
    "social simulation": r"simulat",
    "emergent communication": r"emergent (?:communication|language)",
    "cooperation and games": r"cooperat|game|dilemma|negotiat|bargain",
    "markets and economies": r"market|econom|auction|pricing",
    "norms and culture": r"norms?|cultur|conventions?",
    "collusion": r"collu",
    "error propagation": r"cascad|propagat|snowball",
    "security and injection": r"secur|attack|inject|poison|jailbreak|adversar",
    "unsanctioned coordination": r"unsanctioned|covert|steganograph|secret",
    "governance": r"governance|policy|regulat|accountab",
    "evaluation": r"evaluat|red[- ]team|audit",
    "protocols": r"protocol|\bMCP\b|\bA2A\b|\bACP\b|KQML|FIPA",
    "frameworks": r"framework|library|toolkit|platform|autogen|crewai|langgraph",
    "memory and shared state": r"memory|shared state|blackboard|database",
    "cost and economics": r"cost|token|econom|pric",
    "serving and systems": r"serving|kv cache|throughput|scheduling|system design",
    "observability": r"observab|tracing|monitor",
    "multi-agent systems": r"multi[- ]?agent systems?|contract net|blackboard|\bBDI\b",
    "MARL": r"reinforcement learning|\bMARL\b|markov games?",
    "swarm intelligence": r"swarm|ant colony|boids|flocking",
    "collective intelligence": r"collective intelligence|wisdom of (?:the )?crowds?|condorcet",
    "parallel computing limits": r"amdahl|gustafson|brooks",
    "organisation theory": r"organi[sz]ation|team|firm",
}
_TAX = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "taxonomy.json")))
TAG_CAT = _TAX["tags"]
# Patterns that also cover large neighbouring fields (classic MARL and robotics, swarm optimisation,
# generic "multi-agent systems") or are too broad on their own. A title match on these only marks the
# item as uncertain, so the LLM pass decides.
AMBIGUOUS = {r"multi[- ]?agent reinforcement learning", r"\bMARL\b", r"swarm intelligence", r"swarm robotics", r"particle swarm", r"ant colony", r"\bboids\b", r"flocking",
             r"collective intelligence", r"wisdom of (?:the )?crowds?", r"multi[- ]?agent systems?", r"\bBDI\b", r"markov games?", r"distributed (?:artificial intelligence|problem solving)",
             r"sub-?agents?", r"agent teams?", r"hierarchical (?:multi-?)?agents?", r"agentic workflows?", r"number of agents", r"parallel (?:coding |llm |ai )?agents", r"many-agent",
             r"multi[- ]?agent (?:collaboration|cooperation|coordination|reasoning|conversation)", r"\bMCP\b", r"\bA2A\b", r"agent (?:communication |interoperability )?protocols?",
             r"collu(?:de|des|sion|sive)", r"\bcamel\b", r"\bautogen\b", r"agent swarms?", r"emergent (?:communication|social|cooperation|collusion|norms?)", r"amdahl", r"flocking",
             r"multi[- ]?agent (?:framework|platform|library|toolkit|serving|infrastructure)", r"cascad\w* .{0,25}(?:agents?|multi[- ]?agent)", r"agent (?:harness|scaffold)",
             r"compound (?:ai|inference) systems?", r"multi[- ]?agent (?:risks?|safety|security|attacks?|threats?|vulnerabilit)", r"emergent tool use", r"blackboard (?:system|architecture)"}
_CAT = {c: [re.compile(p, I) for p in ps] for c, ps in CAT.items()}
_AMB = {c: [p in AMBIGUOUS for p in ps] for c, ps in CAT.items()}
_TAG = {t: re.compile(p, I) for t, p in TAGS.items()}


def score(title, text):
    """Return {cat: 2 if the title matches, 1 if only the body matches}."""
    out = {}
    if re.search(r"retract|corrigendum|erratum", title or "", I):
        return out
    for c, ps in _CAT.items():
        hit = [amb for p, amb in zip(ps, _AMB[c]) if p.search(title or "")]
        if hit and not all(hit):
            out[c] = 2
        elif hit or any(p.search(text or "") for p in ps):
            out[c] = 1
    return out


def tags_for(cats, title, text):
    blob = f"{title or ''} {text or ''}"
    tags = []
    for c in cats:
        for t in TAG_CAT[c]:
            if t in _TAG and _TAG[t].search(blob) and t not in tags:
                tags.append(t)
    return tags
