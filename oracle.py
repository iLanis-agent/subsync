#!/usr/bin/env python3
# Sub Sync oracle - mirrors engine.js with Fractions: times become Fraction seconds, retiming is a straight line through the anchors, rounding is floor(x + 1/2) on milliseconds.
import json, re, random, math
from fractions import Fraction as F

TERR = "the time must look like 0:01:05.200 (hours, minutes, seconds, optional milliseconds), up to 99:59:59.999"
FERR = "the frame rate must be a number from 1 to 120 with up to 3 decimals"

def tsec(t):
    t = t.strip() if isinstance(t, str) else ""
    m = re.fullmatch(r"(\d{1,2}):([0-5]\d):([0-5]\d)(?:[.,](\d{1,3}))?", t)
    if not m: raise ValueError(TERR)
    h, mi, s = int(m[1]), int(m[2]), int(m[3])
    frac = F(int(m[4]), 10 ** len(m[4])) if m[4] else F(0)
    return 3600 * h + 60 * mi + s + frac
def rnd(x): return math.floor(x * 1000 + F(1, 2))  # milliseconds, half up
def clock(ms):
    h, rest = divmod(ms, 3600000); mi, rest = divmod(rest, 60000); s, f = divmod(rest, 1000)
    return f"{h}:{mi:02d}:{s:02d}.{f:03d}"
def dec(fr, places):
    v = math.floor(fr * 10 ** places + F(1, 2))
    ip, fp = divmod(v, 10 ** places)
    fs = str(fp).zfill(places).rstrip("0")
    return f"{ip}.{fs}" if fs else str(ip)
def move(dms):
    if dms == 0: return "at the same time"
    a = abs(dms)
    word = "second" if a == 1000 else "seconds"
    return f"{dec(F(a, 1000), 3)} {word} {'earlier' if dms < 0 else 'later'}"
def fps(t):
    t = t.strip() if isinstance(t, str) else ""
    m = re.fullmatch(r"(\d{1,3})(?:\.(\d{1,3}))?", t)
    if not m: raise ValueError(FERR)
    v = F(m[1]) + (F(int(m[2]), 10 ** len(m[2])) if m[2] else 0)
    if not 1 <= v <= 120: raise ValueError(FERR)
    return v
def land(sec):
    ms = rnd(sec)
    if ms < 0: raise ValueError("that line would land before 0:00:00.000")
    if ms > 359999999: raise ValueError("that line would land after 99:59:59.999")
    return ms

def shift(a, b):
    x, y = tsec(a), tsec(b)
    if x == y: return "Both times are the same, so the shift is 0 seconds. Nothing moves."
    return f"A line shown at {clock(rnd(x))} should appear at {clock(rnd(y))}. Moving every line {move(rnd(y) - rnd(x))} does that. It fixes the whole file only if every line is off by the same amount."
def stretch(a1, b1, a2, b2, q):
    x1, y1, x2, y2, t = tsec(a1), tsec(b1), tsec(a2), tsec(b2), tsec(q)
    if x2 <= x1: raise ValueError("the last line must be shown later than the first line")
    if y2 <= y1: raise ValueError("the last line must be wanted later than the first line")
    slope = (y2 - y1) / (x2 - x1)
    ms = land(y1 + (t - x1) * slope)
    return f"The two anchors give a scale factor of {dec(slope, 5)} on the time between them. A line shown at {clock(rnd(t))} should then appear at {clock(ms)}, {move(ms - rnd(t))}. This assumes the drift grows steadily from the first line to the last."
def fpsf(s, v, q):
    s, v, t = fps(s), fps(v), tsec(q)
    st = dec(s, 3).rstrip("0").rstrip(".") if False else (str(s.numerator) if s.denominator == 1 else dec(s, 3))
    vt = str(v.numerator) if v.denominator == 1 else dec(v, 3)
    if s == v: return f"Both frame rates are {st} fps, so the scale factor is 1 and no time changes."
    ms = land(t * s / v)
    return f"Subtitles timed at {st} fps on a video at {vt} fps: multiply every time by {dec(s / v, 5)}. A line shown at {clock(rnd(t))} becomes {clock(ms)}, {move(ms - rnd(t))}."

FNS = {"shiftTruth": shift, "stretchTruth": stretch, "fpsTruth": fpsf}

def cases():
    c = []
    T = ["0:00:00", "0:00:00.000", "0:01:05.200", "0:01:07,700", "1:00:00", "10:20:30.5", "0:59:59.999", "99:59:59.999", "99:59:59", "0:00:01", "0:00:00.001", "2:03:04.05", " 0:10:00 "]
    bad = ["", "x", "1:5:00", "0:60:00", "0:00:60", "100:00:00", "0:00", "0:00:00.", "0:00:00.1234", "-0:01:00", "0:00:00.x", "0:00:00 5"]
    for a in T[:9]:
        for b in T[:9]: c.append(("shiftTruth", [a, b]))
    for b in bad: c += [("shiftTruth", [b, "0:01:00"]), ("shiftTruth", ["0:01:00", b])]
    for a, b in [("0:00:05", "0:00:04"), ("0:00:05", "0:00:06"), ("0:00:05.5", "0:00:05.5")]: c.append(("shiftTruth", [a, b]))
    base = ["0:00:10.000", "0:00:10.500", "1:40:00.000", "1:44:10.000", "0:50:00.000"]
    c.append(("stretchTruth", base))
    for q in T: c.append(("stretchTruth", base[:4] + [q]))
    for i in range(5):
        for b in bad[:6]:
            a = list(base); a[i] = b; c.append(("stretchTruth", a))
    c += [("stretchTruth", ["0:10:00", "0:10:00", "0:10:00", "0:20:00", "0:15:00"]),
          ("stretchTruth", ["0:20:00", "0:10:00", "0:10:00", "0:20:00", "0:15:00"]),
          ("stretchTruth", ["0:10:00", "0:20:00", "0:20:00", "0:20:00", "0:15:00"]),
          ("stretchTruth", ["0:10:00", "0:20:00", "0:30:00", "0:10:00", "0:15:00"]),
          ("stretchTruth", ["0:10:00", "0:05:00", "0:20:00", "0:06:00", "0:00:00"]),
          ("stretchTruth", ["0:10:00", "0:05:00", "0:20:00", "0:06:00", "99:59:59.999"]),
          ("stretchTruth", ["0:00:00", "0:00:00", "1:00:00", "2:00:00", "99:59:59.999"]),
          ("stretchTruth", ["0:00:00", "0:00:00", "1:00:00", "1:00:00", "0:30:00"]),
          ("stretchTruth", ["0:00:00", "0:00:00.001", "0:00:00.003", "0:00:00.004", "0:00:00.002"])]
    R = ["25", "23.976", "24", "29.97", "30", "23.98", "1", "120", "60.5", "25.000", " 24 "]
    for s in R:
        for v in R[:5]: c.append(("fpsTruth", [s, v, "0:50:00"]))
    for q in T: c.append(("fpsTruth", ["25", "23.976", q]))
    for b in ["", "0", "0.999", "120.001", "121", "1000", "x", "24.", "24.1234", "-24", ".5"]:
        c += [("fpsTruth", [b, "24", "0:50:00"]), ("fpsTruth", ["24", b, "0:50:00"])]
    c.append(("fpsTruth", ["120", "1", "0:50:00"]))
    c.append(("fpsTruth", ["120", "1", "0:00:00.001"]))
    r = random.Random(4120)
    def rt():
        return clock(r.randint(0, 359999999)) if r.random() < .3 else clock(r.randint(0, 7200000))
    for _ in range(25):
        x1 = r.randint(0, 3000000); x2 = x1 + r.randint(1, 6000000); y1 = r.randint(0, 3000000); y2 = y1 + r.randint(1, 6000000)
        c.append(("stretchTruth", [clock(x1), clock(y1), clock(x2), clock(y2), clock(r.randint(0, 7200000))]))
    for _ in range(25): c.append(("shiftTruth", [rt(), rt()]))
    for _ in range(25): c.append(("fpsTruth", [str(r.randint(1, 120)), str(r.choice([23.976, 24, 25, 29.97, 30])), clock(r.randint(0, 7200000))]))
    return c

out = []
for fn, args in cases():
    try: exp = FNS[fn](*args)
    except ValueError as e: exp = "ERR:" + str(e)
    out.append({"fn": fn, "args": args, "expected": exp})
with open("expected.json", "w") as f:
    json.dump(out, f, indent=1); f.write("\n")
print(len(out), "cases written")
