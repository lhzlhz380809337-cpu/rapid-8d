(function() {
  'use strict';

  // Professional palette — one color per category type
  var PALETTE = [
    { line: '#2471a3', fill: '#d4e6f1', text: '#1a5276' },  // blue
    { line: '#1e8449', fill: '#d5f5e3', text: '#145a32' },  // green
    { line: '#b9770e', fill: '#fdebd0', text: '#7d6608' },  // amber
    { line: '#c0392b', fill: '#fadbd8', text: '#922b21' },  // red
    { line: '#6c3483', fill: '#e8daef', text: '#4a235a' },  // purple
    { line: '#117a65', fill: '#d1f2eb', text: '#0b5345' }   // teal
  ];

  function renderFishbone(container, data) {
    var W = 960, MARGIN = 10;
    var SPINE_Y, SPINE_X1, SPINE_X2;

    var cats = data.categories || [];
    var problem = data.problem || '问题';
    var n = cats.length;
    var mid = Math.ceil(n / 2);
    var upper = cats.slice(0, mid);
    var lower = cats.slice(mid);
    var maxRows = Math.max(upper.length, lower.length);

    var BONE_LEN = 185;
    var ANGLE = 32;
    var rad = ANGLE * Math.PI / 180;
    var dY = Math.sin(rad) * BONE_LEN;
    var dX = Math.cos(rad) * BONE_LEN;

    // Calculate SVG dimensions
    var topReach = upper.length > 0 ? dY * (upper.length - 0.3) + 80 : 0;
    var bottomReach = lower.length > 0 ? dY * (lower.length - 0.3) + 80 : 0;
    var H = Math.max(520, topReach + bottomReach + 100);

    SPINE_Y = Math.round(topReach + 60);
    SPINE_X1 = 160;
    SPINE_X2 = 760;

    if (H < 400) H = 400;

    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    svg.setAttribute('width', '100%');
    svg.setAttribute('style', 'max-width:960px; display:block; margin:0 auto;');

    var defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');

    // Arrowhead marker
    defs.innerHTML =
      '<marker id="fh-arrow" markerWidth="12" markerHeight="8" refX="10" refY="4" orient="auto">' +
      '<polygon points="0 0, 12 4, 0 8" fill="#2c3e50"/>' +
      '</marker>' +
      // Drop shadow filter
      '<filter id="fh-shadow" x="-5%" y="-5%" width="115%" height="115%">' +
      '<feDropShadow dx="1" dy="1" stdDeviation="1.5" flood-opacity="0.12"/>' +
      '</filter>';
    svg.appendChild(defs);

    // ── Title ──────────────────────────────────────────────────
    var title = elt('text', {
      x: W / 2, y: 28,
      'text-anchor': 'middle', fill: '#2c3e50',
      'font-size': '16', 'font-weight': 'bold',
      'font-family': 'Microsoft YaHei, sans-serif'
    });
    title.textContent = '根本原因分析 — 鱼骨图 ( Ishikawa )';
    svg.appendChild(title);

    // ── Spine ──────────────────────────────────────────────────
    svg.appendChild(elt('line', {
      x1: SPINE_X1, y1: SPINE_Y, x2: SPINE_X2, y2: SPINE_Y,
      stroke: '#2c3e50', 'stroke-width': '3.5',
      'marker-end': 'url(#fh-arrow)'
    }));

    // ── Problem head box ───────────────────────────────────────
    var headW = 170, headH = 52;
    var headX = SPINE_X2 + 6, headY = SPINE_Y - headH / 2;
    svg.appendChild(elt('rect', {
      x: headX, y: headY, width: headW, height: headH, rx: 8,
      fill: '#2c3e50', filter: 'url(#fh-shadow)'
    }));
    var ht = elt('text', {
      x: headX + headW / 2, y: headY + headH / 2 + 6,
      'text-anchor': 'middle', fill: '#fff',
      'font-size': '15', 'font-weight': 'bold',
      'font-family': 'Microsoft YaHei, sans-serif'
    });
    ht.textContent = problem;
    svg.appendChild(ht);

    // ── Upper bones ────────────────────────────────────────────
    var upperStartX = SPINE_X1 + 50;
    var upperSpacing = (SPINE_X2 - upperStartX - dX) / Math.max(upper.length - 1, 1);

    for (var i = 0; i < upper.length; i++) {
      var sx = upperStartX + upperSpacing * (upper.length - 1 - i);
      var ey = SPINE_Y - dY;
      var pal = PALETTE[i % PALETTE.length];
      drawBone(svg, sx, SPINE_Y, sx + dX, ey, upper[i], pal, 1);
    }

    // ── Lower bones ────────────────────────────────────────────
    var lowerStartX = SPINE_X1 + 80;
    var lowerSpacing = (SPINE_X2 - lowerStartX - dX) / Math.max(lower.length - 1, 1);

    for (var j = 0; j < lower.length; j++) {
      var lsx = lowerStartX + lowerSpacing * (lower.length - 1 - j);
      var ley = SPINE_Y + dY;
      var lpal = PALETTE[(mid + j) % PALETTE.length];
      drawBone(svg, lsx, SPINE_Y, lsx + dX, ley, lower[j], lpal, -1);
    }

    container.appendChild(svg);
  }

  function drawBone(svg, sx, sy, ex, ey, cat, pal, dir) {
    var isUp = dir < 0;
    var cx = ex, cy = ey;
    var boneW = 2.2;

    // Main bone line
    svg.appendChild(elt('line', {
      x1: sx, y1: sy, x2: cx, y2: cy,
      stroke: pal.line, 'stroke-width': String(boneW)
    }));

    // Category label box
    var boxW = 60, boxH = 28;
    var bx = cx + (isUp ? -boxW / 2 : -boxW / 2);
    var by = cy + (isUp ? -boxH - 4 : 8);

    svg.appendChild(elt('rect', {
      x: Math.round(bx), y: Math.round(by), width: boxW, height: boxH, rx: 5,
      fill: pal.fill, stroke: pal.line, 'stroke-width': '1.5', filter: 'url(#fh-shadow)'
    }));
    var lbl = elt('text', {
      x: Math.round(bx + boxW / 2), y: Math.round(by + boxH / 2 + 5),
      'text-anchor': 'middle', fill: pal.text,
      'font-size': '13', 'font-weight': 'bold',
      'font-family': 'Microsoft YaHei, sans-serif'
    });
    lbl.textContent = cat.name;
    svg.appendChild(lbl);

    // Causes
    var causes = cat.causes || [];
    var angle = Math.atan2(ey - sy, ex - sx);
    var boneLength = Math.sqrt((ex - sx) * (ex - sx) + (ey - sy) * (ey - sy));

    for (var i = 0; i < causes.length; i++) {
      var t = (i + 1) / (causes.length + 1);
      var px = sx + (ex - sx) * t;
      var py = sy + (ey - sy) * t;

      // Perpendicular branch (sort-of-horizontal)
      var brLen = isUp ? 65 : 65;
      var brDx = brLen * Math.cos(angle) * 0.3 + (isUp ? brLen * 0.7 : brLen * 0.7);
      var brDy = (isUp ? -14 : 14);

      var bEndX = px + brDx;
      var bEndY = py;

      svg.appendChild(elt('line', {
        x1: px, y1: py, x2: bEndX, y2: bEndY,
        stroke: pal.line, 'stroke-width': '1.2', 'stroke-opacity': '0.6'
      }));

      // Small dot at branch point
      svg.appendChild(elt('circle', {
        cx: px, cy: py, r: 2.5, fill: pal.line
      }));

      // Cause label — pill shaped background
      var causeText = causeLabel(causes[i]);
      var causeBoxW = textWidth(causeText) + 20;
      var causeBoxH = 22;
      var cbx = bEndX + 4;
      var cby = bEndY - causeBoxH / 2;

      // Truncate if too long
      if (cbx + causeBoxW > 940) {
        causeBoxW = Math.min(causeBoxW, 940 - cbx);
      }

      svg.appendChild(elt('rect', {
        x: cbx, y: cby, width: causeBoxW, height: causeBoxH, rx: 4,
        fill: '#fff', stroke: pal.line, 'stroke-width': '1', 'stroke-opacity': '0.5'
      }));
      var ct = elt('text', {
        x: cbx + 10, y: cby + causeBoxH / 2 + 4,
        fill: pal.text, 'font-size': '11.5',
        'font-family': 'Microsoft YaHei, sans-serif'
      });
      ct.textContent = causeText;
      svg.appendChild(ct);
    }
  }

  function causeLabel(text) {
    if (text.length <= 16) return text;
    return text.slice(0, 15) + '..';
  }

  function textWidth(text) {
    // Approximate: Chinese chars ~14px, ASCII ~7px at font-size 11.5
    var w = 0;
    for (var i = 0; i < text.length; i++) {
      w += text.charCodeAt(i) > 127 ? 14 : 7;
    }
    return w;
  }

  function elt(tag, attrs) {
    var e = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (var k in attrs) {
      e.setAttribute(k, attrs[k]);
    }
    return e;
  }

  // Auto-render on DOM ready
  function init() {
    var scripts = document.querySelectorAll('script.fishbone-data');
    scripts.forEach(function(script) {
      try {
        var data = JSON.parse(script.textContent.trim());
        var container = script.nextElementSibling;
        if (!container || !container.classList.contains('fishbone-container')) {
          container = document.createElement('div');
          container.className = 'fishbone-container';
          script.parentNode.insertBefore(container, script.nextSibling);
        }
        renderFishbone(container, data);
      } catch(e) {
        console.error('Fishbone render error:', e);
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
