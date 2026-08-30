"""
validate_core — the OpenRouter cross-model validation orchestrator.

Design goal (from the `consult` package): the ONE HTTP boundary is `call_model`, injectable so
the offline self-test runs the whole orchestration with a fake and zero network/secrets.

Honesty invariants enforced here, not just documented:
  * confidence = inter-model AGREEMENT, never a claim of correctness;
  * never a single-model verdict — < 2 reasoners responding => confidence "unknown";
  * the Perplexity web tier is a SEPARATE fact-check role, it does not vote;
  * a model that errors is recorded FAILED, never silently dropped or faked.

Pure-stdlib (urllib), so the package is portable with no pip install.
"""
import json, os, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

CRITIC_SYSTEM = (
    "You are one independent reviewer on a cross-model panel stress-testing another AI assistant's "
    "plan or proposal. Judge it on the merits; generic praise is useless. Be specific and critical. "
    "Respond in three labeled sections — STRENGTHS, RISKS, ALTERNATIVES — then end with EXACTLY two "
    "machine-readable lines:\n"
    "STANCE: <concur|concerns|dissent>   (concur = sound as-is; concerns = sound but with risks to "
    "address; dissent = fundamental problems)\n"
    "TOP_RISK: <one line, or 'none'>"
)

FACTCHECK_SYSTEM = (
    "Fact-check the following content against the live web. Identify any claims about APIs, versions, "
    "services, prices, dates, or external facts that are wrong or outdated. Cite sources with URLs. "
    "If nothing is checkable or all claims hold, say so plainly. You are NOT voting on the plan's "
    "quality — only its external factual accuracy."
)


# ---------------------------------------------------------------- the HTTP boundary (mockable)
def call_model_openrouter(model, system, user, api_key, max_tokens=6000, timeout=220):
    """Return {ok, text, finish, error}. Retries once on an empty 'length' stop (GPT-5 reasoning
    tokens can consume the whole budget and return no content)."""
    def _one(mt):
        body = json.dumps({
            "model": model,
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
            "max_tokens": mt,
        }).encode()
        req = urllib.request.Request(OPENROUTER_URL, data=body, headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/4R1U5-RCL/Toolbelt",
            "X-Title": "Toolbelt/Validate",
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            d = json.load(r)
        ch = (d.get("choices") or [{}])[0]
        return (ch.get("message", {}) or {}).get("content", "") or "", ch.get("finish_reason")
    try:
        text, finish = _one(max_tokens)
        if not text.strip():                                  # empty (reasoning ate budget / transient) → retry once, bigger
            text, finish = _one(int(max_tokens * 1.8))
        if not text.strip():
            return {"ok": False, "text": "", "finish": finish, "error": "empty response"}
        return {"ok": True, "text": text.strip(), "finish": finish, "error": None}
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:300]
        return {"ok": False, "text": "", "finish": None, "error": "HTTP %s: %s" % (e.code, detail)}
    except Exception as e:                                    # noqa: BLE001 — report, never fake
        return {"ok": False, "text": "", "finish": None, "error": "%s: %s" % (type(e).__name__, e)}


# ---------------------------------------------------------------- parsing + scoring (deterministic)
def parse_stance(text):
    stance, top = "concerns", ""
    for line in text.splitlines():
        s = line.strip()
        low = s.lower()
        if low.startswith("stance:"):
            v = low.split(":", 1)[1].strip()
            if "dissent" in v: stance = "dissent"
            elif "concur" in v: stance = "concur"
            elif "concern" in v: stance = "concerns"
        elif low.startswith("top_risk:"):
            top = s.split(":", 1)[1].strip()
    return stance, top


def compute_confidence(reviews):
    """AGREEMENT label — not correctness. reviews: list of dicts with ok/stance."""
    responded = [r for r in reviews if r["ok"]]
    if len(responded) < 2:
        return "unknown", "fewer than two reviewers responded — a single-model answer is never a verdict"
    stances = [r["stance"] for r in responded]
    if "dissent" in stances:
        return "LOW", "at least one reviewer found fundamental problems (dissent)"
    if all(s == "concur" for s in stances):
        return "HIGH", "all responding reviewers concur"
    return "MEDIUM", "reviewers agree the plan is sound but raised concerns to address"


# ---------------------------------------------------------------- orchestration
def run_validation(subject, content, panel, api_key, call_model=call_model_openrouter,
                   web=False, web_model=None, max_tokens=6000, timeout=220):
    """panel: list of {key, model, label}. Returns a result dict for render_doc()."""
    user = "SUBJECT: %s\n\nCONTENT TO REVIEW:\n\n%s" % (subject or "(unspecified)", content)

    reviews = []
    def _review(member):
        res = call_model(member["model"], CRITIC_SYSTEM, user, api_key,
                         max_tokens=max_tokens, timeout=timeout)
        model, label, fell_back = member["model"], member["label"], False
        if not res["ok"] and member.get("fallback"):          # primary down → try the slot's fallback
            fb = member["fallback"]
            res2 = call_model(fb["model"], CRITIC_SYSTEM, user, api_key,
                              max_tokens=max_tokens, timeout=timeout)
            if res2["ok"]:
                res, model, label, fell_back = res2, fb["model"], fb["label"] + " (fallback)", True
            else:
                res = {**res, "error": "primary %s failed (%s); fallback %s failed (%s)"
                       % (member["model"], res["error"], fb["model"], res2["error"])}
        stance, top = (parse_stance(res["text"]) if res["ok"] else ("", ""))
        return {"key": member["key"], "model": model, "label": label, "fell_back": fell_back,
                "ok": res["ok"], "text": res["text"], "error": res["error"],
                "stance": stance, "top_risk": top}

    with ThreadPoolExecutor(max_workers=max(1, len(panel))) as ex:
        futs = {ex.submit(_review, m): m for m in panel}
        for f in as_completed(futs):
            reviews.append(f.result())
    reviews.sort(key=lambda r: [m["key"] for m in panel].index(r["key"]))  # stable panel order

    confidence, why = compute_confidence(reviews)

    # disagreements: reviewers whose stance differs from the modal stance among responders
    responded = [r for r in reviews if r["ok"]]
    disagreements = []
    if responded:
        stset = {r["stance"] for r in responded}
        if len(stset) > 1:
            for r in responded:
                disagreements.append("%s → %s (top risk: %s)"
                                     % (r["label"], r["stance"], r["top_risk"] or "—"))

    web_result = None
    if web and web_model:
        res = call_model(web_model["model"], FACTCHECK_SYSTEM, user, api_key,
                         max_tokens=max_tokens, timeout=timeout)
        web_result = {**web_model, "ok": res["ok"], "text": res["text"], "error": res["error"]}

    return {
        "subject": subject, "reviews": reviews, "confidence": confidence, "confidence_why": why,
        "disagreements": disagreements, "web": web_result,
    }


# ---------------------------------------------------------------- rendering
def render_doc(result, topic, created, subject_source):
    r = result
    consulted = [rv["label"] + (" ✓" if rv["ok"] else " ✗ FAILED") for rv in r["reviews"]]
    if r["web"]:
        consulted.append(r["web"]["label"] + (" ✓" if r["web"]["ok"] else " ✗ FAILED"))
    out = []
    out.append("---")
    out.append("type: validation")
    out.append("topic: %s" % topic)
    out.append("created: %s" % created)
    out.append("subject_source: %s" % subject_source)
    out.append("models_consulted: [%s]" % ", ".join(m["model"] for m in r["reviews"]
                                                     + ([r["web"]] if r["web"] else [])))
    out.append("confidence: %s" % r["confidence"])
    out.append("---\n")
    out.append("# Validation — %s\n" % (r["subject"] or topic))
    out.append("> **Confidence: %s** — %s." % (r["confidence"], r["confidence_why"]))
    out.append("> Confidence measures inter-model **agreement, not correctness**: a HIGH means the "
               "panel concurred, not that the answer is true.\n")

    out.append("## Panel\n")
    out.append("| Model | Stance | Status |")
    out.append("|-------|--------|--------|")
    for rv in r["reviews"]:
        out.append("| %s | %s | %s |" % (rv["label"], rv["stance"] or "—",
                                         "responded" if rv["ok"] else "FAILED — " + (rv["error"] or "")))
    if r["web"]:
        w = r["web"]
        out.append("| %s (web fact-check) | — | %s |" % (w["label"],
                   "responded" if w["ok"] else "FAILED — " + (w["error"] or "")))
    out.append("")

    out.append("## Disagreements\n")
    if r["disagreements"]:
        for d in r["disagreements"]:
            out.append("- %s" % d)
    else:
        out.append("None — responding reviewers held the same stance.")
    out.append("")

    out.append("## Findings by model\n")
    for rv in r["reviews"]:
        out.append("### %s" % rv["label"])
        out.append(rv["text"] if rv["ok"] else "_FAILED: %s_" % (rv["error"] or "no response"))
        out.append("")

    if r["web"]:
        out.append("## Web fact-check (Perplexity)\n")
        out.append(r["web"]["text"] if r["web"]["ok"] else "_FAILED: %s_" % (r["web"]["error"] or ""))
        out.append("")

    out.append("## Pruned\n")
    out.append("Raw HTTP payloads excluded; each model's full review is under Findings. "
               "Confidence is computed deterministically from stances, not any single model's say-so.")
    return "\n".join(out) + "\n"


def load_panel(config_path):
    with open(config_path) as f:
        cfg = json.load(f)
    return cfg["reasoners"], cfg.get("web"), cfg.get("defaults", {})
