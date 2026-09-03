"""Give the title and the two stars the same grain the buttons use (--noise).

They cannot take a rectangular ::after the way the buttons do. A button is a
solid rounded rectangle, so the overlay lines up with it exactly; the title and
the stars are irregular shapes, and a rectangle would leave a visible square
patch of extra grain on the gingham cloth. So the same image becomes an SVG
pattern, masked by the lettering (including its 10px outline) and by the star
outlines themselves, and the grain lands only on the artwork's own ink.
"""
import re

SRC = 'pancake-app.html'
s = open(SRC).read()


def sub(a, b):
    global s
    assert a in s, 'MISSING: ' + a[:90]
    s = s.replace(a, b, 1)


# ---- 0. Pull out the grain image the buttons use ----
noise = re.search(r'--noise:\s*url\(["\']?(data:image/[^"\')]+)', s).group(1)

# ---- 1. One document-wide pattern; the id resolves from any svg on the page ----
sub('<div id="stage">', '''<div id="stage">
    <!-- Grain pattern: the same image and the same 128px tile as the buttons' .grain -->
    <svg width="0" height="0" aria-hidden="true" style="position:absolute">
      <defs>
        <pattern id="grain-pat" width="128" height="128" patternUnits="userSpaceOnUse">
          <image href="%s" width="128" height="128" preserveAspectRatio="none"/>
        </pattern>
      </defs>
    </svg>
''' % noise)

# ---- 2. Title: mask with the full outer edge of the lettering (glyph + 10px outline) ----
TXT = ('<text x="166.22" y="37.18" xml:space="preserve">IT”S </text>'
       '<text x="166.22" y="74.18" xml:space="preserve">PANCAKE </text>'
       '<text x="166.22" y="111.18">TIME</text>')

sub('''        </mask>
      </defs>''',
    '''        </mask>
        <!-- Grain mask: a stroke of 20 (= 10px outside) is exactly the title's outermost edge -->
        <mask id="title-solid" maskUnits="userSpaceOnUse" x="-60" y="-60" width="480" height="300">
          <g class="t-solid">%s</g>
        </mask>
      </defs>''' % TXT)

sub('''<g class="t-core">%s</g>
      </g>
    </svg>''' % TXT,
    '''<g class="t-core">%s</g>
        <g class="t-grain" mask="url(#title-solid)">
          <rect x="-120" y="-120" width="600" height="420" fill="url(#grain-pat)"/>
        </g>
      </g>
    </svg>''' % TXT)

# ---- 3. The two stars: the outer Star 6 path plus its 10px stroke is the whole silhouette ----
n = 0


def star(m):
    global n
    n += 1
    svg = m.group(0)
    d = re.search(r'<path id="Star 6" d="([^"]+)"', svg).group(1)
    mask = ('<defs><mask id="star-solid-%d" maskUnits="userSpaceOnUse" '
            'x="-40" y="-40" width="240" height="240">'
            '<path d="%s" fill="#fff" stroke="#fff" stroke-width="10" '
            'stroke-linejoin="round"/></mask></defs>' % (n, d))
    grain = ('<g class="d-grain" mask="url(#star-solid-%d)">'
             '<rect x="-40" y="-40" width="240" height="240" fill="url(#grain-pat)"/></g>' % n)
    svg = svg.replace('<g id="star deco">', mask + '\n<g id="star deco">', 1)
    return svg.replace('</svg>', grain + '</svg>', 1)


s = re.sub(r'<svg class="deco deco-star".*?</svg>', star, s, flags=re.S)
assert n == 2, 'found %d stars, expected 2' % n

# ---- 4. CSS: opacity .45 and overlay, matching .pbtn > .grain ----
sub('.t-core  text{fill:#d57e36;stroke:none}                  /* orange glyph body */',
    '''.t-core  text{fill:#d57e36;stroke:none}                  /* orange glyph body */
.t-solid text{fill:#fff;stroke:#fff;stroke-width:20;stroke-linejoin:round}  /* solid silhouette used as the grain mask */
/* Grain: same opacity and blend mode as the buttons' .grain */
.t-grain,.d-grain{mix-blend-mode:overlay;opacity:.45}''')

open(SRC, 'w').write(s)
print('grain wired in: title + %d stars, %.0f KB' % (n, len(s) / 1024))
