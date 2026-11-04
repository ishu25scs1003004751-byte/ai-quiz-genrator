import base64
import difflib
import hashlib
import html
import io
import json
import math
import os
import random
import re
import time
from datetime import datetime, timedelta, timezone

import pandas as pd
from pypdf import PdfReader
import streamlit as st
import streamlit.components.v1 as components
from groq import Groq

import i18n
from i18n import tr

# ─── 3D tutor (built in, so no extra file is needed) ───
import types

_AVATAR_THREE = "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"
_AVATAR_NAMES = {"girl": "Aanya", "boy": "Arjun"}

_AVATAR_TEMPLATE = """
<!doctype html><html><head><meta charset="utf-8">
<style>
  html,body{margin:0;height:100%;background:transparent;overflow:hidden;font-family:'Segoe UI',system-ui,sans-serif}
  #wrap{position:relative;width:100%;height:100%}
  canvas{display:block;width:100%;height:100%;outline:none;cursor:pointer}
  #bub{position:absolute;right:8px;top:50%;transform:translateY(-46%) scale(.92);max-width:56%;opacity:0;transition:opacity .4s,transform .4s}
  #bub.on{opacity:1;transform:translateY(-50%) scale(1)}
  .card{position:relative;padding:10px 14px 11px;border-radius:18px 18px 18px 6px;color:#EEF0FF;font-size:14px;line-height:1.4;
        background:linear-gradient(135deg,rgba(124,92,255,.32),rgba(34,211,238,.14));border:1px solid rgba(255,255,255,.22);
        box-shadow:0 8px 28px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.18);backdrop-filter:blur(8px)}
  .card:before{content:"";position:absolute;left:-9px;bottom:12px;border:7px solid transparent;border-right-color:rgba(255,255,255,.22);border-left:0}
  .card.ok{border-color:#34D399;background:linear-gradient(135deg,rgba(52,211,153,.3),rgba(34,211,238,.12))}
  .card.no{border-color:#FB7185;background:linear-gradient(135deg,rgba(251,113,133,.28),rgba(124,92,255,.12))}
  .nm{display:inline-block;font-size:11px;font-weight:700;letter-spacing:.04em;padding:1px 9px;border-radius:99px;margin-bottom:5px;
      background:#FFC857;color:#0B0F1E}
  #fallback{display:none;position:absolute;inset:0;align-items:center;justify-content:center;font-size:64px}
</style></head><body>
<div id="wrap"><canvas id="c"></canvas>
<div id="bub"><div class="card" id="card"><span class="nm">__NAME__</span><div id="txt"></div></div></div>
<div id="fallback">__EMOJI__</div></div>
<script src="__AVATAR_THREE__"></script>
<script>
(function(){
  var MOOD = __MOOD__, SAY = __SAY__, CHAR = __CHAR__;
  var GIRL = CHAR === 'girl';
  var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

  // speech bubble with typewriter
  var bub = document.getElementById('bub'), card = document.getElementById('card'), txt = document.getElementById('txt');
  if (SAY){
    card.className = 'card ' + (MOOD==='correct' ? 'ok' : MOOD==='wrong' ? 'no' : '');
    setTimeout(function(){
      bub.classList.add('on');
      if (reduce){ txt.textContent = SAY; return; }
      var n = 0, iv = setInterval(function(){ n++; txt.textContent = SAY.slice(0, n); if (n >= SAY.length) clearInterval(iv); }, 22);
    }, 300);
  } else { bub.style.display = 'none'; }

  if (!window.THREE){ document.getElementById('fallback').style.display = 'flex'; return; }

  var cv = document.getElementById('c');
  var R = new THREE.WebGLRenderer({canvas:cv, antialias:true, alpha:true});
  R.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  var S = new THREE.Scene();
  var cam = new THREE.PerspectiveCamera(32, 1, .1, 60);
  cam.position.set(0, 1.7, 7.0); cam.lookAt(0, 1.6, 0);

  // lights
  S.add(new THREE.HemisphereLight(0xd9e0ff, 0x2a1a60, .95));
  var key = new THREE.DirectionalLight(0xffffff, .95); key.position.set(2.5, 4.5, 5); S.add(key);
  var rim = new THREE.DirectionalLight(0x22D3EE, .85); rim.position.set(-4, 2.5, -2); S.add(rim);
  var rim2 = new THREE.DirectionalLight(0xFFC857, .5); rim2.position.set(4, 1.5, -2); S.add(rim2);

  function mat(c, r, m){ return new THREE.MeshStandardMaterial({color:c, roughness:r == null ? .7 : r, metalness:m == null ? .05 : m}); }
  function basic(c, o){ return new THREE.MeshBasicMaterial({color:c, transparent:o != null, opacity:o == null ? 1 : o}); }
  function add(p, g, m, x, y, z){ var o = new THREE.Mesh(g, m); o.position.set(x||0, y||0, z||0); p.add(o); return o; }
  function tex(draw, w, h){ var c = document.createElement('canvas'); c.width = w; c.height = h || w; draw(c.getContext('2d'), c.width, c.height); return new THREE.CanvasTexture(c); }

  var glowTex = tex(function(g, w, h){ var gr = g.createRadialGradient(w/2, h/2, 0, w/2, h/2, w/2);
    gr.addColorStop(0, 'rgba(255,255,255,.95)'); gr.addColorStop(1, 'rgba(255,255,255,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, h); }, 128);
  function qTex(ch, col){ return tex(function(g, w, h){ g.font = 'bold 96px Segoe UI, Arial'; g.textAlign = 'center'; g.textBaseline = 'middle';
    g.shadowColor = col; g.shadowBlur = 18; g.fillStyle = col; g.fillText(ch, w/2, h/2 + 4); }, 128); }

  // ── stage: glow orbs, floor shadow, rings ──
  var orbs = [];
  [[0x7C5CFF, -2.2, 2.6, -3, 5], [0x22D3EE, 2.6, 1.2, -3, 4], [0xFFC857, .2, 3.4, -4, 3]].forEach(function(o, i){
    var s = new THREE.Sprite(new THREE.SpriteMaterial({map:glowTex, color:o[0], transparent:true, opacity:.42, depthWrite:false}));
    s.position.set(o[1], o[2], o[3]); s.scale.set(o[4], o[4], 1); S.add(s); orbs.push(s);
  });
  var shadow = new THREE.Mesh(new THREE.CircleGeometry(1.5, 40), new THREE.MeshBasicMaterial({map:glowTex, color:0x000000, transparent:true, opacity:.55, depthWrite:false}));
  shadow.rotation.x = -Math.PI/2; shadow.position.y = .01; S.add(shadow);
  var ring1 = new THREE.Mesh(new THREE.TorusGeometry(1.32, .022, 8, 80), basic(0x22D3EE, .85)); ring1.rotation.x = -Math.PI/2; ring1.position.y = .03; S.add(ring1);
  var ring2 = new THREE.Mesh(new THREE.TorusGeometry(1.62, .014, 8, 80), basic(0x7C5CFF, .7)); ring2.rotation.x = -Math.PI/2; ring2.position.y = .03; S.add(ring2);
  var dots = [];
  for (var d = 0; d < 6; d++){ var dm = new THREE.Mesh(new THREE.SphereGeometry(.05, 10, 8), basic(0xFFC857)); ring2.add(dm); dm.position.set(Math.cos(d * 1.047) * 1.62, Math.sin(d * 1.047) * 1.62, 0); dots.push(dm); }

  // ── materials ──
  var SKIN = mat(0xD9A27A, .55), SKIN2 = mat(0xC98E65, .6);
  var HAIR = mat(0x241A33, .32, .12);
  var HOOD = mat(0x7C5CFF, .6), HOOD2 = mat(0x5B3FE6, .65), WHITE = mat(0xFFFFFF, .35), DARK = mat(0x120E1C, .4);
  var PANT = mat(0x1B2447, .8), AMBER = new THREE.MeshStandardMaterial({color:0xFFC857, roughness:.35, metalness:.4, emissive:0x6a4a00});

  var root = new THREE.Group(); root.position.y = .05; S.add(root);

  // body
  var torso = add(root, new THREE.CylinderGeometry(.6, .5, 1.3, 32), HOOD, 0, .95, 0); torso.scale.z = .68;
  add(root, new THREE.SphereGeometry(.62, 28, 16, 0, Math.PI*2, 0, Math.PI/2), HOOD, 0, 1.58, 0).scale.set(1.02, .42, .62);
  add(root, new THREE.CylinderGeometry(.52, .52, .34, 28), PANT, 0, .2, 0).scale.z = .68;
  add(root, new THREE.SphereGeometry(.4, 24, 16), HOOD2, 0, 1.74, -.2).scale.set(1.25, .8, .6);               // hood behind neck
  var collar = add(root, new THREE.TorusGeometry(.24, .07, 12, 28), HOOD2, 0, 1.66, .03); collar.rotation.x = Math.PI/2;
  add(root, new THREE.CylinderGeometry(.14, .16, .3, 16), SKIN2, 0, 1.78, 0);
  [-.11, .11].forEach(function(x){ add(root, new THREE.CylinderGeometry(.016, .016, .34, 8), WHITE, x, 1.38, .38); add(root, new THREE.SphereGeometry(.03, 8, 8), WHITE, x, 1.2, .38); });
  var badge = add(root, new THREE.CylinderGeometry(.12, .12, .035, 5), AMBER, .27, 1.12, .405); badge.rotation.x = Math.PI/2;

  // head
  var head = new THREE.Group(); head.position.set(0, 2.2, 0); root.add(head);
  var skull = add(head, new THREE.SphereGeometry(.58, 44, 34), SKIN); skull.scale.set(1, 1.02, .97);
  [-1, 1].forEach(function(s){ add(head, new THREE.SphereGeometry(.085, 14, 12), SKIN, s*.57, -.02, 0).scale.set(.55, 1, .9); });
  if (GIRL){ [-1, 1].forEach(function(s){ add(head, new THREE.SphereGeometry(.03, 10, 8), AMBER, s*.58, -.12, .03); }); }
  add(head, new THREE.SphereGeometry(.05, 14, 12), SKIN2, 0, -.1, .56).scale.set(1, .9, .9);                  // nose

  // hair
  add(head, new THREE.SphereGeometry(.625, 44, 30, 0, Math.PI*2, 0, Math.PI*.56), HAIR, 0, .05, -.04).scale.set(1, 1.03, 1.02);
  if (GIRL){
    [[-.22, .42, .42, -.2], [0, .46, .44, 0], [.22, .42, .42, .2]].forEach(function(f){
      var s = add(head, new THREE.SphereGeometry(.24, 18, 14), HAIR, f[0], f[1], f[2]); s.scale.set(1.15, .55, .7); s.rotation.z = f[3]; });
    add(head, new THREE.SphereGeometry(.62, 28, 20), HAIR, 0, -.12, -.3).scale.set(1, 1.1, .7);
    [-1, 1].forEach(function(s){ var l = add(head, new THREE.SphereGeometry(.13, 14, 12), HAIR, s*.54, -.18, .06); l.scale.set(.8, 2.3, .8); });
  } else {
    add(head, new THREE.SphereGeometry(.26, 20, 14), HAIR, .1, .5, .22).scale.set(1.6, .8, 1);
    add(head, new THREE.SphereGeometry(.2, 18, 14), HAIR, -.22, .46, .3).scale.set(1.2, .7, .9);
    [-1, 1].forEach(function(s){ var l = add(head, new THREE.SphereGeometry(.09, 12, 10), HAIR, s*.55, -.02, .1); l.scale.set(.7, 1.8, .8); });
  }
  var tail = new THREE.Group(); tail.position.set(0, .3, -.52); head.add(tail);
  if (GIRL){
    add(tail, new THREE.TorusGeometry(.12, .035, 8, 18), AMBER, 0, 0, 0).rotation.x = Math.PI/2;
    add(tail, new THREE.SphereGeometry(.17, 16, 12), HAIR, 0, -.05, -.1);
    add(tail, new THREE.SphereGeometry(.15, 16, 12), HAIR, 0, -.3, -.16).scale.set(.95, 1.6, .95);
    add(tail, new THREE.SphereGeometry(.1, 14, 10), HAIR, 0, -.62, -.18).scale.set(.85, 1.7, .85);
  }

  // eyes
  function eye(x){
    var g = new THREE.Group(); g.position.set(x, .02, .49); head.add(g);
    add(g, new THREE.SphereGeometry(.115, 24, 18), WHITE).scale.set(1, 1.18, .55);
    var iris = new THREE.Group(); g.add(iris);
    add(iris, new THREE.SphereGeometry(.082, 20, 16), mat(0x4A2E1B, .3), 0, 0, .03).scale.set(1, 1.1, .5);
    add(iris, new THREE.SphereGeometry(.044, 16, 12), DARK, 0, 0, .05).scale.set(1, 1.1, .5);
    add(iris, new THREE.SphereGeometry(.026, 10, 8), basic(0xffffff), .028, .035, .075);
    add(iris, new THREE.SphereGeometry(.013, 8, 6), basic(0xffffff), -.025, -.03, .072);
    if (GIRL){ for (var i = 0; i < 3; i++){ var l = add(g, new THREE.BoxGeometry(.07, .012, .01), DARK, x < 0 ? -.1 - i * .01 : .1 + i * .01, .09 + i * .035, .05); l.rotation.z = (x < 0 ? 1 : -1) * (.5 + i * .3); } }
    g.userData.iris = iris; return g;
  }
  var eyeL = eye(-.21), eyeR = eye(.21);
  function brow(x){ return add(head, new THREE.BoxGeometry(.2, .036, .03), HAIR, x, .24, .5); }
  var browL = brow(-.21), browR = brow(.21);

  var mouthMat = new THREE.MeshStandardMaterial({color:0x7a2433, roughness:.45, side:THREE.DoubleSide});
  var mouth = add(head, new THREE.TorusGeometry(.13, .024, 8, 28, Math.PI), mouthMat, 0, -.27, .5);
  var blushM = new THREE.MeshBasicMaterial({color:0xFF8FA3, transparent:true, opacity:.4});
  [-1, 1].forEach(function(s){ add(head, new THREE.SphereGeometry(.065, 12, 10), blushM, s*.31, -.12, .47).scale.set(1.3, .7, .3); });

  // glasses
  var FRAME = mat(0x2B1B6B, .3, .5), LENS = new THREE.MeshBasicMaterial({color:0x7BE7F7, transparent:true, opacity:.14, side:THREE.DoubleSide});
  [-.21, .21].forEach(function(x){
    add(head, new THREE.TorusGeometry(.17, .02, 10, 32), FRAME, x, .02, .6);
    add(head, new THREE.CircleGeometry(.17, 28), LENS, x, .02, .6);
  });
  add(head, new THREE.BoxGeometry(.09, .02, .02), FRAME, 0, .06, .6);
  [-1, 1].forEach(function(s){ var a = add(head, new THREE.BoxGeometry(.02, .02, .6), FRAME, s*.39, .04, .3); a.rotation.y = s * .12; });

  // arms
  function arm(side){
    var sh = new THREE.Group(); sh.position.set(side*.76, 1.52, 0); root.add(sh);
    add(sh, new THREE.SphereGeometry(.18, 16, 12), HOOD);
    add(sh, new THREE.CylinderGeometry(.15, .13, .62, 18), HOOD, 0, -.31, 0);
    var el = new THREE.Group(); el.position.set(0, -.62, 0); sh.add(el);
    add(el, new THREE.SphereGeometry(.13, 14, 10), HOOD2);
    add(el, new THREE.CylinderGeometry(.12, .1, .5, 18), HOOD2, 0, -.25, 0);
    var cuff = add(el, new THREE.TorusGeometry(.1, .03, 8, 18), WHITE, 0, -.52, 0); cuff.rotation.x = Math.PI/2;
    add(el, new THREE.SphereGeometry(.125, 18, 14), SKIN, 0, -.64, 0);
    add(el, new THREE.SphereGeometry(.05, 10, 8), SKIN, side*.1, -.62, .06);
    return {sh:sh, el:el};
  }
  var aL = arm(-1), aR = arm(1);

  // ── effects ──
  var confetti = [], palette = [0x7C5CFF, 0x22D3EE, 0xFFC857, 0x34D399, 0xFB7185, 0xffffff];
  if (MOOD === 'correct' && !reduce){
    for (var c = 0; c < 70; c++){
      var m = new THREE.Mesh(new THREE.PlaneGeometry(.07, .12), new THREE.MeshBasicMaterial({color:palette[c % 6], side:THREE.DoubleSide}));
      m.position.set((Math.random() - .5) * .8, 3.2, (Math.random() - .5) * .8);
      m.userData = {vx:(Math.random() - .5) * 2.6, vy:2 + Math.random() * 2.4, vz:(Math.random() - .5) * 1.4, rx:Math.random() * 8, rz:Math.random() * 8, life:2.6 + Math.random() * 1.2, delay:Math.random() * .25};
      m.visible = false; S.add(m); confetti.push(m);
    }
  }
  var qs = [];
  if (MOOD === 'think' && !reduce){
    [0, 1, 2].forEach(function(i){ var s = new THREE.Sprite(new THREE.SpriteMaterial({map:qTex('?', i === 1 ? '#22D3EE' : '#FFC857'), transparent:true, depthWrite:false}));
      s.scale.set(.5, .5, 1); S.add(s); qs.push(s); });
  }
  var drop = null;
  if (MOOD === 'wrong'){
    drop = add(head, new THREE.SphereGeometry(.06, 12, 10), new THREE.MeshStandardMaterial({color:0x7BE7F7, transparent:true, opacity:.85, roughness:.1}), .42, .36, .5);
    drop.scale.set(.8, 1.3, .8);
  }
  var sparks = [];
  if (!reduce){
    for (var k = 0; k < 14; k++){
      var sp = new THREE.Sprite(new THREE.SpriteMaterial({map:glowTex, color:palette[k % 3], transparent:true, opacity:.8, depthWrite:false}));
      sp.scale.set(.18, .18, 1); sp.userData = {x:(Math.random() - .5) * 5, y:Math.random() * 3.5, z:-1 - Math.random() * 1.5, v:.15 + Math.random() * .25, ph:Math.random() * 6};
      S.add(sp); sparks.push(sp);
    }
  }

  // ── input ──
  var look = {x:0, y:0}, tgt = {x:0, y:0}, poke = -10;
  function ptr(e){
    var r = cv.getBoundingClientRect(), p = e.touches ? e.touches[0] : e;
    tgt.x = Math.max(-1, Math.min(1, ((p.clientX - r.left) / r.width - .5) * 2));
    tgt.y = Math.max(-1, Math.min(1, ((p.clientY - r.top) / r.height - .5) * 2));
  }
  window.addEventListener('pointermove', ptr, {passive:true});
  window.addEventListener('touchmove', ptr, {passive:true});
  cv.addEventListener('pointerdown', function(){ poke = clock.elapsedTime; });

  function resize(){
    var w = cv.clientWidth || 300, h = cv.clientHeight || 230;
    R.setSize(w, h, false); cam.aspect = w / h;
    cam.setViewOffset(w, h, SAY ? w * .17 : 0, 0, w, h);
    cam.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);

  function ease(t){ return t < .5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2; }
  function lerp(a, b, k){ return a + (b - a) * k; }
  var clock = new THREE.Clock(), nextBlink = 1.4, blink = 0;
  resize();
  var st = {mouth:0, brow:0, lArmX:0, lArmZ:.12, rArmX:0, rArmZ:-.12, lEl:.2, rEl:.2, hy:0, hx:0, hz:0, jump:0};

  function pose(t){
    var p = {mouth:.05, brow:0, lArmX:0, lArmZ:.12, rArmX:0, rArmZ:-.12, lEl:.2, rEl:.2, hy:0, hx:0, hz:0, jump:0};
    if (MOOD === 'correct'){
      p.mouth = -1; p.brow = .6;
      if (reduce) return p;
      var k = Math.min(t / .5, 1);
      p.lArmZ = lerp(.12, 2.55, ease(k)) + Math.sin(t * 9) * .12 * k; p.rArmZ = lerp(-.12, -2.55, ease(k)) - Math.sin(t * 9) * .12 * k;
      p.lEl = p.rEl = lerp(.2, .35, k);
      p.jump = Math.max(0, Math.sin(t * 7)) * .18 * (t < 3.2 ? 1 : 0);
      p.hx = -.12 * k; p.hz = Math.sin(t * 6) * .05;
    } else if (MOOD === 'wrong'){
      p.mouth = .75; p.brow = -.7;
      if (reduce) return p;
      var s = Math.min(t / .4, 1);
      p.lArmZ = lerp(.12, .55, s); p.rArmZ = lerp(-.12, -.55, s);
      p.lEl = p.rEl = lerp(.2, 1.1, s); p.lArmX = p.rArmX = lerp(0, -.5, s);
      p.hy = t < 1.6 ? Math.sin(t * 11) * .38 * Math.max(0, 1 - t / 1.6) : 0; p.hx = .16 * s;
    } else if (MOOD === 'think'){
      p.mouth = -.05; p.brow = .3;
      var q = ease(Math.min(t / .7, 1));
      p.rArmZ = -.25; p.rArmX = lerp(0, -1.25, q); p.rEl = lerp(.2, 2.1, q);
      p.hz = .08; p.hy = -.25; p.hx = -.08;
    } else {
      p.mouth = -.45; p.brow = .15;
      if (!reduce && (t < 2.4 || t % 9 > 7.2)){ p.rArmZ = -2.35; p.rEl = .7 + Math.sin(t * 10) * .55; p.mouth = -.9; }
    }
    if (!reduce && t - poke < 1.2){ var u = (t - poke) / 1.2; p.jump = Math.max(p.jump, Math.sin(u * Math.PI) * .22); p.mouth = -1; p.rArmZ = -2.35; p.rEl = .7 + Math.sin(t * 14) * .5; }
    return p;
  }

  function tick(){
    requestAnimationFrame(tick);
    var dt = Math.min(clock.getDelta(), .05), t = clock.elapsedTime;
    var P = pose(t), kk = 1 - Math.pow(.0006, dt);
    for (var n in P) st[n] = lerp(st[n], P[n], kk);
    look.x = lerp(look.x, tgt.x, .08); look.y = lerp(look.y, tgt.y, .08);

    root.position.y = .05 + st.jump;
    root.scale.y = 1 + (reduce ? 0 : Math.sin(t * 1.8) * .012);
    root.rotation.y = look.x * .14 + (reduce ? 0 : Math.sin(t * .6) * .04);
    head.rotation.y = st.hy + look.x * .45; head.rotation.x = st.hx + look.y * .25; head.rotation.z = st.hz;
    shadow.scale.setScalar(1 - st.jump * 1.2);

    aL.sh.rotation.z = st.lArmZ; aL.sh.rotation.x = st.lArmX; aL.el.rotation.z = -st.lEl * .3; aL.el.rotation.x = -st.lEl * .6;
    aR.sh.rotation.z = st.rArmZ; aR.sh.rotation.x = st.rArmX; aR.el.rotation.z = st.rEl * .3; aR.el.rotation.x = -st.rEl * .6;

    mouth.scale.y = -st.mouth; mouth.position.y = -.27 + (st.mouth < 0 ? .03 : -.02);
    browL.rotation.z = st.brow * .35; browR.rotation.z = -st.brow * .35;
    browL.position.y = browR.position.y = .24 + Math.max(0, st.brow) * .03;
    [eyeL, eyeR].forEach(function(e){ e.userData.iris.position.set(look.x * .03, -look.y * .02, 0); });
    tail.rotation.x = reduce ? 0 : Math.sin(t * 2.2) * .12 + st.jump * 1.5;
    tail.rotation.z = reduce ? 0 : Math.sin(t * 1.7) * .08 - st.hy * .5;

    if (!reduce){
      nextBlink -= dt;
      if (nextBlink < 0){ blink = .14; nextBlink = 2 + Math.random() * 3; }
      blink = Math.max(0, blink - dt);
    }
    eyeL.scale.y = eyeR.scale.y = blink > 0 ? .08 : 1;

    // stage motion
    ring1.rotation.z = t * .4; ring2.rotation.z = -t * .25;
    orbs.forEach(function(o, i){ o.position.y += Math.sin(t * .5 + i) * .002; });

    sparks.forEach(function(s){ var u = s.userData; var yy = (u.y + t * u.v) % 3.8; s.position.set(u.x + Math.sin(t * .6 + u.ph) * .2, yy, u.z); s.material.opacity = .7 * Math.sin(yy / 3.8 * Math.PI); });
    confetti.forEach(function(m){ var u = m.userData, tt = t - u.delay; if (tt < 0) return;
      if (tt > u.life){ m.visible = false; return; } m.visible = true;
      m.position.set(m.position.x + u.vx * dt, 3.2 + u.vy * tt - 2.6 * tt * tt, m.position.z + u.vz * dt);
      m.rotation.x = u.rx * tt; m.rotation.z = u.rz * tt; });
    qs.forEach(function(s, i){ var a = t * 1.1 + i * 2.09; s.position.set(Math.cos(a) * 1.0, 3.15 + Math.sin(t * 2 + i) * .1, Math.sin(a) * .5); s.material.opacity = .55 + .45 * Math.sin(t * 2 + i); });
    if (drop){ var f = (t * .8) % 1; drop.position.y = .36 - f * .55; drop.material.opacity = .85 * (1 - f * f); }

    R.render(S, cam);
  }
  tick();
})();
</script></body></html>
"""


def _avatar_render(mood="idle", say="", height=230, nonce=None, char="girl"):
    """mood: idle | correct | wrong | think.  char: girl | boy.  `say` = translated bubble text."""
    mood = mood if mood in ("idle", "correct", "wrong", "think") else "idle"
    char = char if char in _AVATAR_NAMES else "girl"
    emoji = {"correct": "🎉", "wrong": "🤗", "think": "🤔"}.get(mood, "🧑‍🏫")
    code = (
        _AVATAR_TEMPLATE.replace("__AVATAR_THREE__", _AVATAR_THREE)
        .replace("__MOOD__", json.dumps(mood))
        .replace("__SAY__", json.dumps(say or ""))
        .replace("__CHAR__", json.dumps(char))
        .replace("__NAME__", html.escape(_AVATAR_NAMES[char]))
        .replace("__EMOJI__", html.escape(emoji))
    )
    if nonce is not None:  # changing comment forces a fresh iframe so the animation replays
        code += f"<!-- {html.escape(str(nonce))} -->"
    components.html(code, height=height)


def _tutor_card(*args, **kwargs):
    with st.container(key="tutor"):
        _avatar_render(*args, **kwargs)


avatar3d = types.SimpleNamespace(render=_tutor_card)
# ───────────────────────────────────────────────────────

try:  # login + database (optional: without it the app runs in guest mode)
    from supabase import create
