#!/usr/bin/env python3
"""Offline orchestration self-test — injects a fake call_model, so it runs the whole flow with no
network and no secrets (proves the escalation/scoring/honesty logic didn't regress; it does NOT and
cannot test non-deterministic model answers)."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "lib"))
import validate_core as vc

PANEL = [
    {"key": "gpt5",   "model": "openai/gpt-5",          "label": "GPT-5 (OpenAI)"},
    {"key": "gemini", "model": "google/gemini-2.5-pro", "label": "Gemini 2.5 Pro (Google)"},
    {"key": "grok",   "model": "x-ai/grok-4.6",         "label": "Grok 4.6 (xAI)",
     "fallback": {"model": "deepseek/deepseek-r1", "label": "DeepSeek R1 (DeepSeek)"}},
]
WEB = {"key": "perplexity", "model": "perplexity/sonar", "label": "Perplexity Sonar"}

def review(stance, top="none"):
    return "STRENGTHS\n- s\nRISKS\n- r\nALTERNATIVES\n- a\nSTANCE: %s\nTOP_RISK: %s" % (stance, top)

def fake(script):
    """script: {model_id: (ok, text) | 'RAISE'}. Returns a call_model with matching signature."""
    def cm(model, system, user, api_key, max_tokens=6000, timeout=220):
        v = script.get(model, (True, review("concur")))
        if v == "RAISE":
            return {"ok": False, "text": "", "finish": None, "error": "simulated failure"}
        ok, text = v
        return {"ok": ok, "text": text, "finish": "stop", "error": None if ok else "err"}
    return cm

P, F = 0, 0
def ok(name, cond):
    global P, F
    print(("  PASS · " if cond else "  FAIL · ") + name);
    globals().__setitem__("P", P + (1 if cond else 0)); globals().__setitem__("F", F + (0 if cond else 1))

C = "some plan content"

# A — full consensus → HIGH, no disagreements, web skipped
r = vc.run_validation("subj", C, PANEL, "k", call_model=fake({
    "openai/gpt-5": (True, review("concur")), "google/gemini-2.5-pro": (True, review("concur")),
    "x-ai/grok-4.6": (True, review("concur"))}), web=False, web_model=WEB)
ok("A: all concur → HIGH", r["confidence"] == "HIGH")
ok("A: no disagreements", r["disagreements"] == [])
ok("A: web skipped when web=False", r["web"] is None)
ok("A: all 3 reviewers responded", sum(1 for x in r["reviews"] if x["ok"]) == 3)

# B — a dissent → LOW, disagreements surfaced
r = vc.run_validation("subj", C, PANEL, "k", call_model=fake({
    "openai/gpt-5": (True, review("concur")), "google/gemini-2.5-pro": (True, review("concerns")),
    "x-ai/grok-4.6": (True, review("dissent", "breaks under load"))}))
ok("B: any dissent → LOW", r["confidence"] == "LOW")
ok("B: disagreements listed (mixed stances)", len(r["disagreements"]) == 3)

# C — one model fails → marked FAILED, others still score
r = vc.run_validation("subj", C, PANEL, "k", call_model=fake({
    "openai/gpt-5": (True, review("concur")), "google/gemini-2.5-pro": "RAISE",
    "x-ai/grok-4.6": (True, review("concur"))}))
gem = [x for x in r["reviews"] if x["key"] == "gemini"][0]
ok("C: failed model recorded ok=False", gem["ok"] is False)
ok("C: 2 concurring responders → HIGH", r["confidence"] == "HIGH")

# D — only one responds → 'unknown' (grok's fallback must ALSO fail for its slot to be down)
r = vc.run_validation("subj", C, PANEL, "k", call_model=fake({
    "openai/gpt-5": (True, review("concur")), "google/gemini-2.5-pro": "RAISE",
    "x-ai/grok-4.6": "RAISE", "deepseek/deepseek-r1": "RAISE"}))
ok("D: <2 responders → unknown", r["confidence"] == "unknown")

# G — primary (grok) down, fallback (deepseek) answers → slot responds, marked (fallback)
r = vc.run_validation("subj", C, PANEL, "k", call_model=fake({
    "openai/gpt-5": (True, review("concur")), "google/gemini-2.5-pro": (True, review("concur")),
    "x-ai/grok-4.6": "RAISE", "deepseek/deepseek-r1": (True, review("concerns", "slow"))}))
g = [x for x in r["reviews"] if x["key"] == "grok"][0]
ok("G: fallback answered the slot", g["ok"] and g["fell_back"])
ok("G: fallback labelled", "fallback" in g["label"] and "DeepSeek" in g["label"])
ok("G: mixed concur+concerns → MEDIUM", r["confidence"] == "MEDIUM")

# H — primary AND fallback both down → slot FAILED with a combined error
r = vc.run_validation("subj", C, PANEL, "k", call_model=fake({
    "openai/gpt-5": (True, review("concur")), "google/gemini-2.5-pro": (True, review("concur")),
    "x-ai/grok-4.6": "RAISE", "deepseek/deepseek-r1": "RAISE"}))
g = [x for x in r["reviews"] if x["key"] == "grok"][0]
ok("H: slot FAILED when both down", g["ok"] is False)
ok("H: error names primary + fallback", "primary" in g["error"] and "fallback" in g["error"])

# E — web tier runs when web=True
r = vc.run_validation("subj", C, PANEL, "k", call_model=fake({
    "perplexity/sonar": (True, "checked: all claims hold")}), web=True, web_model=WEB)
ok("E: web fact-check included", r["web"] is not None and r["web"]["ok"])

# F — render_doc carries the honesty caveat + required sections + FAILED marker
r = vc.run_validation("subj", C, PANEL, "k", call_model=fake({"google/gemini-2.5-pro": "RAISE"}))
doc = vc.render_doc(r, "topic", "2026-01-01T00-00Z", "inline")
ok("F: doc has agreement-not-correctness caveat", "agreement, not correctness" in doc)
ok("F: doc has Panel + Disagreements + Findings", all(s in doc for s in ("## Panel", "## Disagreements", "## Findings by model")))
ok("F: doc marks the failed model", "FAILED" in doc)
ok("F: parse_stance reads STANCE line", vc.parse_stance(review("dissent", "x")) == ("dissent", "x"))

# I — a responder returns an UNPARSEABLE stance → non-responding (not a silent 'concerns')
r = vc.run_validation("subj", C, PANEL, "k", call_model=fake({
    "openai/gpt-5": (True, review("concur")),
    "google/gemini-2.5-pro": (True, "STRENGTHS\n- x\nRISKS\n- y\n(no stance line at all)"),
    "x-ai/grok-4.6": (True, review("concur"))}))
gem = [x for x in r["reviews"] if x["key"] == "gemini"][0]
ok("I: unparseable stance → ok False", gem["ok"] is False)
ok("I: error flags unparseable", "unparseable" in (gem["error"] or ""))
ok("I: two parseable concur → HIGH", r["confidence"] == "HIGH")

# J — HONESTY REGRESSION: 1 parseable + 2 unparseable → unknown (old parser faked 'concerns'→HIGH)
r = vc.run_validation("subj", C, PANEL, "k", call_model=fake({
    "openai/gpt-5": (True, review("concur")),
    "google/gemini-2.5-pro": (True, "prose only, no anchored stance"),
    "x-ai/grok-4.6": (True, "prose only, no anchored stance")}))
ok("J: unparseable no longer inflates the panel → unknown", r["confidence"] == "unknown")

# K — a stance mentioned ONLY inside a code fence is ignored (parses to non-responding)
fenced = "STRENGTHS\n- x\n```\nSTANCE: concur\n```\nRISKS\n- y"
ok("K: fenced stance ignored", vc.parse_stance(fenced)[0] is None)

# L — doc shows stance counts + the resolved-model manifest column
r = vc.run_validation("subj", C, PANEL, "k", call_model=fake({
    "openai/gpt-5": (True, review("concur")), "google/gemini-2.5-pro": (True, review("concerns")),
    "x-ai/grok-4.6": (True, review("concur"))}))
doc = vc.render_doc(r, "t", "2026-01-01T00-00Z", "inline")
ok("L: doc has stance counts", "**Stances:**" in doc)
ok("L: doc has resolved-model column", "Resolved model" in doc)

# M — critic prompt carries the injection guardrail; MEDIUM wording no longer claims 'sound'
ok("M: CRITIC_SYSTEM warns of untrusted content", "UNTRUSTED" in vc.CRITIC_SYSTEM)
ok("M: MEDIUM wording dropped 'sound'", "sound" not in vc.compute_confidence(
    [{"ok": True, "stance": "concur"}, {"ok": True, "stance": "concerns"}])[1])

print("\n== selftest: %d passed, %d failed ==" % (P, F))
sys.exit(0 if F == 0 else 1)
