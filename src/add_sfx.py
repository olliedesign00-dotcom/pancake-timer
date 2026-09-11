"""Add sound to the pancake-app.html that build_app.py produced.

Every clip is embedded as a data URI. The artifact CSP only allows scripts from
the CDN allowlist and Google Fonts; external audio is blocked, blob: included.
"""
import base64

SRC = 'pancake-app.html'
FILES = [
    ('cook',   'pancake-cooking'),
    ('ok',     'serve-success'),
    ('normal', 'serve-normal'),
    ('click',  'button-click'),
    ('slide',  'slider'),
]

s = open(SRC).read()


def sub(a, b):
    global s
    assert a in s, 'MISSING: ' + a[:90]
    s = s.replace(a, b, 1)


entries = []
for key, name in FILES:
    with open('sfx/%s.mp3' % name, 'rb') as fh:
        entries.append('    %s: "data:audio/mpeg;base64,%s"'
                       % (key, base64.b64encode(fh.read()).decode()))

block = (
    '  /* ---- Sound ----\n'
    '     All embedded as data URIs: the artifact CSP only allows scripts from\n'
    '     the CDN allowlist and Google Fonts, so external audio is blocked.\n'
    '     The originals are 193-208kbps stereo, overkill for UI sound; at mono\n'
    '     96kbps they drop from 538KB to 269KB. */\n'
    '  var SFX = {\n'
    + ',\n'.join(entries) + '\n'
    '  };\n'
    '  /* <audio loop> leaves about 6ms of silence every time it wraps, an audible\n'
    '     tick in a 2.25s sizzle. This element is only the fallback now; the loop\n'
    '     itself runs through Web Audio further down. */\n'
    '  var cookAudio = new Audio(SFX.cook);\n'
    '  cookAudio.loop = true;\n'
    '  cookAudio.volume = 0.45;\n'
    '\n'
    '  var sfxPool = {};\n'
    '  function playSfx(key, vol){\n'
    '    var a = sfxPool[key] || (sfxPool[key] = new Audio(SFX[key]));\n'
    '    a.volume = vol == null ? 0.75 : vol;\n'
    '    try { a.currentTime = 0; } catch (e) {}\n'
    '    /* browsers block autoplay before the first interaction; fail quietly */\n'
    '    var pr = a.play();\n'
    '    if (pr && pr.catch) pr.catch(function(){});\n'
    '  }\n'
    '  function cookSound(on){\n'
    '    if (!on){\n'
    '      cookAudio.pause();\n'
    '      if (cookSrc){\n'
    '        cookAt = (actx.currentTime - cookT0) % cookBuf.duration;  /* resume from here */\n'
    '        try { cookSrc.stop(); } catch (e) {}\n'
    '        cookSrc = null;\n'
    '      }\n'
    '      return;\n'
    '    }\n'
    '    if (actx && cookBuf){\n'
    '      if (cookSrc) return;\n'
    '      if (actx.state === "suspended") actx.resume();\n'
    '      var s = actx.createBufferSource();\n'
    '      s.buffer = cookBuf;\n'
    '      s.loop = true;                  /* wraps sample-accurately: no gap */\n'
    '      var g = actx.createGain();\n'
    '      g.gain.value = 0.45;\n'
    '      s.connect(g); g.connect(actx.destination);\n'
    '      s.start(0, cookAt);\n'
    '      cookT0 = actx.currentTime - cookAt;\n'
    '      cookSrc = s;\n'
    '      return;\n'
    '    }\n'
    '    /* not decoded yet: fall back to the element */\n'
    '    var pr = cookAudio.play(); if (pr && pr.catch) pr.catch(function(){});\n'
    '  }\n'
    '  var lastSlide = 0;\n'
    '\n'
    '  /* ---- Handle-turn sound, via Web Audio ----\n'
    '     Two things <audio> cannot do: cut off instantly on release, and play\n'
    '     the clip backwards when turning anticlockwise. There is only one file,\n'
    '     so we decode it and build a reversed copy to give the dial direction. */\n'
    '  var AC = window.AudioContext || window.webkitAudioContext;\n'
    '  var actx = AC ? new AC() : null;\n'
    '  var slideFwd = null, slideRev = null, slideSrc = null;\n'
    '  if (actx){\n'
    '    try {\n'
    '      /* not fetch(dataURI): CSP connect-src blocks it, so decode base64 by hand */\n'
    '      var raw = atob(SFX.slide.slice(SFX.slide.indexOf(",") + 1));\n'
    '      var bytes = new Uint8Array(raw.length);\n'
    '      for (var bi = 0; bi < raw.length; bi++) bytes[bi] = raw.charCodeAt(bi);\n'
    '      actx.decodeAudioData(bytes.buffer, function(buf){\n'
    '        /* The file ends with about 0.3s of silence. Reversing it moves that\n'
    '           to the front, and since dragging retriggers every 150ms and\n'
    '           release cuts it off, anticlockwise would only ever play silence.\n'
    '           Trimming both ends makes either direction audible immediately. */\n'
    '        var ch0 = buf.getChannelData(0), n = buf.length, TH = 0.004;\n'
    '        var s0 = 0, s1 = n - 1;\n'
    '        while (s0 < n && Math.abs(ch0[s0]) < TH) s0++;\n'
    '        while (s1 > s0 && Math.abs(ch0[s1]) < TH) s1--;\n'
    '        var len = Math.max(1, s1 - s0 + 1);\n'
    '        var fwd = actx.createBuffer(buf.numberOfChannels, len, buf.sampleRate);\n'
    '        var rev = actx.createBuffer(buf.numberOfChannels, len, buf.sampleRate);\n'
    '        for (var c = 0; c < buf.numberOfChannels; c++){\n'
    '          var src = buf.getChannelData(c), f = fwd.getChannelData(c), r = rev.getChannelData(c);\n'
    '          for (var i = 0; i < len; i++){ f[i] = src[s0 + i]; r[i] = src[s1 - i]; }\n'
    '        }\n'
    '        slideFwd = fwd; slideRev = rev;\n'
    '      }, function(){});\n'
    '    } catch (e) {}\n'
    '  }\n'
    '  /* ---- Cooking loop, via Web Audio ----\n'
    '     An AudioBufferSourceNode with loop = true wraps sample-accurately, so a\n'
    '     seamless clip stays seamless. Decoded once at load. */\n'
    '  var cookBuf = null, cookSrc = null, cookAt = 0, cookT0 = 0;\n'
    '  if (actx){\n'
    '    try {\n'
    '      var craw = atob(SFX.cook.slice(SFX.cook.indexOf(",") + 1));\n'
    '      var cbytes = new Uint8Array(craw.length);\n'
    '      for (var ci = 0; ci < craw.length; ci++) cbytes[ci] = craw.charCodeAt(ci);\n'
    '      actx.decodeAudioData(cbytes.buffer, function(buf){ cookBuf = buf; }, function(){});\n'
    '    } catch (e) {}\n'
    '  }\n'
    '  function stopSlide(){\n'
    '    if (slideSrc){ try { slideSrc.stop(); } catch (e) {} slideSrc = null; }\n'
    '  }\n'
    '  /* dir > 0 clockwise (more time) plays forwards, dir < 0 plays reversed */\n'
    '  function playSlide(dir){\n'
    '    if (!actx || !slideFwd){ playSfx("slide", 0.6); return; }\n'
    '    if (actx.state === "suspended") actx.resume();\n'
    '    stopSlide();\n'
    '    var s = actx.createBufferSource();\n'
    '    s.buffer = (dir < 0 && slideRev) ? slideRev : slideFwd;\n'
    '    var g = actx.createGain();\n'
    '    g.gain.value = 0.6;\n'
    '    s.connect(g); g.connect(actx.destination);\n'
    '    s.start();\n'
    '    slideSrc = s;\n'
    '  }\n'
    '\n'
)

sub('  "use strict";\n', '  "use strict";\n\n' + block)

# Sizzle while the countdown runs; stop on pause, finish or serve
sub('''  function setRunning(on){
    running = on;
    toggleLabel.textContent = on ? "PAUSE" : "START";''',
    '''  function setRunning(on){
    running = on;
    cookSound(on);
    toggleLabel.textContent = on ? "PAUSE" : "START";''')

# Turning the handle to set the time
sub('''  function setDur(sec){
    if (served){ served = null; plateP = 0; }''',
    '''  function setDur(sec){
    var target = Math.max(DIAL_MIN, Math.min(DIAL_MAX, sec));
    var now = Date.now();
    /* dragging fires continuously, so throttle it; once clamped at an end, stay quiet */
    if (target !== DUR && now - lastSlide > 150){
      lastSlide = now;
      playSlide(target > DUR ? 1 : -1);
    }
    if (served){ served = null; plateP = 0; }''')

# Cut off the moment the handle or key is released
sub('''  function endDial(){ dialing = false; if (document.activeElement !== grip) card.classList.remove("is-setting"); }''',
    '''  function endDial(){
    stopSlide();
    dialing = false;
    if (document.activeElement !== grip) card.classList.remove("is-setting");
  }
  grip.addEventListener("keyup", stopSlide);
  grip.addEventListener("blur", stopSlide);''')

# START / PAUSE
sub('''  toggle.addEventListener("click", function(){
    if (served){ served = null; tweenPlate(0); }''',
    '''  toggle.addEventListener("click", function(){
    playSfx("click");
    if (served){ served = null; tweenPlate(0); }''')

# RESET
sub('''  replay.addEventListener("click", function(){ served = null; t = 0; setRunning(false); tweenPlate(0); });''',
    '''  replay.addEventListener("click", function(){
    playSfx("click");
    served = null; t = 0; setRunning(false); tweenPlate(0);
  });''')

# SERVE: 2.5s either side of 00:00 counts as a well-timed serve
sub('''  serveBtn.addEventListener("click", function(){
    if (t <= 0 || served) return;
    setRunning(false);''',
    '''  var SERVE_WINDOW = 2.5;   /* 2.5s either side of 00:00 = a five-second window */
  serveBtn.addEventListener("click", function(){
    if (t <= 0 || served) return;
    setRunning(false);
    playSfx(Math.abs(t - DUR) <= SERVE_WINDOW ? "ok" : "normal");''')

open(SRC, 'w').write(s)
print('sound wired in, %.0f KB' % (len(s) / 1024))
