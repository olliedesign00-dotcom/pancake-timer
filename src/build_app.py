import re, base64

style = open('_style.txt').read()
script = open('_script.txt').read()

# ---------- 1. JS: drop the two doc-page-only sections (stills and board) ----------
a = script.index('/* ---- Static stills ---- */')
b = script.index('/* ---- Hero pan: animated ---- */')
script = script[:a] + script[b:]

# This build has no doneness scrubber and no preset buttons, so drop their wiring
def drop(pat, why):
    global script
    m = re.search(pat, script, re.S)
    assert m, why
    script = script[:m.start()] + script[m.end():]

# Remove the scrubber wiring wholesale (scrubTo through keydown)
a1 = script.index('  function scrubTo(clientX){')
b1 = script.index('  /* for screen recording', a1)
script = script[:a1] + script[b1:]
script = script.replace('  /* for screen recording: lets an external caller set the cook time directly */\n  window.__seek = function(sec){ setRunning(false); t = sec; render(); };\n', '')

# the two scrubber-related lines inside render()
script = script.replace('    playhead.style.left = (t / endOf(DUR) * 100) + "%";\n', '')
script = script.replace('    track.setAttribute("aria-valuemax", Math.round(endOf(DUR)));\n', '')
script = script.replace('    track.setAttribute("aria-valuenow", Math.round(t));\n', '')
script = script.replace('    track.setAttribute("aria-valuetext", s.label + " " + s.text + "，" + s.stage);\n', '')
script = script.replace('  var track = document.getElementById("track");\n', '')
script = script.replace('  var playhead = document.getElementById("playhead");\n', '')
# legend and hint text
script = script.replace('    legStart.textContent = mmss(DUR) + " raw batter";\n', '')
script = script.replace('    legEnd.textContent = mmss(burnOf(DUR)) + " burnt";\n', '')
script = script.replace('  var legStart = document.getElementById("leg-start");\n', '')
script = script.replace('  var legEnd = document.getElementById("leg-end");\n', '')
script = script.replace('  var dialHint = document.getElementById("dial-hint");\n', '')
script = re.sub(r'    dialHint\.innerHTML = .*?;\n', '', script, flags=re.S)
# Leave the preset-button forEach in place: with no .sp-btn it is a no-op
# anyway, and deleting it by regex swallows the toggle handler that follows.
# Keyboard handling for the scrubber (there is no scrubber any more)

# Finally: add the logic that scales the 660x900 stage to fit the window
# Web-page build: open paused at the set time and wait for START; never autostart
script = script.replace('\n  setRunning(true);\n', '\n  setRunning(false);\n')
assert '\n  setRunning(true);\n' not in script

script = script.rstrip()
assert script.endswith('})();')
script = script[:-len('})();')] + '''
  /* Scale the 660x900 layout to fit the window, so every position below
     can be hard-coded straight from the design. */
  var stage = document.getElementById("stage");
  var shell = document.getElementById("shell");
  function fit(){
    var k = Math.min((window.innerWidth - 32) / 660, (window.innerHeight - 32) / 900, 1.2);
    k = Math.max(k, 0.28);
    stage.style.transform = "scale(" + k + ")";
    shell.style.height = (900 * k) + "px";
    shell.style.width = (660 * k) + "px";
  }
  fit();
  window.addEventListener("resize", fit);
})();'''

# ---------- 2. CSS: keep all of it; layout rules go last and win ----------
comp = style          # keep every component rule, so .pan-card / .pbtn / .cutlery are never missed
tokens = ''

page = '''
/* ========== Web-page layout (overrides the doc-page layout above) ========== */
html,body{height:100%}
body{
  margin:0;
  background:var(--cloth-base);
  background-image:
    repeating-linear-gradient(90deg, var(--cloth-line) 0 62px, transparent 62px 100px),
    repeating-linear-gradient(0deg,  var(--cloth-line) 0 62px, transparent 62px 100px);
  color:var(--ink);
  font-family:Nunito,"Noto Sans TC",system-ui,sans-serif;
  display:flex;align-items:center;justify-content:center;
  padding:16px;overflow:hidden;
}
body::after{                      /* the cloth takes the same grain */
  content:"";position:fixed;inset:0;pointer-events:none;z-index:0;
  background-image:var(--noise);background-repeat:repeat;background-size:128px 128px;
  mix-blend-mode:overlay;opacity:.45;
}
#shell{position:relative;z-index:1}
#stage{position:absolute;left:0;top:0;width:660px;height:900px;transform-origin:top left}
#stage > *{position:absolute}

/* ---- Every coordinate straight from the design ---- */
#hero{left:104px;top:101px;width:454px;height:500px;box-shadow:none}
.pad{left:104px;top:641px;width:454px;display:flex;flex-direction:column;gap:20px}
.pad-row{display:flex;gap:4px;align-items:flex-start}
.pad-row .pbtn{flex:1 1 0;min-width:0}
.pbtn{--h:90px;--lbl:20px}
.pbtn--serve{--lbl:40px}

/* ---- Title and decorations ---- */
.title{
  /* 14px of extra viewBox, so the 10px outside stroke is not clipped */
  left:-5px;top:13px;width:360.449px;height:176.365px;
  pointer-events:none;
}
.title text{
  font-family:Chango,Nunito,sans-serif;
  font-size:40px;letter-spacing:3px;
  text-anchor:middle;dominant-baseline:central;
  paint-order:stroke;stroke-linejoin:miter;stroke-miterlimit:4;
}
/* Figma: back layer is a 10-outside #5e3624 stroke, front layer a 5-outside
   #ffffff stroke, both filled #d57e36. Inside out that reads orange / 5px
   white / 5px dark brown, and the counters (the holes in A and P) must be white.

   Simply stacking the two strokes breaks: the dark stroke also reaches 10px
   INTO the counters while the white only reaches 5px, so it cannot cover it
   and the middle of A's counter stays dark brown. Hence four layers — lay
   down white wide enough to fill the counters, mask the dark layer to the
   outside of the glyphs, then put the 5px white edge back on top. */
.t-mask  text{fill:#000;stroke:#000;stroke-width:8}      /* mask: glyph + 4px, which fills the counters */
.t-inner text{fill:#fff;stroke:#fff;stroke-width:20}     /* white base that fills the counters */
.t-edge  text{fill:none;stroke:#5e3624;stroke-width:20}  /* dark brown outline, masked to outside the glyphs */
.t-halo  text{fill:#fff;stroke:#fff;stroke-width:10}     /* 5px white ring */
.t-core  text{fill:#d57e36;stroke:none}                  /* orange glyph body */
/* Only the handle needs to be interactive inside the pan SVG; everything
   else refuses pointer events. The two serve-cutlery images sit at opacity 0,
   but an SVG <image> still intercepts clicks — and they sit at the bottom
   corners of the card, exactly over the middle of the handle when it is
   turned to a diagonal. */
/* The sunburst behind the plate on a successful serve (Figma node 2706:2857).
   The original is a conic-gradient at mix-blend-lighten 60%; this uses SVG
   wedges instead, so it can sit behind the plate and in front of the pan. */
.rays{
  mix-blend-mode:lighten;
  transform-box:view-box;transform-origin:227px 248.5px;
  animation:rays-spin 20s linear infinite;
}
@keyframes rays-spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
@media (prefers-reduced-motion:reduce){ .rays{animation:none} }
.pan-card svg *{pointer-events:none}
.pan-card svg .grip{pointer-events:auto}
.spark{background:#fff;width:17.08px;height:12px;transform:rotate(-7.93deg);pointer-events:none}
.deco{pointer-events:none}
.sr{position:absolute;width:1px;height:1px;margin:-1px;padding:0;overflow:hidden;
    clip-path:inset(50%);white-space:nowrap;border:0}
'''

# Cloth swatches. Only on :root, never redefined for dark mode — these are
# the design's own colours.
comp = comp.replace('  --d-edge:#5e3624;',
                    '  --cloth-base:#fffaf8;\n  --cloth-line:rgba(233,169,160,.30);\n  --d-edge:#5e3624;', 1)

light = open('assets/light.svg').read()
star_a = open('assets/star-a.svg').read()
star_b = open('assets/star-b.svg').read()
def inline(svg, cls, style):
    svg = svg.replace('<svg ', '<svg class="deco %s" style="%s" aria-hidden="true" ' % (cls, style), 1)
    svg = svg.replace('preserveAspectRatio="none" overflow="visible" style="display: block;"', '')
    # Figma bakes its noise/texture into a filter inside the exported SVG. That
    # grain is far coarser than the global grain layer, and on a small shape like
    # a star it turns the whole outline into rough speckle. Strip it and let the
    # global 128px tile handle texture everywhere.
    svg = re.sub(r'\s*filter="url\(#filter0_ng_[^"]*\)"', '', svg)
    svg = re.sub(r'<defs>.*?</defs>\s*', '', svg, flags=re.S)
    return svg

body = '''
<div id="shell">
  <div id="stage">
    <div class="pan-card grainy" id="hero"></div>

    <div class="pad">
      <button type="button" class="pbtn pbtn--serve" id="serve">
        <i class="grain"></i>
        %SERVE_INNER%
      </button>
      <div class="pad-row">
        <button type="button" class="pbtn" id="replay"><i class="grain"></i><span class="pbtn-label">RESET</span></button>
        <button type="button" class="pbtn" id="toggle"><i class="grain"></i><span class="pbtn-label" id="toggle-label">START</span></button>
      </div>
    </div>

    <div class="spark" style="left:33px;top:114px"></div>
    <div class="spark" style="left:72px;top:109px"></div>
    <div class="spark" style="left:194px;top:92px"></div>
    <svg class="title" viewBox="-14 -14 360.449 176.365" aria-hidden="true">
      <defs>
        <mask id="title-outside" maskUnits="userSpaceOnUse" x="-40" y="-40" width="440" height="240">
          <rect x="-40" y="-40" width="440" height="240" fill="#fff"/>
        <g class="t-mask"><text x="166.22" y="37.18" xml:space="preserve">IT”S </text><text x="166.22" y="74.18" xml:space="preserve">PANCAKE </text><text x="166.22" y="111.18">TIME</text></g>
        </mask>
      </defs>
      <g transform="rotate(-8 166.22 74.18)">
        <g class="t-inner"><text x="166.22" y="37.18" xml:space="preserve">IT”S </text><text x="166.22" y="74.18" xml:space="preserve">PANCAKE </text><text x="166.22" y="111.18">TIME</text></g>
        <g class="t-edge" mask="url(#title-outside)"><text x="166.22" y="37.18" xml:space="preserve">IT”S </text><text x="166.22" y="74.18" xml:space="preserve">PANCAKE </text><text x="166.22" y="111.18">TIME</text></g>
        <g class="t-halo"><text x="166.22" y="37.18" xml:space="preserve">IT”S </text><text x="166.22" y="74.18" xml:space="preserve">PANCAKE </text><text x="166.22" y="111.18">TIME</text></g>
        <g class="t-core"><text x="166.22" y="37.18" xml:space="preserve">IT”S </text><text x="166.22" y="74.18" xml:space="preserve">PANCAKE </text><text x="166.22" y="111.18">TIME</text></g>
      </g>
    </svg>
    %LIGHT%

    %STAR_B%
    %STAR_A%

    <p class="sr" id="clock-line" aria-live="polite">
      <span class="pre" id="clock-label">Left</span>
      <span id="clock">00:30</span>
      <span id="chip"><span id="chip-text">Raw batter</span></span>
    </p>
  </div>
</div>
'''
# The shared defs (noise/texture filters + the cutlery clip paths) have to come
# across too. Without them the cutlery highlights lose their clip and the plate
# loses a layer of texture.
body = open('_defs.txt').read() + body

body = body.replace('%LIGHT%', inline(light, 'deco-light', 'left:102px;top:67px;width:183.629px;height:78.8815px'))
body = body.replace('%STAR_A%', inline(star_a, 'deco-star', 'left:542px;top:120px;width:38.975px;height:38.976px'))
body = body.replace('%STAR_B%', inline(star_b, 'deco-star', 'left:493px;top:69px;width:64.959px;height:64.959px'))

body = body.replace('%SERVE_INNER%', open('_serve.txt').read().strip())

extra = ''

# ---- favicon: the 860x860 source, resized to 64 for the browser tab and
# 180 for iOS "Add to Home Screen". Embedded as data URIs for the same reason
# as the audio: it keeps this a single self-contained HTML file. ----
import base64, io
from PIL import Image
_ico = Image.open('assets/favicon.png').convert('RGBA')


def _icon(n):
    buf = io.BytesIO()
    _ico.resize((n, n), Image.LANCZOS).save(buf, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()


fav = ('<link rel="icon" type="image/png" sizes="64x64" href="%s">\n'
       '<link rel="apple-touch-icon" href="%s">\n' % (_icon(64), _icon(180)))

out = (open('_head.txt').read().replace('<title>Pancake Timer</title>',
                                        '<title>It’s Pancake Time</title>\n' + fav.rstrip())
       + '<style>' + comp + page + extra + '</style>\n'
       + body + '\n<script>' + script + '</script>\n')
open('pancake-app.html','w').write(out)
print('written', len(out))
