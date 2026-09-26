# Copper-Policy project page

Static project page based on the public-facing arXiv version in `../MTLBot_Latex`.

Open `index.html` directly, or serve this directory:

```bash
python3 serve.py 8000      # http://localhost:8000
```

Use `serve.py`, **not** `python3 -m http.server`. The stdlib server ignores HTTP `Range`
requests, so Chrome reports `video.seekable === [0, 0]` and the custom progress bar cannot be
clicked or dragged — the videos look frozen at 0:00. Real static hosts (GitHub Pages, Netlify,
S3, nginx) all support ranges, so this is a local-preview problem only. `serve.py` adds byte-range
support and nothing else.

## Design rules

- **Everything important is on the page.** Abstract, headline numbers, the ablation tables,
  the method, and the representation diagnostics are rendered as HTML. The PDF link is a bonus,
  not the only path.
- **Ablations only.** The page deliberately carries no baseline-comparison tables. The headline
  strip gives our own numbers; every table below it is Measured on Copper-Policy and its own
  variants, so the reader sees what each component buys rather than a leaderboard.
- **Headline strip.** Six equal-width cards, no spans. Six columns of the 1120 px column leave
  ~162 px of content each, and two four-digit RoboTwin values plus their percent signs want ~153 px
  at the shared value size — which is why that size is 22 px rather than 26. The longest note
  ("No embodied pretraining") wants ~150 px, so notes stay on one line. The column count steps
  6 -> 3 -> 2 -> 1 at 1160 / 900 / 420 px, each step being the width below which a card could no
  longer hold both the pair and the longest note without wrapping. Keep the media queries in
  *descending* order: at 375 px an earlier `max-width:420px` block silently lost to a later
  `max-width:560px` one.
- **Videos, not stills, where motion is the evidence.** Real-robot rollouts and representation
  attention use a custom player instead of the native control strip: an always-visible progress bar
  that seeks on click, drag and arrow keys, plus play/pause, elapsed/total time and fullscreen.
  Native `controls` are deliberately off — the native strip auto-hides and is unusable for these
  wide, short strips. Videos are `preload="metadata"` with an extracted poster, so nothing plays
  on its own. Multiple clips per topic live in a tabbed box (`.mediabox[data-tabs]`).
- **One player per attention pair.** The Copper-Policy and `w/o Joint-Embedding Prediction` clips
  sit in the *same* `.vp` box, stacked, labelled with `.vp-tag` badges, and driven by a single
  control bar. `makePlayer` takes every `video` inside a box, the first one drives the time
  readout, and play/pause/seek are applied to all of them.
- **Pair sync is frame-accurate, not `timeupdate`-driven.** The first version corrected on the
  primary clip's `timeupdate` with a 0.25 s tolerance, and re-aligned nothing when the playback
  rate changed. Two problems: `timeupdate` fires only a few times a second and tolerated 2.5 frames
  of permanent offset on 10 fps strips, and assigning `playbackRate` to a *playing* element
  re-anchors each media clock independently — so the pair was furthest apart exactly when the
  reader had just slowed it down to look closely. Now a `requestAnimationFrame` loop pulls the
  sibling back to within `SYNC_TOLERANCE` (0.08 s, under one 10 fps frame) every frame while
  playing, and `align(true)` runs on rate change, on either clip starting, and on seek. A 300 ms
  `_syncHold` after a clip is actually moved stops seek thrash. The loop only schedules itself
  while something is playing, and `timeupdate` re-arms it so playback can never resume unsupervised.
  Verified with a Node harness driving the real script against a stubbed DOM: 0.7 s offsets
  injected before and after the rate-change align, mid-playback drift, and loop-boundary wraps all
  converge to 0.000 s; paused playback runs zero callbacks.
- **Playback speed.** Each control bar carries a `<select>` with 0.25× / 0.5× / 1.0× / 2.0×.
  The choice is page-wide (`setRate`) rather than per-player: slowing one clip to inspect the
  attention or speeding up a 38 s rollout should follow you into the next tab instead of having
  to be set again in all six players. A non-default speed turns the select copper so a
  slowed-down clip is never a mystery. `defaultPlaybackRate` is set alongside `playbackRate`, and a
  `ratechange` listener keeps the UI honest if the rate is ever changed from elsewhere.
- **Click easter egg.** Both logos play a hit and run a shake. Clicks 1-3 walk through `1/2/3.mp3`;
  every click from the fourth on is `meme-4.mp3`, so hammering the logo layers that one on itself
  instead of cycling. Playback is **layered, not restarted**: each click gets its own element, so a
  new hit never cuts off the previous one. Finished elements return to a per-file pool — already
  buffered, so reuse is instant — and all four files are primed at load so no click waits on a
  decode. A `MAX_VOICES` cap of 4 retires the oldest sounding voice when a fifth starts; stealing
  the oldest rather than refusing the new click keeps the logo responsive at any click rate.

  Each hit has its own shake, generated from a damped sinusoid rather than hand-written
  (`SPECS` + `sample()`), so frequency and decay are numbers that can be tuned. The design is
  deliberately **metal rather than jelly**: a soft body absorbs a blow and wobbles (large
  deformation, low frequency, one or two slow swings), while a stiff object jolts, rings fast and
  stops. So the impact stages carry no scale deformation at all — deforming is what makes a shape
  read as soft — the ring runs at 14-22 Hz instead of one swing per 300 ms, and amplitude halves
  every ~2 cycles. A 4 ms attack frame puts the peak almost instantly at the front; easing that in
  was the single biggest source of the jelly look. Keyframes interpolate linearly at ~10 samples
  per cycle because the sinusoid shape comes from the samples, not from an easing curve.

  Stage 3 sums three copies of the same impulse at the measured knock times. Sampled grids can
  straddle an impulse and render that knock a few percent short, so a frame is placed exactly on
  each hit — otherwise one of the three visibly landed softer than the others.

  Every set starts and ends on the identity transform, otherwise the mark jumps on replay.
  Rotation and displacement are anchored at `50% 50%`, avoiding the off-centre pivot that a stale
  `translateY` once produced (7 px on a 26 px icon is 27% of its own size, which read as the mark
  swinging rather than being struck).

## Asset caching

`styles.css` and the icon files are linked with a `?v=` query (`styles.css?v=2`). Browsers cache
stylesheets hard, and a stale one silently breaks layout — an earlier revision had `.brand` as a
plain `<a>` because the new `display:flex` never arrived, so the flex container in the top bar
compressed it below its content width and dropped the "Copper-Policy" label under the logo.

**Bump the `?v=` number in `index.html` whenever `styles.css` or an icon changes.**

## Where content comes from

| Page section | Source |
| --- | --- |
| Abstract | `sec_ARXIV/0_abstract.tex` |
| Overview figure caption | `main_arxiv.tex` teaser block + `sec_ARXIV/1_intro.tex` |
| Headline numbers, ablation tables, RoboTwin clean/random, training cost | `sec_ARXIV/5_experiments.tex`, `sec_ARXIV/5_efficiency_table.tex` |
| Ablation configurations | `sec_ARXIV/4_setting_tables.tex` |
| Method | `sec_ARXIV/4_method.tex` |
| Representation diagnostics | `sec_ARXIV/5_representation_analysis.tex` |
| Real-robot ablation + per-task scores | `~/PhD_HKU/realbot/saved/evaluation_summary.json`, cross-checked against each task's `evaluation_records.json` |
| Real-robot rollout videos | `~/PhD_HKU/realbot/saved/real_robot_results/full/*_grid_8x6_plus2_info.mp4` (1536×756, 30 fps; re-encoded CRF 26) |
| Attention videos | `~/PhD_HKU/realbot/saved/representation_diagnostics/{libero,robotwin,realbot}/attention/` — same episode, `full` vs `no_future` |
| `assets/temporal_cosine.png` | rendered from `pictures/temporal_cosine.pdf` |
| `assets/representation_analysis.png` | rendered from `pictures/representation_analysis.pdf` |
| `assets/copper.png` | project logo, supplied by the authors (360×360, transparent) |
| `assets/favicon.png` | 64×64 downscale of the logo, used as `<link rel="icon">` |
| `assets/apple-touch-icon.png` | 180×180 downscale, used as `apple-touch-icon` |
| `assets/sounds/1-3.mp3`, `meme-4.mp3` | click hits, all trimmed of head/tail silence and peak-matched to -1.0 dBFS. Clicks 1-3 play 1/2/3, click 4+ always plays `meme-4` |

Posters in `assets/video/` are extracted from the first frame of each clip
(`ffmpeg -vf "select=eq(n,0)" -frames:v 1`). Real-robot clips are the 1536×756 @ 30 fps grids from
`saved/`; the lower-resolution `MTLBot_Latex/supplementary/demo_mp4/tasks_summary/` copies are not
used.

Attention episode IDs currently on the page:

| Tab | Episode | Task |
| --- | --- | --- |
| LIBERO | `repo_0` / `000129` | “put both moka pots on the stove” (10.2 s, the longest of the LIBERO exports) |
| RoboTwin | `stack_blocks_three` / `000027` | “move the red, green and blue blocks to the centre and stack them” (12.1 s) |
| Real robot | `fold_the_towel` / `000066` | “Fold the towel” (16.8 s) |

The two clips in each attention tab live in one `.vp--pair` box with a single control bar, so they
play, pause and seek together and stay within 0.25 s of each other while running. A 3 px white rule
(`.vp-clip + .vp-clip`) separates the two models. The real-robot clips are separate boxes, so
starting one stops the others.

When the paper changes, refresh `assets/` and re-check every number against the LaTeX sources
above. Do not edit numbers in `index.html` without a matching change in the paper.
