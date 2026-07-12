"""
Faithfulness check — does the answer actually follow from the retrieved text?

A lightweight, dependency-free grounding check in the spirit of RAGAS and the
POLIS-Bench "false success" warning from the roadmap. The answer is split into
sentences; each is scored for lexical support against the retrieved context
(token overlap, with numbers required to appear in the context so a fabricated
figure is penalised). The overall score is the fraction of supported sentences.

This is a v1 heuristic, not an NLI model — it reliably catches invented
figures and wholly-unsupported claims, which is the main risk. Swap in an
LLM-judge or NLI scorer later behind the same function signature.
"""
import re
from typing import List, Tuple

_STOP = set("a an the of for to in on and or is are was were be been being this that "
            "you your with at by as from will can may shall under their its it".split())
_NUM = re.compile(r"\d[\d,]*")


def _tokens(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9₹]+", text.lower()) if w not in _STOP}


def _sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text or "")
    return [p.strip() for p in parts if len(p.strip()) > 12]


def _nums(text: str) -> set:
    return {n.replace(",", "") for n in _NUM.findall(text or "")}


def score(answer: str, context: str, threshold: float = 0.45) -> Tuple[float, bool, List[str]]:
    """Return (faithfulness_score 0-1, is_grounded, unsupported_sentences)."""
    sents = _sentences(answer)
    if not sents:
        return 1.0, True, []
    ctx_tok = _tokens(context)
    ctx_num = _nums(context)
    supported, unsupported = 0, []
    for s in sents:
        st = _tokens(s)
        if not st:
            supported += 1
            continue
        overlap = len(st & ctx_tok) / len(st)
        snums = _nums(s)
        if snums and not snums.issubset(ctx_num):
            overlap *= 0.3  # penalise invented numbers
        if overlap >= threshold:
            supported += 1
        else:
            unsupported.append(s)
    sc = round(supported / len(sents), 3)
    return sc, sc >= 0.5, unsupported


def label(sc: float) -> str:
    if sc >= 0.75:
        return "High"
    if sc >= 0.5:
        return "Medium"
    return "Low"
