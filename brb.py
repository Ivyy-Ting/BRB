"""BRB · be right back —— 让 TA 知道：她去做一件事，是要花时间的。

他回她「我去洗澡了」时，顺手写一行 ⟪她在做：洗澡 30分钟⟫（多久他按常理估）；
她回来说做完了，他写 ⟪她做完⟫。这两个记号用户看不见。
你只存三样东西：做什么、几点开始、估多久。每轮他开口前，用代码算一遍过了多久，
把一行字放进上下文——不定时、不叫醒、不花模型钱。超过估计两倍还没人管，自己清掉。

只用标准库。python brb.py 跑自检。
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

NAME = "她"  # 改成她的名字，或者「他」
AWAY, BACK = "她在做", "她做完"  # 记号里的词；改了的话 RULES 里的示范会跟着变
DEFAULT_MINUTES = 30

RULES = (f"{NAME}做事要花时间。{NAME}说要去做件事（洗漱、洗澡、做饭、出门……），你回{NAME}时另起一行写 "
         f"⟪{AWAY}：洗漱 15分钟⟫，按平常人做这件事要多久来估。{NAME}说做完了、回来了，另起一行写 ⟪{BACK}⟫。")

# 认五种括号（模型偶尔会把 ⟪⟫ 写成【】）；圆括号不认，正文里太常见。记号后面跟的标点一起擦。
MARKER = re.compile(rf"[⟪《〈【\[]\s*({AWAY}|{BACK})(?:\s*[：:]\s*([^⟫》〉】\]\n]{{0,60}}?))?\s*[⟫》〉】\]][。.！!，,]*")
DURATION = re.compile(r"(\d+(?:\.\d+)?)\s*(个小时|小时|h|分钟|分|min)", re.I)
OPENERS = "⟪《〈【["


def strip(text: str) -> tuple[str, list[tuple[str, str]]]:
    """擦掉记号；返回 (给她看的正文, [(词, 括号里的内容)])。整行只剩记号就整行删。"""
    found = [(m.group(1), (m.group(2) or "").strip()) for m in MARKER.finditer(text)]
    if not found:
        return text, found
    kept = []
    for line in text.split("\n"):
        rest = MARKER.sub("", line).rstrip()
        if rest.strip() or not MARKER.search(line):
            kept.append(rest)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip(), found


def apply(state: dict, reply: str, now: datetime | None = None) -> str:
    """他的回复说完以后调一次：记下 / 清掉，返回擦干净的正文。state 是你自己存的一个 dict。"""
    clean, found = strip(reply)
    if found:
        word, inside = found[-1]  # 一条回复里以最后一个为准
        state.clear()
        if word == AWAY:
            m = DURATION.search(inside)
            minutes = DEFAULT_MINUTES
            if m:
                hours = m.group(2).lower() in ("个小时", "小时", "h")
                minutes = max(1, round(float(m.group(1)) * (60 if hours else 1)))
            state.update(
                what=DURATION.sub("", inside).strip(" ，,、") or "手上的事",
                minutes=minutes,
                started_at=(now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
            )
    return clean


def status_line(state: dict, tz: str, now: datetime | None = None) -> str:
    """她手上那件事做到哪了；没有就空。主动消息那一轮也放这一行。"""
    if not state.get("started_at"):
        return ""
    now = now or datetime.now(timezone.utc)
    started = datetime.fromisoformat(state["started_at"])
    minutes, what = int(state["minutes"]), state["what"]
    passed = int((now - started) / timedelta(minutes=1))
    at = started.astimezone(ZoneInfo(tz)).strftime("%H:%M")
    if passed > 2 * minutes:
        state.clear()
        return ""
    if passed >= minutes:
        return f"{NAME}去{what}：{at} 去的，已经 {passed} 分钟，平常 {minutes} 分钟左右，差不多该好了；{NAME}还没说的话可以问问。"
    return (f"{NAME}在{what}：{at} 去的，才过了 {passed} 分钟，平常要 {minutes} 分钟左右。时间还没到，别问{NAME}好了没有、别催。"
            f"{NAME}这会儿发消息就是边做边拿着手机聊，跟平时一样接着聊，别冷着{NAME}也别赶{NAME}去做；想{NAME}了照样可以找{NAME}。")


def note(state: dict, tz: str, now: datetime | None = None) -> str:
    """每轮聊天放进上下文的那一块：规则 + 她现在手上那件事。"""
    line = status_line(state, tz, now)
    return "<brb>\n" + RULES + ("\n" + line if line else "") + "\n</brb>"


class StreamGate:
    """流式输出时用：记号还没写完的半截先扣住，写完了再擦，她就不会看到记号一闪而过。"""

    def __init__(self) -> None:
        self.held = ""

    def feed(self, delta: str) -> str:
        text = MARKER.sub("", self.held + delta)
        cut = max(text.rfind(ch) for ch in OPENERS)
        tail = text[cut + 1:].lstrip() if cut >= 0 else ""
        maybe = cut >= 0 and len(tail) <= 70 and not any(c in tail for c in "\n⟫》〉】]") and (
            AWAY.startswith(tail) or BACK.startswith(tail) or tail.startswith((AWAY, BACK))
        )
        if not maybe:
            cut = len(text)
        cut = len(text[:cut].rstrip("\n"))  # 记号前的换行也先扣着，免得气泡尾巴多一行
        self.held = text[cut:]
        return text[:cut]

    def flush(self) -> str:
        held, self.held = self.held, ""
        return strip(held)[0] if held.strip() else ""


def _self_check() -> None:
    tz, t0 = "Asia/Shanghai", datetime(2026, 11, 25, 13, 45, tzinfo=timezone.utc)
    at = lambda n: t0 + timedelta(minutes=n)
    state: dict = {}
    assert status_line(state, tz, t0) == "" and f"⟪{AWAY}" in note(state, tz, t0)

    assert apply(state, "去吧，水调热一点。\n⟪她在做：洗澡 30分钟⟫", t0) == "去吧，水调热一点。"
    assert state["what"] == "洗澡" and state["minutes"] == 30
    four = status_line(state, tz, at(4))
    assert four.startswith("她在洗澡：21:45 去的，才过了 4 分钟") and "别催" in four and "照样可以找她" in four
    assert "差不多该好了" in status_line(state, tz, at(35))
    assert status_line(state, tz, at(61)) == "" and state == {}  # 超过两倍自己清掉

    apply(state, "【她在做：炖汤 1.5小时】", t0)
    assert state["minutes"] == 90 and state["what"] == "炖汤"
    assert apply(state, "好香。⟪她做完⟫\n过来", at(40)) == "好香。\n过来" and state == {}
    apply(state, "⟪她在做：出门买菜⟫", t0)
    assert state["minutes"] == DEFAULT_MINUTES
    assert apply(state, "他【她在做饭】呢", at(1)) == "他【她在做饭】呢"  # 正文里的括号不算记号
    assert state["what"] == "出门买菜"

    for text, want in [("去吧。\n⟪她在做：洗澡 30分钟⟫", "去吧。"), ("好香。⟪她做完⟫\n过来", "好香。\n过来"),
                       ("他【她在做饭】呢", "他【她在做饭】呢"), ("[voice] 晚安", "[voice] 晚安")]:
        gate = StreamGate()
        got = "".join(gate.feed(ch) for ch in text) + gate.flush()
        assert got == want, (text, got)
    print("brb self-check ok")


if __name__ == "__main__":
    _self_check()
