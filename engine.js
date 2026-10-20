// Sub Sync engine: subtitle retiming arithmetic. A fixed shift, a two anchor stretch, and a frame rate change. Exact BigInt milliseconds.
var _TERR = "the time must look like 0:01:05.200 (hours, minutes, seconds, optional milliseconds), up to 99:59:59.999";
var _MAXMS = 359999999n;
function _time(t) {
  var m = /^([0-9]{1,2}):([0-5][0-9]):([0-5][0-9])(?:[.,]([0-9]{1,3}))?$/.exec(typeof t === "string" ? t.trim() : "");
  if (!m) throw new Error(_TERR);
  var frac = (m[4] || "").padEnd(3, "0");
  return BigInt(m[1]) * 3600000n + BigInt(m[2]) * 60000n + BigInt(m[3]) * 1000n + BigInt(frac);
}
function _fmt(ms) {
  var h = ms / 3600000n, mi = (ms / 60000n) % 60n, s = (ms / 1000n) % 60n, f = ms % 1000n;
  return h + ":" + String(mi).padStart(2, "0") + ":" + String(s).padStart(2, "0") + "." + String(f).padStart(3, "0");
}
function _floorDiv(n, d) { return n >= 0n ? n / d : -((-n + d - 1n) / d); }
function _halfUp(n, d) { return _floorDiv(2n * n + d, 2n * d); }
function _secs(ms) { // positive ms as seconds, trailing zeros dropped
  var s = String(ms / 1000n), f = String(ms % 1000n).padStart(3, "0").replace(/0+$/, "");
  return f ? s + "." + f : s;
}
function _move(diff) { // signed ms to a phrase
  if (diff === 0n) return "at the same time";
  var a = diff < 0n ? -diff : diff;
  return _secs(a) + (a === 1000n ? " second " : " seconds ") + (diff < 0n ? "earlier" : "later");
}
function _fps(t) {
  var m = /^([0-9]{1,3})(?:\.([0-9]{1,3}))?$/.exec(typeof t === "string" ? t.trim() : "");
  if (!m) throw new Error("the frame rate must be a number from 1 to 120 with up to 3 decimals");
  var v = BigInt(m[1]) * 1000n + BigInt((m[2] || "").padEnd(3, "0") || "0");
  if (v < 1000n || v > 120000n) throw new Error("the frame rate must be a number from 1 to 120 with up to 3 decimals");
  return v;
}
function _fpsText(v) {
  var s = String(v / 1000n), f = String(v % 1000n).padStart(3, "0").replace(/0+$/, "");
  return f ? s + "." + f : s;
}
function _scale(n, d) { // positive ratio to 5 decimals, half up, trailing zeros dropped
  var v = _halfUp(n * 100000n, d), s = String(v / 100000n), f = String(v % 100000n).padStart(5, "0").replace(/0+$/, "");
  return f ? s + "." + f : s;
}
function _land(n, d) {
  var r = _halfUp(n, d);
  if (r < 0n) throw new Error("that line would land before 0:00:00.000");
  if (r > _MAXMS) throw new Error("that line would land after 99:59:59.999");
  return r;
}

function shiftTruth(shown, wanted) {
  var a = _time(shown), b = _time(wanted), d = b - a;
  if (d === 0n) return "Both times are the same, so the shift is 0 seconds. Nothing moves.";
  return "A line shown at " + _fmt(a) + " should appear at " + _fmt(b) + ". Moving every line " + _move(d) + " does that. It fixes the whole file only if every line is off by the same amount.";
}
function stretchTruth(a1, b1, a2, b2, q) {
  var x1 = _time(a1), y1 = _time(b1), x2 = _time(a2), y2 = _time(b2), t = _time(q);
  if (x2 <= x1) throw new Error("the last line must be shown later than the first line");
  if (y2 <= y1) throw new Error("the last line must be wanted later than the first line");
  var dx = x2 - x1, dy = y2 - y1;
  var r = _land(y1 * dx + (t - x1) * dy, dx);
  return "The two anchors give a scale factor of " + _scale(dy, dx) + " on the time between them. A line shown at " + _fmt(t) + " should then appear at " + _fmt(r) + ", " + _move(r - t) + ". This assumes the drift grows steadily from the first line to the last.";
}
function fpsTruth(subFps, vidFps, q) {
  var s = _fps(subFps), v = _fps(vidFps), t = _time(q);
  if (s === v) return "Both frame rates are " + _fpsText(s) + " fps, so the scale factor is 1 and no time changes.";
  var r = _land(t * s, v);
  return "Subtitles timed at " + _fpsText(s) + " fps on a video at " + _fpsText(v) + " fps: multiply every time by " + _scale(s, v) + ". A line shown at " + _fmt(t) + " becomes " + _fmt(r) + ", " + _move(r - t) + ".";
}
