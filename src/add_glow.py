"""The sunburst behind the plate on a successful serve (Figma node 2706:2857).

The original is a conic-gradient at mix-blend-lighten 60%. This uses SVG wedge
paths instead, because the burst has to sit above the pan and below the plate,
and a CSS div cannot be slotted into the SVG's paint order.
"""
SRC = 'pancake-app.html'
s = open(SRC).read()


def sub(a, b):
    global s
    assert a in s, 'MISSING: ' + a[:90]
    s = s.replace(a, b, 1)


# ---- 1. The burst layer, painted before the plate ----
sub('''    /* Plate: Figma node 2696:2130, 362x362, sharing the pan's centre */''',
    '''    /* Successful-serve sunburst (Figma node 2706:2857), above the pan, below the plate */
    var raysG = null;
    if (opts.dial){
      raysG = el("g", {"class":"rays", opacity:0});
      /* Angular spans of the white wedges, taken from the original conic-gradient
         colour stops (in %, from 90deg) */
      [[0,4.33],[11.54,15.86],[23.09,34.62],[41.36,48.55],[56,65],[74.53,85.58],[90,94.78]]
        .forEach(function(w){
          var R = 430, D = Math.PI / 180;
          var a0 = (90 + w[0] * 3.6) * D, a1 = (90 + w[1] * 3.6) * D;
          var x0 = PCX + R * Math.sin(a0), y0 = PCY - R * Math.cos(a0);
          var x1 = PCX + R * Math.sin(a1), y1 = PCY - R * Math.cos(a1);
          raysG.appendChild(el("path", {
            d: "M" + PCX + " " + PCY + " L" + x0.toFixed(1) + " " + y0.toFixed(1) +
               " A" + R + " " + R + " 0 0 1 " + x1.toFixed(1) + " " + y1.toFixed(1) + " Z",
            fill: "#ffffff"
          }));
        });
      svg.appendChild(raysG);
    }

    /* Plate: Figma node 2696:2130, 362x362, sharing the pan's centre */''')

# ---- 2. set() takes an extra glow argument ----
sub('''      set: function(state, dialAngle, plateP){''',
    '''      set: function(state, dialAngle, plateP, glow){
        if (raysG) raysG.setAttribute("opacity", (0.6 * clamp(glow || 0)).toFixed(3));''')

# ---- 3. Pass it from render(); only a well-timed serve lights up ----
sub('''    hero.set(s, durToAngle(DUR), plateP);''',
    '''    /* the burst fades in as the plate settles */
    hero.set(s, durToAngle(DUR), plateP, serveOk ? smooth((plateP - 0.15) / 0.5) : 0);''')

# ---- 4. Record whether this serve landed in the success window ----
sub('''  var served = null;   /* verdict frozen at the moment of serving */''',
    '''  var served = null;   /* verdict frozen at the moment of serving */
  var serveOk = false; /* did this serve land in the 00:00 success window */''')

sub('''    playSfx(Math.abs(t - DUR) <= SERVE_WINDOW ? "ok" : "normal");''',
    '''    serveOk = Math.abs(t - DUR) <= SERVE_WINDOW;
    playSfx(serveOk ? "ok" : "normal");''')

# Reset, retiming and restarting all switch the burst off
sub('''  replay.addEventListener("click", function(){
    playSfx("click");
    served = null; t = 0; setRunning(false); tweenPlate(0);
  });''',
    '''  replay.addEventListener("click", function(){
    playSfx("click");
    served = null; serveOk = false; t = 0; setRunning(false); tweenPlate(0);
  });''')

sub('''    if (served){ served = null; tweenPlate(0); }''',
    '''    if (served){ served = null; serveOk = false; tweenPlate(0); }''')

sub('''    if (served){ served = null; plateP = 0; }''',
    '''    if (served){ served = null; serveOk = false; plateP = 0; }''')


# ---- 5. Burn more slowly past zero: stretch the burn window from 1/5 of the
# countdown to 1/2. The browning at 5s over now equals what 2s over used to give
# (b^0.8 = 0.415); the curve keeps its shape and is simply stretched 2.5x. ----
sub('  function burnOf(x){ return x * 0.2; }',
    '  function burnOf(x){ return x * 0.5; }')
sub('  function endOf(x){ return x * 1.2; }',
    '  function endOf(x){ return x * 1.5; }')

open(SRC, 'w').write(s)
print('sunburst wired in, %.0f KB' % (len(s) / 1024))
