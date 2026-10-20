# Sub Sync

Subtitle retiming arithmetic. A subtitle shown at 0:01:05.200 that should appear at 0:01:07.700 needs every line moved 2.5 seconds later.

## What it computes

Times are typed as hours:minutes:seconds with optional milliseconds (comma or dot), from 0:00:00 up to 99:59:59.999. Results are exact to the millisecond, rounded half up.

- **The shift truth** - the move, in seconds, that takes one line from where it shows to where it should show, early or late.
- **The stretch truth** - two anchor lines (first and last) give a scale factor. Any other line is placed on the straight line between them. This assumes the drift grows steadily.
- **The frame rate truth** - subtitles timed for one frame rate (1 to 120 fps, up to 3 decimals) played on a video at another: the scale factor and where a line lands.

## Boundary

Arithmetic only. It has not seen the subtitle file or the video. It does not know which lines are wrong, whether the drift is steady, whether the video has cuts or a different intro, or what a player does, and it gives no verdict that a fix is right. Check results against the picture. Every time and frame rate is the owner's own entry.

## Files

- `index.html` - landing page.
- `app.html` - the interactive calculator.
- `engine.js` - the arithmetic (BigInt milliseconds).
- `oracle.py` - the Python mirror (Fractions of seconds, a straight line through the anchors) that generates `expected.json`.
- `test.js` - compares every engine output against `expected.json` (328 cases).
- `expected.json` - the golden answers.

## Test

```
python3 oracle.py
node test.js
```

Live: https://ilanis-agent.github.io/subsync/
Repo: https://github.com/iLanis-agent/subsync
