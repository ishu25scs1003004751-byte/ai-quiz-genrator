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
    from supabase import create_client
except Exception:  # pragma: no cover
    create_client = None
try:  # keeps the user logged in after a page refresh
    import extra_streamlit_components as stx
except Exception:  # pragma: no cover
    stx = None

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
APP_NAME = "AI Quiz Arena"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded",
)

i18n.init()  # English by default; the saved choice is restored from the browser's localStorage
LIGHT = bool(st.session_state.get("light", False))

# ─────────────────────────────────────────────────────────────
# STYLING — midnight ink, violet→cyan energy, amber highlights
# ─────────────────────────────────────────────────────────────
BASE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;500;600;700&display=swap');
@property --p { syntax:'<number>'; inherits:false; initial-value:0; }

:root{
  --bg:#0B0F1E; --panel:rgba(255,255,255,.045); --panel-2:rgba(255,255,255,.07);
  --line:rgba(255,255,255,.12); --txt:#E8EAF6; --mute:#9AA3C7;
  --violet:#7C5CFF; --cyan:#22D3EE; --amber:#FFC857; --good:#34D399; --bad:#FB7185;
}
html, body, [class*="css"]{ font-family:'Plus Jakarta Sans','Noto Sans Devanagari',sans-serif; color:var(--txt); }
h1,h2,h3,.qf-display{ font-family:'Space Grotesk','Noto Sans Devanagari',sans-serif !important; letter-spacing:-.02em; }
/* Hide watermark but keep the sidebar toggle usable (important on mobile) */
#MainMenu, footer{ visibility:hidden; height:0; }
header[data-testid="stHeader"]{ background:transparent !important; }
[data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarExpandButton"]{
  display:block !important; position:fixed !important; top:12px !important; left:12px !important; z-index:999999 !important;
  background-color:#1f2937 !important; border-radius:8px !important; border:1px solid var(--line) !important;
  box-shadow:0 4px 12px rgba(0,0,0,.5) !important;
}

.stApp{
  background:
    radial-gradient(1100px 560px at 8% -10%, rgba(124,92,255,.25), transparent 60%),
    radial-gradient(900px 480px at 100% 0%, rgba(34,211,238,.15), transparent 55%),
    var(--bg);
}
.block-container{ padding-top:1.4rem; max-width:860px; }
section[data-testid="stSidebar"]{ background:#0E1330; border-right:1px solid var(--line); }

/* Hero */
.qf-hero{
  position:relative; overflow:hidden; border-radius:26px; padding:38px 34px 28px; margin-bottom:18px;
  border:1px solid var(--line);
  background:
    linear-gradient(rgba(255,255,255,.035) 1px, transparent 1px) 0 0/28px 28px,
    linear-gradient(90deg, rgba(255,255,255,.035) 1px, transparent 1px) 0 0/28px 28px,
    linear-gradient(135deg, rgba(124,92,255,.35), rgba(34,211,238,.12) 70%, rgba(11,15,30,.4));
}
.qf-hero:after{
  content:""; position:absolute; width:340px; height:340px; right:-90px; top:-120px; border-radius:50%;
  background:radial-gradient(circle, rgba(255,200,87,.38), transparent 65%); filter:blur(6px);
}
.qf-title{
  font-size:3.3rem; font-weight:700; line-height:1; margin:0; position:relative; z-index:1;
  background:linear-gradient(90deg,#fff 10%,#C9BEFF 45%,#7BE7F7 90%); -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent;
}
.qf-sub{ margin-top:12px; color:#C3C9EA; font-size:1.05rem; max-width:560px; position:relative; z-index:1; }
.qf-steps{ display:flex; gap:8px; margin-top:20px; position:relative; z-index:1; flex-wrap:wrap; }
.qf-step{ padding:6px 14px; border-radius:99px; font-size:.82rem; font-weight:600; color:#AEB6DD; border:1px solid rgba(255,255,255,.18); background:rgba(0,0,0,.2); }
.qf-step.on{ color:#0B0F1E; background:var(--amber); border-color:var(--amber); }
.qf-step.done{ color:var(--good); border-color:rgba(52,211,153,.5); }

/* Glass panels */
.st-key-panel, .st-key-panel_pyq, .st-key-panel_doubt, .st-key-panel_login, .st-key-optbox, .st-key-morebox{
  background:var(--panel); border:1px solid var(--line); border-radius:20px; padding:20px 22px; backdrop-filter:blur(6px);
}
.st-key-optbox{ padding:14px 16px; counter-reset:opt; }

/* Source picker → pills */
.st-key-srcpick div[role="radiogroup"]{ gap:8px; flex-wrap:wrap; }
.st-key-srcpick label[data-baseweb="radio"]{ background:var(--panel); border:1px solid var(--line); border-radius:99px; padding:8px 16px; margin:0; }
.st-key-srcpick label[data-baseweb="radio"]:has(input:checked){ background:rgba(124,92,255,.28); border-color:var(--violet); }
.st-key-srcpick label[data-baseweb="radio"] > div:first-of-type{ display:none; }

/* Answer options → numbered cards */
.st-key-optbox div[role="radiogroup"]{ gap:0; }
.st-key-optbox label[data-baseweb="radio"], .st-key-optbox label[data-baseweb="checkbox"]{
  display:flex; align-items:center; gap:12px;
  background:var(--panel-2); border:1.5px solid var(--line); border-radius:14px; padding:12px 14px; margin:0 0 10px; width:100%;
  transition:border-color .12s, background .12s, transform .08s;
}
.st-key-optbox label[data-baseweb="radio"]::before, .st-key-optbox label[data-baseweb="checkbox"]::before{
  counter-increment:opt; content:counter(opt); flex:0 0 auto; width:28px; height:28px; border-radius:99px;
  display:flex; align-items:center; justify-content:center; font-weight:700; font-size:.85rem;
  background:rgba(124,92,255,.22); color:var(--txt); border:1px solid var(--line);
}
.st-key-optbox label[data-baseweb="radio"] > div:first-of-type{ display:none; }
.st-key-optbox label[data-baseweb="radio"]:hover, .st-key-optbox label[data-baseweb="checkbox"]:hover{ border-color:var(--cyan); transform:translateX(2px); }
.st-key-optbox label:has(input:checked){ border-color:var(--violet); background:rgba(124,92,255,.22); }
.st-key-optbox label:has(input:checked)::before{ background:var(--violet); color:#fff; border-color:var(--violet); }

/* Question card */
@keyframes qf-rise{ from{ opacity:0; transform:translateY(8px); } to{ opacity:1; transform:none; } }
.qf-qcard{
  position:relative; background:linear-gradient(160deg, rgba(124,92,255,.18), rgba(255,255,255,.04));
  border:1px solid var(--line); border-radius:20px; padding:24px 26px; margin:12px 0 12px; animation:qf-rise .35s ease-out;
}
.qf-qcard:before{ content:""; position:absolute; left:0; top:20px; bottom:20px; width:5px; border-radius:0 6px 6px 0; background:var(--amber); }
.qf-qnum{ font-size:.82rem; font-weight:700; color:var(--amber); margin-bottom:8px; }
.qf-qtext{ font-family:'Space Grotesk','Noto Sans Devanagari',sans-serif; font-size:1.4rem; font-weight:500; line-height:1.38; }
.qf-tags{ float:right; display:flex; gap:6px; }
.qf-tag{ font-size:.74rem; padding:3px 11px; border-radius:99px; border:1px solid var(--line); color:var(--mute); }
.qf-tag.lv{ border-color:var(--cyan); color:var(--cyan); }
.qf-kbd{ font-size:.78rem; color:var(--mute); margin:2px 0 12px; }
.qf-kbd kbd{ background:var(--panel-2); border:1px solid var(--line); border-bottom-width:2px; border-radius:6px; padding:1px 7px; font-family:inherit; font-size:.76rem; color:var(--txt); }

.qf-fb{ border-radius:14px; padding:14px 18px; margin:10px 0; }
.qf-fb.ok{ background:rgba(52,211,153,.12); border:1px solid var(--good); }
.qf-fb.no{ background:rgba(251,113,133,.12); border:1px solid var(--bad); }
.qf-fb.mid{ background:rgba(255,200,87,.1); border:1px solid var(--amber); }
.qf-hint{ background:rgba(255,200,87,.1); border:1px dashed var(--amber); border-radius:12px; padding:10px 14px; margin:8px 0; }
.qf-hearts{ text-align:right; font-size:1.15rem; letter-spacing:2px; }

/* Stats */
.qf-tiles{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:14px 0 10px; }
.qf-tile{ background:var(--panel); border:1px solid var(--line); border-radius:16px; padding:14px 10px; text-align:center; }
.qf-tile .v{ font-family:'Space Grotesk',sans-serif; font-size:1.5rem; font-weight:700; }
.qf-tile .l{ font-size:.76rem; color:var(--mute); }
@media (max-width:640px){ .qf-tiles{ grid-template-columns:repeat(2,1fr);} .qf-title{ font-size:2.4rem; } }

.qf-ring{ --t:0; position:relative; width:170px; height:170px; margin:8px auto 6px; display:flex; align-items:center; justify-content:center; }
.qf-ring:before{
  content:""; position:absolute; inset:0; border-radius:50%;
  background:conic-gradient(var(--ring-color) calc(var(--p)*1%), rgba(127,127,160,.25) 0);
  -webkit-mask:radial-gradient(farthest-side, transparent calc(100% - 15px), #000 calc(100% - 14px));
          mask:radial-gradient(farthest-side, transparent calc(100% - 15px), #000 calc(100% - 14px));
  animation:qf-fill 1.3s cubic-bezier(.2,.8,.2,1) forwards;
}
@keyframes qf-fill{ from{ --p:0; } to{ --p:var(--t); } }
.qf-ring-in{ position:relative; text-align:center; }
.qf-ring-in .big{ font-family:'Space Grotesk',sans-serif; font-size:2.5rem; font-weight:700; line-height:1; }
.qf-ring-in .sm{ font-size:.85rem; color:var(--mute); }
@media (prefers-reduced-motion:reduce){ .qf-ring:before{ animation:none; --p:var(--t); } .qf-qcard{ animation:none; } }

.qf-badges{ display:flex; flex-wrap:wrap; gap:8px; justify-content:center; margin:10px 0; }
.qf-badge{ background:rgba(255,200,87,.12); border:1px solid var(--amber); color:var(--amber); border-radius:99px; padding:6px 14px; font-weight:700; font-size:.86rem; }

.qf-flash{
  min-height:210px; display:flex; align-items:center; justify-content:center; text-align:center; margin:12px 0;
  background:linear-gradient(160deg, rgba(124,92,255,.2), rgba(255,255,255,.04)); border:1px solid var(--line);
  border-radius:22px; padding:30px; font-family:'Space Grotesk',sans-serif; font-size:1.45rem; font-weight:500;
}
.qf-flash.back{ border-color:var(--good); background:rgba(52,211,153,.1); }

/* Buttons & inputs */
.stButton>button, .stDownloadButton>button{
  border-radius:13px; font-weight:700; padding:.6rem 1.1rem; border:1px solid var(--line);
  background:var(--panel-2); color:var(--txt); transition:transform .08s ease, border-color .12s;
}
.stButton>button:hover, .stDownloadButton>button:hover{ transform:translateY(-1px); border-color:var(--cyan); }
.stButton>button[kind="primary"], [data-testid="stBaseButton-primary"]{
  background:linear-gradient(135deg,var(--violet),#4F8CFF 55%,var(--cyan)); border:0; color:#fff;
  box-shadow:0 8px 24px rgba(124,92,255,.35);
}
.stButton>button:focus-visible{ outline:3px solid var(--amber); }
.stTextInput input, .stTextArea textarea{ background:rgba(255,255,255,.05) !important; border-radius:12px !important; border:1px solid var(--line) !important; }
div[data-testid="stExpander"]{ background:var(--panel); border:1px solid var(--line); border-radius:14px; }
.stProgress > div > div > div > div{ background-image:linear-gradient(90deg,var(--violet),var(--cyan)); }
iframe{ border:0; }
</style>
"""

LIGHT_CSS = """
<style>
:root{
  --bg:#F4F5FC; --panel:rgba(255,255,255,.78); --panel-2:#FFFFFF;
  --line:rgba(30,35,80,.16); --txt:#1B1F3B; --mute:#5B6390;
}
.stApp{
  background:
    radial-gradient(1000px 500px at 5% -10%, rgba(124,92,255,.14), transparent 60%),
    radial-gradient(800px 420px at 100% 0%, rgba(34,211,238,.12), transparent 55%),
    #F4F5FC !important;
}
section[data-testid="stSidebar"]{ background:#FFFFFF !important; }
.stApp [data-testid="stMarkdownContainer"] :is(p,li,h1,h2,h3,h4,strong,em,span,small):not([class*="qf-"]),
.stApp [data-testid="stWidgetLabel"] *, .stApp [data-testid="stCaptionContainer"] *,
.stApp label, .stApp [data-testid="stExpander"] summary *{ color:var(--txt) !important; }
.stApp [data-testid="stCaptionContainer"] *{ color:var(--mute) !important; }
.stApp button [data-testid="stMarkdownContainer"] *{ color:inherit !important; }
.stApp [data-testid="stBaseButton-primary"], .stApp [data-testid="stBaseButton-primary"] *{ color:#fff !important; }
.qf-hero{ background:linear-gradient(135deg,#4B3FD1,#6D5BFF 55%,#1CA7C9) !important; }
.qf-hero .qf-sub{ color:#E6E9FF !important; }
.qf-hero .qf-step{ color:#fff !important; border-color:rgba(255,255,255,.45); }
.qf-hero .qf-step.on{ color:#0B0F1E !important; }
.qf-badge{ color:#8A5A00; background:rgba(255,200,87,.25); }
.qf-qnum{ color:#B77900; }
.qf-qcard{ background:linear-gradient(160deg, rgba(124,92,255,.12), rgba(255,255,255,.9)); }
.qf-flash{ background:linear-gradient(160deg, rgba(124,92,255,.12), rgba(255,255,255,.9)); }
.qf-tag.lv{ color:#0A7C93; border-color:#0A7C93; }
.stTextInput input, .stTextArea textarea{ background:#fff !important; color:var(--txt) !important; }
div[data-baseweb="select"] > div{ background:#fff !important; }
div[data-baseweb="select"] *{ color:var(--txt) !important; }
.st-key-optbox label[data-baseweb="radio"]::before, .st-key-optbox label[data-baseweb="checkbox"]::before{ background:rgba(124,92,255,.14); }
</style>
"""

# ─────────────────────────────────────────────────────────────
# UI REFRESH — clean, modern, responsive design layer (CSS only; no logic touched)
# Loaded after BASE_CSS / LIGHT_CSS / LANG_CSS so it refines them.
# ─────────────────────────────────────────────────────────────
UI_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap');
@property --p { syntax:'<number>'; inherits:false; initial-value:0; }
:root{
  --ui-bg:#07090F; --ui-surface:#0E1220; --ui-surface-2:#141A31; --ui-surface-3:#1B2242;
  --ui-line:rgba(255,255,255,.075); --ui-line-2:rgba(255,255,255,.14);
  --ui-txt:#ECEEFB; --ui-mute:#9AA2C6; --ui-faint:#6E769D;
  --ui-accent:#7C6BFF; --ui-accent-2:#5B8CFF; --ui-cyan:#22D3EE; --ui-accent-soft:rgba(124,107,255,.16);
  --ui-good:#34D399; --ui-bad:#FB7185; --ui-warn:#FFC857;
  --ui-grad:linear-gradient(135deg,#7C6BFF 0%,#5B8CFF 60%,#22D3EE 130%);
  --ui-r:14px; --ui-r-lg:22px; --ui-ease:cubic-bezier(.2,.8,.2,1);
  --ui-sh1:0 1px 2px rgba(0,0,0,.35); --ui-sh2:0 18px 40px -22px rgba(0,0,0,.75);
  --ui-glow:rgba(124,107,255,.55);
  --bg:var(--ui-bg); --panel:var(--ui-surface); --panel-2:var(--ui-surface-2); --line:var(--ui-line); --txt:var(--ui-txt); --mute:var(--ui-mute);
}
html{ scroll-behavior:smooth; -webkit-text-size-adjust:100%; }
html, body, [class*="css"]{ font-family:'Inter','Noto Sans Devanagari',system-ui,sans-serif !important; }
h1,h2,h3,.qf-display{ font-family:'Plus Jakarta Sans','Noto Sans Devanagari',sans-serif !important; letter-spacing:-.02em; }
body{ -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility; font-feature-settings:"cv11","ss01"; }
:focus-visible{ outline:2px solid var(--ui-accent-2) !important; outline-offset:2px; border-radius:8px; }
::selection{ background:rgba(124,107,255,.45); color:#fff; }

/* ── Canvas: ink + violet glow + faint grid ── */
.stApp{ isolation:isolate; background:
  radial-gradient(1100px 560px at 12% -12%, rgba(124,107,255,.24), transparent 62%),
  radial-gradient(900px 480px at 100% -4%, rgba(34,211,238,.11), transparent 60%),
  var(--ui-bg) !important; }
.stApp::before{ content:""; position:fixed; inset:0; z-index:-1; pointer-events:none;
  background-image:linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px);
  background-size:44px 44px; -webkit-mask-image:radial-gradient(75% 60% at 50% 0%,#000 15%,transparent 78%); mask-image:radial-gradient(75% 60% at 50% 0%,#000 15%,transparent 78%); }
.block-container{ max-width:920px; padding:.6rem clamp(.9rem,3vw,2rem) 5rem !important; }
[data-testid="stVerticalBlock"]{ gap:.9rem; }
h2{ font-size:clamp(1.4rem,3.2vw,1.9rem) !important; font-weight:800; }
h3{ font-size:clamp(1.1rem,2.6vw,1.3rem) !important; font-weight:700; }
[data-testid="stCaptionContainer"]{ color:var(--ui-mute); }
hr{ border-color:var(--ui-line) !important; }
@keyframes qf-rise{ from{ opacity:0; transform:translateY(14px); } to{ opacity:1; transform:none; } }
@keyframes qf-pop{ 0%{ opacity:0; transform:scale(.94); } 100%{ opacity:1; transform:none; } }
@keyframes qf-float{ 0%,100%{ transform:translate3d(0,0,0); } 50%{ transform:translate3d(0,-16px,0); } }
@keyframes qf-shine{ to{ left:130%; } }

header[data-testid="stHeader"]{ background:transparent !important; pointer-events:none; }
header[data-testid="stHeader"] *{ pointer-events:auto; }
/* ── App bar ── */
.st-key-navbar{ flex-direction:row !important; flex-wrap:nowrap !important; align-items:center; justify-content:space-between; gap:12px !important;
  position:sticky; top:0; z-index:60; margin:0 -8px; padding:10px 8px; background:linear-gradient(180deg,rgba(7,9,15,.82),rgba(7,9,15,.55)); backdrop-filter:blur(14px) saturate(1.4); -webkit-backdrop-filter:blur(14px) saturate(1.4);
  border-bottom:1px solid var(--ui-line); }
.st-key-navbar > div{ width:auto !important; flex:0 0 auto; min-width:0; }
.st-key-navbar .st-key-langbar{ margin:0; }
.stApp:has([data-testid="stSidebarCollapsedControl"]) .st-key-navbar{ padding-left:52px; }
.qf-brand{ display:flex; align-items:center; gap:10px; font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:1.02rem; letter-spacing:-.02em; color:var(--ui-txt); white-space:nowrap; }
.qf-brand .mk{ width:32px; height:32px; border-radius:10px; display:grid; place-items:center; background:var(--ui-grad); box-shadow:0 8px 20px -8px var(--ui-glow), inset 0 1px 0 rgba(255,255,255,.35); }
.qf-brand .mk svg{ width:18px; height:18px; stroke:#fff; fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
.qf-brand small{ font-family:'Inter',sans-serif; font-weight:600; font-size:.68rem; padding:2px 8px; border-radius:99px; color:var(--ui-mute); border:1px solid var(--ui-line-2); letter-spacing:.02em; }
.st-key-lang_sw_top div[role="radiogroup"]{ background:var(--ui-surface) !important; border-color:var(--ui-line-2) !important; }
.st-key-lang_sw_top label[data-baseweb="radio"]{ padding:5px 14px !important; font-size:.84rem; }

/* ── Hero / dashboard header ── */
.qf-hero{ position:relative; overflow:hidden; display:grid; grid-template-columns:1fr auto; gap:22px; align-items:center;
  margin:14px 0 6px; padding:clamp(22px,4vw,38px); border-radius:var(--ui-r-lg); border:1px solid rgba(255,255,255,.11);
  background:linear-gradient(135deg,rgba(124,107,255,.30),rgba(91,140,255,.12) 55%,rgba(34,211,238,.10)),var(--ui-surface) !important;
  box-shadow:0 40px 80px -50px var(--ui-glow), inset 0 1px 0 rgba(255,255,255,.09); }
.qf-hero:before{ content:""; position:absolute; inset:0; pointer-events:none; opacity:.55;
  background-image:linear-gradient(rgba(255,255,255,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.06) 1px,transparent 1px); background-size:30px 30px;
  -webkit-mask-image:radial-gradient(90% 100% at 85% 0%,#000 10%,transparent 75%); mask-image:radial-gradient(90% 100% at 85% 0%,#000 10%,transparent 75%); }
.qf-hero:after{ display:none; }
.qf-blob{ position:absolute; border-radius:50%; pointer-events:none; filter:blur(40px); }
.qf-blob.b1{ width:260px; height:260px; right:-60px; top:-90px; background:rgba(124,107,255,.55); animation:qf-float 9s ease-in-out infinite; }
.qf-blob.b2{ width:200px; height:200px; right:18%; bottom:-110px; background:rgba(34,211,238,.32); animation:qf-float 11s ease-in-out -3s infinite; }
.qf-hero > *{ position:relative; z-index:1; }
.qf-hero > .qf-blob{ position:absolute; z-index:0; }
.qf-eyebrow{ display:inline-flex; align-items:center; gap:8px; padding:5px 12px; border-radius:99px; font-size:.78rem; font-weight:600; color:#DCD8FF; background:rgba(255,255,255,.08); border:1px solid rgba(255,255,255,.14); margin-bottom:14px; max-width:100%; }
.qf-eyebrow .dot{ width:7px; height:7px; border-radius:50%; background:var(--ui-good); box-shadow:0 0 0 4px rgba(52,211,153,.22); flex:0 0 auto; }
.qf-eyebrow span.nm{ overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.qf-title{ display:block; font-size:clamp(1.65rem,4.6vw,2.7rem); font-weight:800; line-height:1.08; margin:0; max-width:18ch;
  background:linear-gradient(180deg,#fff 20%,#C9CCFF) !important; -webkit-background-clip:text !important; background-clip:text !important; -webkit-text-fill-color:transparent !important; }
.qf-title:before{ display:none; }
.qf-sub{ margin-top:12px; color:rgba(236,238,251,.78) !important; font-size:clamp(.92rem,2.2vw,1.04rem); max-width:56ch; line-height:1.6; }
.qf-steps{ display:flex; flex-wrap:nowrap; align-items:center; gap:0; margin-top:20px; overflow-x:auto; scrollbar-width:none; padding:2px 2px 4px; }
.qf-steps::-webkit-scrollbar{ display:none; }
.qf-step{ position:relative; display:inline-flex; align-items:center; gap:8px; flex:0 0 auto; padding:5px 13px 5px 5px; border-radius:99px; white-space:nowrap;
  font-size:.8rem; font-weight:600; color:var(--ui-mute) !important; background:rgba(255,255,255,.05) !important; border:1px solid rgba(255,255,255,.1) !important; transition:all .3s var(--ui-ease); }
.qf-step + .qf-step{ margin-left:20px; }
.qf-step + .qf-step:before{ content:""; position:absolute; left:-20px; top:50%; width:20px; height:1px; background:rgba(255,255,255,.2); }
.qf-step i{ font-style:normal; width:22px; height:22px; border-radius:50%; display:grid; place-items:center; font-size:.72rem; font-weight:700; background:rgba(255,255,255,.1); color:var(--ui-txt); }
.qf-step.on{ color:#fff !important; background:rgba(124,107,255,.28) !important; border-color:rgba(160,148,255,.7) !important; box-shadow:0 8px 22px -10px var(--ui-glow); }
.qf-step.on i{ background:var(--ui-grad); color:#fff; }
.qf-step.done{ color:#BFF6DC !important; background:rgba(52,211,153,.12) !important; border-color:rgba(52,211,153,.4) !important; }
.qf-step.done i{ background:var(--ui-good); color:#052E20; }
.qf-xp{ display:flex; align-items:center; gap:14px; padding:14px 18px; border-radius:18px; background:rgba(255,255,255,.07); border:1px solid rgba(255,255,255,.14); backdrop-filter:blur(12px); min-width:200px; }
.qf-xpring{ --p:0; position:relative; width:58px; height:58px; border-radius:50%; flex:0 0 auto; display:grid; place-items:center; background:conic-gradient(var(--ui-warn) calc(var(--p)*1%), rgba(255,255,255,.14) 0); }
.qf-xpring:before{ content:""; position:absolute; inset:5px; border-radius:50%; background:#121836; }
.qf-xpring b{ position:relative; font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:1.2rem; color:#fff; }
.qf-xp .a{ font-weight:700; font-size:.98rem; color:#fff; } .qf-xp .b{ font-size:.78rem; color:var(--ui-mute); margin-top:2px; }
.qf-hero.compact{ grid-template-columns:1fr; padding:14px 18px; margin:12px 0 4px; }
.qf-hero.compact .qf-eyebrow, .qf-hero.compact .qf-title, .qf-hero.compact .qf-sub, .qf-hero.compact .qf-xp{ display:none; }
.qf-hero.compact .qf-steps{ margin-top:0; }
.qf-hero.plain{ grid-template-columns:1fr; }
.qf-hero.plain .qf-title{ max-width:none; }

/* ── KPI cards ── */
.qf-kpis{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
.qf-kpi{ --c:#7C6BFF; --cs:rgba(124,107,255,.16); position:relative; overflow:hidden; padding:16px 16px 14px; border-radius:18px; background:var(--ui-surface); border:1px solid var(--ui-line); box-shadow:var(--ui-sh1);
  transition:transform .3s var(--ui-ease), border-color .3s, box-shadow .3s; }
.qf-kpi:hover{ transform:translateY(-4px); border-color:color-mix(in srgb,var(--c) 55%,transparent); box-shadow:0 22px 44px -26px var(--c); }
.qf-kpi:before{ content:""; position:absolute; right:-30px; top:-30px; width:100px; height:100px; border-radius:50%; background:var(--cs); filter:blur(22px); opacity:.8; }
.qf-kpi.k2{ --c:#FFC857; --cs:rgba(255,200,87,.16); } .qf-kpi.k3{ --c:#22D3EE; --cs:rgba(34,211,238,.15); } .qf-kpi.k4{ --c:#34D399; --cs:rgba(52,211,153,.15); }
.qf-kpi .ic{ position:relative; width:36px; height:36px; border-radius:11px; display:grid; place-items:center; color:var(--c); background:var(--cs); border:1px solid color-mix(in srgb,var(--c) 30%,transparent); }
.qf-kpi .ic svg{ width:18px; height:18px; stroke:currentColor; fill:none; stroke-width:2; stroke-linecap:round; stroke-linejoin:round; }
.qf-kpi .v{ position:relative; margin-top:14px; font-family:'Plus Jakarta Sans',sans-serif; font-size:clamp(1.55rem,3.6vw,2rem); font-weight:800; letter-spacing:-.03em; line-height:1; font-variant-numeric:tabular-nums; }
.qf-kpi .l{ position:relative; margin-top:6px; font-size:.76rem; font-weight:500; color:var(--ui-mute); }
.qf-kpi .bar{ position:relative; height:4px; border-radius:99px; background:rgba(255,255,255,.09); margin-top:12px; overflow:hidden; }
.qf-kpi .bar i{ display:block; height:100%; border-radius:99px; background:var(--c); }

/* ── Activity card ── */
.qf-card{ padding:18px 18px 8px; border-radius:var(--ui-r-lg); background:var(--ui-surface); border:1px solid var(--ui-line); box-shadow:var(--ui-sh1); }
.qf-card .hd{ font-family:'Plus Jakarta Sans',sans-serif; font-weight:700; font-size:.95rem; margin-bottom:6px; display:flex; align-items:center; gap:8px; }
.qf-card .hd:before{ content:""; width:6px; height:16px; border-radius:4px; background:var(--ui-grad); }
.qf-act{ display:grid; grid-template-columns:auto 1fr auto; gap:6px 14px; align-items:center; padding:11px 0; border-top:1px solid var(--ui-line); }
.qf-act:first-of-type{ border-top:0; }
.qf-act .pct{ grid-row:1 / span 2; grid-column:1; width:46px; height:46px; border-radius:13px; display:grid; place-items:center; font-weight:800; font-size:.84rem; color:var(--cc); background:color-mix(in srgb,var(--cc) 14%,transparent); border:1px solid color-mix(in srgb,var(--cc) 32%,transparent); }
.qf-act .t{ grid-column:2; font-weight:600; font-size:.94rem; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.qf-act .s{ grid-column:2; font-size:.78rem; color:var(--ui-mute); }
.qf-act .w{ grid-column:3; grid-row:1 / span 2; width:64px; height:5px; border-radius:99px; background:rgba(255,255,255,.1); overflow:hidden; }
.qf-act .w i{ display:block; height:100%; background:var(--cc); border-radius:99px; }
.qf-empty{ display:flex; gap:14px; align-items:center; padding:20px; border-radius:var(--ui-r-lg); border:1.5px dashed var(--ui-line-2); background:rgba(255,255,255,.02); color:var(--ui-mute); font-size:.92rem; line-height:1.5; }
.qf-empty .ei{ flex:0 0 auto; width:44px; height:44px; border-radius:13px; display:grid; place-items:center; font-size:1.3rem; background:var(--ui-accent-soft); }

.qf-kpi .v, .qf-act .t, .qf-card .hd, .qf-brand, .qf-tile .v{ color:var(--ui-txt); } .qf-kpi .l, .qf-act .s, .qf-empty{ color:var(--ui-mute); }
.qf-act.g{ --cc:#34D399; } .qf-act.m{ --cc:#FFC857; } .qf-act.b{ --cc:#FB7185; }

/* ── Tutor card ── */
.st-key-tutor{ position:relative; background:linear-gradient(135deg,rgba(124,107,255,.15),rgba(34,211,238,.05) 70%),var(--ui-surface); border:1px solid var(--ui-line); border-radius:var(--ui-r-lg); padding:2px 6px; overflow:hidden; box-shadow:var(--ui-sh2); }
.st-key-tutor iframe{ display:block; width:100%; background:transparent; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"]{ gap:4px; padding:5px; border-radius:16px; background:var(--ui-surface); border:1px solid var(--ui-line); overflow-x:auto; scrollbar-width:none; box-shadow:var(--ui-sh1); }
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar{ display:none; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"]{ display:none !important; }
.stTabs button[data-baseweb="tab"]{ flex:1 1 auto; height:44px; padding:0 16px; border-radius:11px; justify-content:center; white-space:nowrap; color:var(--ui-mute); transition:background .25s var(--ui-ease), color .2s, box-shadow .25s; }
.stTabs button[data-baseweb="tab"] p{ font-weight:600; font-size:.92rem; }
.stTabs button[data-baseweb="tab"]:hover{ color:var(--ui-txt); background:rgba(255,255,255,.05); }
.stTabs button[data-baseweb="tab"][aria-selected="true"]{ color:#fff; background:var(--ui-grad); box-shadow:0 10px 24px -10px var(--ui-glow), inset 0 1px 0 rgba(255,255,255,.3); }
.stTabs [data-baseweb="tab-panel"]{ padding-top:1.1rem; }

/* ── Surfaces ── */
.st-key-panel, .st-key-panel_pyq, .st-key-panel_doubt, .st-key-panel_login, .st-key-morebox{
  position:relative; background:linear-gradient(180deg,rgba(255,255,255,.03),transparent 40%),var(--ui-surface); border:1px solid var(--ui-line); border-radius:var(--ui-r-lg);
  padding:clamp(16px,2.8vw,24px); box-shadow:var(--ui-sh2); backdrop-filter:none; transition:border-color .3s; }
.st-key-panel:hover, .st-key-panel_pyq:hover, .st-key-panel_doubt:hover{ border-color:var(--ui-line-2); }
.st-key-panel_login{ max-width:520px; margin:10px auto 0; }
.st-key-optbox{ background:transparent; border:0; padding:0; box-shadow:none; backdrop-filter:none; }
div[data-testid="stExpander"]{ background:var(--ui-surface); border:1px solid var(--ui-line); border-radius:var(--ui-r); overflow:hidden; transition:border-color .2s; }
div[data-testid="stExpander"]:hover{ border-color:var(--ui-line-2); }
div[data-testid="stExpander"] summary{ font-weight:600; padding:.75rem 1rem; }
div[data-testid="stExpander"] summary:hover{ background:rgba(255,255,255,.03); }
[data-testid="stAlert"]{ border-radius:var(--ui-r); border:1px solid var(--ui-line); animation:qf-pop .35s var(--ui-ease) both; }
[data-testid="stChatMessage"]{ background:var(--ui-surface); border:1px solid var(--ui-line); border-radius:var(--ui-r); padding:12px 14px; }
[data-testid="stSpinner"] > div{ color:var(--ui-mute); }

/* ── Buttons ── */
.stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"]>button{
  position:relative; overflow:hidden; min-height:46px; border-radius:12px; padding:.55rem 1.1rem; font-weight:600; font-size:.94rem; letter-spacing:-.005em;
  background:var(--ui-surface-2); color:var(--ui-txt); border:1px solid var(--ui-line-2); box-shadow:var(--ui-sh1);
  transition:transform .18s var(--ui-ease), border-color .18s, background .18s, box-shadow .25s; }
.stButton>button:hover, .stDownloadButton>button:hover{ border-color:rgba(160,148,255,.7); background:var(--ui-accent-soft); transform:translateY(-2px); box-shadow:0 12px 26px -16px var(--ui-glow); }
.stButton>button:active, .stDownloadButton>button:active{ transform:translateY(0) scale(.98); }
.stButton>button:disabled, .stDownloadButton>button:disabled{ opacity:.42; transform:none; cursor:not-allowed; box-shadow:none; }
.stButton>button[kind="primary"], [data-testid="stBaseButton-primary"]{ background:var(--ui-grad) !important; border:0 !important; color:#fff !important; font-weight:700;
  box-shadow:0 14px 30px -12px var(--ui-glow), inset 0 1px 0 rgba(255,255,255,.3); }
.stButton>button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover{ filter:brightness(1.1); transform:translateY(-2px); box-shadow:0 20px 40px -14px var(--ui-glow), inset 0 1px 0 rgba(255,255,255,.35); }
.stButton>button[kind="primary"]::after, [data-testid="stBaseButton-primary"]::after{ content:""; position:absolute; top:0; left:-70%; width:40%; height:100%; transform:skewX(-20deg);
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.35),transparent); pointer-events:none; }
.stButton>button[kind="primary"]:hover::after, [data-testid="stBaseButton-primary"]:hover::after{ animation:qf-shine .8s var(--ui-ease); }

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea, .stNumberInput input{ border-radius:12px !important; border:1px solid var(--ui-line-2) !important; background:var(--ui-surface-2) !important; font-size:.97rem; transition:border-color .2s, box-shadow .2s; }
.stTextInput input:focus, .stTextArea textarea:focus, .stNumberInput input:focus{ border-color:var(--ui-accent) !important; box-shadow:0 0 0 4px rgba(124,107,255,.22) !important; }
div[data-baseweb="select"] > div{ border-radius:12px !important; border-color:var(--ui-line-2) !important; background:var(--ui-surface-2); min-height:44px; transition:border-color .2s, box-shadow .2s; }
div[data-baseweb="select"] > div:focus-within{ border-color:var(--ui-accent) !important; box-shadow:0 0 0 4px rgba(124,107,255,.22); }
[data-testid="stWidgetLabel"] p, .stSlider label p{ font-weight:600; font-size:.86rem; color:var(--ui-txt); }
[data-testid="stFileUploaderDropzone"]{ border:1.5px dashed rgba(124,107,255,.5) !important; border-radius:var(--ui-r) !important; background:rgba(124,107,255,.06) !important; transition:background .2s, transform .2s; }
[data-testid="stFileUploaderDropzone"]:hover{ background:rgba(124,107,255,.13) !important; transform:scale(1.005); }
.st-key-srcpick div[role="radiogroup"]{ gap:8px; flex-wrap:wrap; }
.st-key-srcpick label[data-baseweb="radio"]{ padding:10px 18px; font-weight:600; font-size:.9rem; background:var(--ui-surface); border:1px solid var(--ui-line-2); border-radius:99px; transition:all .2s var(--ui-ease); }
.st-key-srcpick label[data-baseweb="radio"]:hover{ border-color:var(--ui-accent); transform:translateY(-2px); }
.st-key-srcpick label[data-baseweb="radio"]:has(input:checked){ background:var(--ui-accent-soft); border-color:var(--ui-accent); box-shadow:0 10px 24px -14px var(--ui-glow); }

/* ── Progress ── */
.stProgress > div > div{ background:rgba(255,255,255,.08) !important; border-radius:99px; height:8px; }
.stProgress > div > div > div > div{ border-radius:99px; background-size:200% 100%; background-image:linear-gradient(90deg,#7C6BFF,#22D3EE,#7C6BFF); animation:qf-bar 4s linear infinite; }
@keyframes qf-bar{ to{ background-position:-200% 0; } }

/* ── Question ── */
.qf-qcard{ position:relative; margin:6px 0 10px; padding:clamp(20px,3.2vw,30px) clamp(18px,3.6vw,30px) clamp(20px,3vw,28px) clamp(22px,3.6vw,32px); border-radius:var(--ui-r-lg);
  background:linear-gradient(145deg,rgba(124,107,255,.14),transparent 55%),var(--ui-surface); border:1px solid var(--ui-line-2); box-shadow:0 30px 60px -38px var(--ui-glow); }
.qf-qcard:before{ content:""; position:absolute; left:0; top:22px; bottom:22px; width:4px; border-radius:0 6px 6px 0; background:var(--ui-grad); }
.qf-qnum{ color:var(--ui-accent-2); font-size:.82rem; font-weight:700; margin-bottom:10px; letter-spacing:.01em; }
.qf-qtext{ font-family:'Plus Jakarta Sans','Noto Sans Devanagari',sans-serif; font-size:clamp(1.15rem,2.9vw,1.42rem); line-height:1.45; font-weight:600; letter-spacing:-.01em; }
.qf-tags{ gap:6px; flex-wrap:wrap; justify-content:flex-end; max-width:58%; }
.qf-tag{ font-size:.7rem; font-weight:600; padding:3px 10px; background:rgba(255,255,255,.05); color:var(--ui-mute); border:1px solid var(--ui-line-2); backdrop-filter:blur(6px); }
.qf-tag.lv{ color:#7BE7F7; border-color:rgba(123,231,247,.4); }
.st-key-optbox label[data-baseweb="radio"], .st-key-optbox label[data-baseweb="checkbox"]{ min-height:54px; margin:0 0 10px; padding:12px 14px; cursor:pointer; font-size:.98rem; line-height:1.4;
  background:var(--ui-surface); border:1.5px solid var(--ui-line-2); border-radius:var(--ui-r); transition:border-color .18s, background .18s, transform .18s var(--ui-ease), box-shadow .25s; }
.st-key-optbox label[data-baseweb="radio"]:hover, .st-key-optbox label[data-baseweb="checkbox"]:hover{ border-color:var(--ui-accent); background:var(--ui-surface-2); transform:translateX(4px); box-shadow:0 12px 28px -18px var(--ui-glow); }
.st-key-optbox label:has(input:checked){ border-color:var(--ui-accent); background:var(--ui-accent-soft); box-shadow:0 0 0 3px rgba(124,107,255,.2), 0 14px 30px -16px var(--ui-glow); transform:none; }
.st-key-optbox label[data-baseweb="radio"]::before, .st-key-optbox label[data-baseweb="checkbox"]::before{ width:32px; height:32px; border-radius:10px; background:rgba(124,107,255,.16); border:1px solid var(--ui-line-2); transition:transform .2s var(--ui-ease), background .2s; }
.st-key-optbox label:has(input:checked)::before{ background:var(--ui-grad); color:#fff; border-color:transparent; transform:scale(1.08); }
.qf-kbd{ font-size:.74rem; color:var(--ui-faint); }
.qf-fb{ position:relative; overflow:hidden; border-radius:var(--ui-r); padding:15px 18px 15px 22px; line-height:1.6; box-shadow:none; animation:qf-pop .35s var(--ui-ease) both; }
.qf-fb:before{ content:""; position:absolute; left:0; top:0; bottom:0; width:4px; }
.qf-fb.ok:before{ background:var(--ui-good); } .qf-fb.no:before{ background:var(--ui-bad); } .qf-fb.mid:before{ background:var(--ui-warn); }
.qf-hint{ border-radius:var(--ui-r); }
.qf-hearts{ filter:none; }

/* ── Results ── */
.qf-ring{ width:190px; height:190px; filter:drop-shadow(0 0 26px var(--ring-color)); }
.qf-ring-in .big{ font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:2.8rem; letter-spacing:-.04em; }
.qf-tiles{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:6px 0; }
.qf-tile{ position:relative; overflow:hidden; padding:15px 10px 13px; border-radius:16px; text-align:center; background:var(--ui-surface); border:1px solid var(--ui-line); box-shadow:var(--ui-sh1);
  transition:transform .3s var(--ui-ease), border-color .3s, box-shadow .3s; }
.qf-tile:hover{ transform:translateY(-3px); border-color:rgba(160,148,255,.5); box-shadow:0 18px 38px -24px var(--ui-glow); }
.qf-tile .v{ font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:clamp(1.25rem,3.2vw,1.65rem); letter-spacing:-.03em; font-variant-numeric:tabular-nums; }
.qf-tile .l{ font-size:.76rem; color:var(--ui-mute); margin-top:4px; font-weight:500; }
.qf-flash{ border-radius:var(--ui-r-lg); background:linear-gradient(145deg,rgba(124,107,255,.14),transparent 60%),var(--ui-surface); border:1px solid var(--ui-line-2); box-shadow:var(--ui-sh2); font-family:'Plus Jakarta Sans','Noto Sans Devanagari',sans-serif; font-size:clamp(1.15rem,3vw,1.5rem); font-weight:600; }
.qf-badge{ font-size:.82rem; padding:6px 14px; animation:qf-pop .6s var(--ui-ease) both; }

/* ── Sidebar ── */
section[data-testid="stSidebar"]{ background:linear-gradient(180deg,#0C1022,#090C18) !important; border-right:1px solid var(--ui-line); box-shadow:none; }
section[data-testid="stSidebar"] > div{ padding-top:.4rem; }
section[data-testid="stSidebar"] [data-testid="stVerticalBlock"]{ gap:.7rem; }
section[data-testid="stSidebar"] h3{ font-size:1.02rem !important; font-weight:700; margin:.8rem 0 .1rem; padding-bottom:.4rem; border-bottom:1px solid var(--ui-line); }
section[data-testid="stSidebar"] hr{ margin:.9rem 0; }
section[data-testid="stSidebar"] .stProgress > div > div{ height:6px; }
[data-testid="stSidebarCollapsedControl"], [data-testid="stSidebarExpandButton"]{ background:var(--ui-surface) !important; border:1px solid var(--ui-line-2) !important; border-radius:12px !important; box-shadow:var(--ui-sh2) !important; top:12px !important; left:10px !important; }

*::-webkit-scrollbar{ width:9px; height:9px; } *::-webkit-scrollbar-thumb{ background:rgba(154,162,198,.3); border-radius:99px; border:2px solid transparent; background-clip:padding-box; } *::-webkit-scrollbar-track{ background:transparent; }

@media (hover:none){ .qf-kbd{ display:none; } .st-key-optbox label:hover{ transform:none !important; } }
@media (max-width:900px){ .block-container{ max-width:100%; } }
@media (max-width:760px){ .qf-kpis, .qf-tiles{ grid-template-columns:repeat(2,1fr); } .qf-hero{ grid-template-columns:1fr; } .qf-xp{ min-width:0; } }
@media (max-width:640px){
  .block-container{ padding-top:.2rem !important; }
  [data-testid="stVerticalBlock"]{ gap:.75rem; } [data-testid="stHorizontalBlock"]{ gap:.6rem !important; }
  .qf-brand small{ display:none; }
  .st-key-navbar{ padding-left:48px; margin:0 -4px; }
  .qf-hero{ padding:20px 18px; border-radius:20px; } .qf-hero.compact{ padding:12px 14px; }
  .qf-kpi{ padding:13px; } .qf-kpi .v{ margin-top:10px; }
  .qf-tags{ float:none; max-width:100%; justify-content:flex-start; margin-bottom:10px; }
  .qf-qcard{ border-radius:18px; }
  .stTabs button[data-baseweb="tab"]{ padding:0 10px; height:42px; } .stTabs button[data-baseweb="tab"] p{ font-size:.8rem; }
  .stButton>button, .stDownloadButton>button{ min-height:50px; }
  .st-key-optbox label[data-baseweb="radio"], .st-key-optbox label[data-baseweb="checkbox"]{ min-height:56px; }
  .qf-ring{ width:164px; height:164px; } .qf-act .w{ width:44px; }
}

/* ══ Polish pass: readability, touch comfort, mobile sidebar, steady layout ══ */
.block-container{ max-width:880px; }
p, li{ line-height:1.62; }
[data-testid="stMarkdownContainer"] p{ max-width:72ch; }
.qf-qtext, .qf-flash{ max-width:none; }
[data-testid="stMarkdownContainer"] a{ color:var(--ui-accent-2); text-underline-offset:3px; }

/* hero: quieter, clearer hierarchy */
.qf-title{ max-width:20ch; }
.qf-hero{ box-shadow:0 30px 70px -52px var(--ui-glow), inset 0 1px 0 rgba(255,255,255,.08); }
.qf-blob.b1{ opacity:.8; } .qf-blob.b2{ opacity:.7; }
.qf-step.on{ box-shadow:0 6px 18px -10px var(--ui-glow); }
.qf-xp{ box-shadow:0 14px 30px -22px rgba(0,0,0,.7); }

/* cards: consistent radius + one shadow level */
.qf-kpi, .qf-tile, .qf-card, .qf-empty{ border-radius:16px; }
.qf-kpi:hover, .qf-tile:hover{ transform:translateY(-2px); }
.qf-act{ transition:background .2s; border-radius:10px; }
.qf-act:hover{ background:rgba(255,255,255,.03); }

/* tabs: clearer active state, comfortable targets */
.stTabs [data-baseweb="tab-list"]{ position:sticky; top:62px; z-index:40; backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px); }
.stTabs button[data-baseweb="tab"]{ min-height:44px; }

/* buttons: consistent sizing, clear disabled + keyboard focus */
.stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"]>button{ min-height:46px; }
.stButton>button:focus-visible, .stDownloadButton>button:focus-visible{ outline:2px solid var(--ui-accent-2) !important; outline-offset:2px; }
.stButton>button[kind="primary"]:disabled, [data-testid="stBaseButton-primary"]:disabled{ filter:saturate(.5); opacity:.5; box-shadow:none; }

/* answer options: bigger tap area, clear selected state, no sideways jump on touch */
.st-key-optbox label[data-baseweb="radio"], .st-key-optbox label[data-baseweb="checkbox"]{ min-height:56px; }
.st-key-optbox label[data-baseweb="radio"] p, .st-key-optbox label[data-baseweb="checkbox"] p{ font-size:.98rem; line-height:1.45; }

/* inputs: labels and helper text easier to read */
[data-testid="stWidgetLabel"] p{ font-size:.88rem; }
[data-testid="stCaptionContainer"] p, small{ font-size:.8rem; line-height:1.5; }
textarea{ line-height:1.55 !important; }

/* feedback + alerts */
.qf-fb{ font-size:.96rem; }
[data-testid="stAlert"]{ padding:.2rem .35rem; }

/* sidebar: tidy sections, full-width controls */
section[data-testid="stSidebar"] .stButton>button, section[data-testid="stSidebar"] .stDownloadButton>button{ min-height:42px; font-size:.9rem; }
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p{ font-size:.84rem; }
section[data-testid="stSidebar"] [data-testid="stExpander"]{ background:rgba(255,255,255,.025); }

/* navbar: slightly more compact, keeps brand + language switch on one line */
.st-key-navbar{ padding-top:8px; padding-bottom:8px; }

@media (max-width:640px){
  /* 16px inputs stop iOS from zooming the page on focus */
  .stTextInput input, .stTextArea textarea, .stNumberInput input, div[data-baseweb="select"] input{ font-size:16px !important; }
  section[data-testid="stSidebar"]{ width:min(88vw,340px) !important; min-width:0 !important; }
  .stTabs [data-baseweb="tab-list"]{ top:56px; }
  .qf-title{ max-width:none; }
  .qf-sub{ font-size:.92rem; }
  .qf-kpi .v{ font-size:1.5rem; }
  [data-testid="stHorizontalBlock"]{ flex-wrap:wrap !important; }
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{ min-width:calc(50% - .5rem) !important; flex:1 1 calc(50% - .5rem) !important; }
  .qf-card{ padding:14px 14px 6px; }
  .st-key-panel, .st-key-panel_pyq, .st-key-panel_doubt, .st-key-panel_login, .st-key-morebox{ border-radius:18px; }
}
@media (max-width:380px){
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"]{ min-width:100% !important; flex:1 1 100% !important; }
  .qf-kpis, .qf-tiles{ grid-template-columns:1fr 1fr; gap:8px; }
}
@media (min-width:1100px){ .block-container{ max-width:940px; } }
@media (prefers-reduced-motion:reduce){ *,*::before,*::after{ animation:none !important; transition:none !important; scroll-behavior:auto !important; } }
</style>
"""

UI_LIGHT_CSS = """
<style>
:root{
  --ui-bg:#F5F6FB; --ui-surface:#FFFFFF; --ui-surface-2:#F6F7FC; --ui-surface-3:#EEF0FA;
  --ui-line:rgba(22,28,72,.09); --ui-line-2:rgba(22,28,72,.17);
  --ui-txt:#171B38; --ui-mute:#575F8C; --ui-faint:#7C84AC; --ui-accent-soft:rgba(124,107,255,.10);
  --ui-sh1:0 1px 2px rgba(22,28,72,.07); --ui-sh2:0 18px 40px -26px rgba(22,28,72,.35); --ui-glow:rgba(110,90,240,.38);
}
.stApp{ background:radial-gradient(1000px 520px at 12% -12%, rgba(124,107,255,.16), transparent 62%), radial-gradient(800px 420px at 100% -4%, rgba(34,211,238,.09), transparent 60%), #F5F6FB !important; }
.stApp::before{ background-image:linear-gradient(rgba(22,28,72,.04) 1px,transparent 1px),linear-gradient(90deg,rgba(22,28,72,.04) 1px,transparent 1px); }
.st-key-navbar{ background:linear-gradient(180deg,rgba(245,246,251,.92),rgba(245,246,251,.65)); }
.qf-hero{ background:linear-gradient(135deg,#4A3DE0 0%,#5B55F0 50%,#2F86E8 100%) !important; border-color:rgba(255,255,255,.25); box-shadow:0 36px 70px -44px rgba(74,61,224,.8), inset 0 1px 0 rgba(255,255,255,.3); }
.qf-hero .qf-title{ background:none !important; -webkit-text-fill-color:#fff !important; color:#fff !important; }
.qf-hero .qf-sub{ color:rgba(255,255,255,.9) !important; }
.qf-hero .qf-eyebrow{ color:#fff; background:rgba(255,255,255,.16); border-color:rgba(255,255,255,.3); }
.qf-hero .qf-step{ color:rgba(255,255,255,.88) !important; background:rgba(255,255,255,.12) !important; border-color:rgba(255,255,255,.28) !important; }
.qf-hero .qf-step i{ background:rgba(255,255,255,.2); color:#fff; }
.qf-hero .qf-step.on{ color:#2A1F9A !important; background:#fff !important; border-color:#fff !important; }
.qf-hero .qf-step.on i{ background:var(--ui-grad); color:#fff; }
.qf-hero .qf-step.done{ color:#D6FFEC !important; background:rgba(52,211,153,.28) !important; }
.qf-hero .qf-xp{ background:rgba(255,255,255,.16); border-color:rgba(255,255,255,.3); }
.qf-hero .qf-xp .b{ color:rgba(255,255,255,.85); }
.qf-hero .qf-xpring:before{ background:#4B44D8; }
.qf-kpi:before{ opacity:.55; }
.qf-act.g{ --cc:#0B8F63; } .qf-act.m{ --cc:#B77900; } .qf-act.b{ --cc:#D6304F; }
.qf-act .pct{ background:color-mix(in srgb,var(--cc) 12%,#fff); }
.qf-act .w{ background:rgba(22,28,72,.09); }
.qf-kpi .bar{ background:rgba(22,28,72,.09); }
.st-key-tutor{ background:linear-gradient(135deg,rgba(124,107,255,.10),rgba(34,211,238,.05) 70%),#fff; }
.st-key-tutor + * { }
.stTabs button[data-baseweb="tab"]:hover{ background:rgba(124,107,255,.08); }
.stTabs button[data-baseweb="tab"][aria-selected="true"], .stTabs button[data-baseweb="tab"][aria-selected="true"] p{ color:#fff !important; }
.stButton>button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]){ color:var(--ui-txt) !important; background:#fff; }
.stTextInput input, .stTextArea textarea, .stNumberInput input{ background:#fff !important; color:var(--ui-txt) !important; }
div[data-baseweb="select"] > div{ background:#fff !important; }
.qf-tag{ background:#F1F3FB; } .qf-tag.lv{ color:#0A7C93; border-color:rgba(10,124,147,.45); }
.qf-qnum{ color:#5B3FE0; }
.qf-qcard, .qf-flash{ background:linear-gradient(145deg,rgba(124,107,255,.09),transparent 55%),#fff; }
.qf-tile .v{ color:var(--ui-txt); }
section[data-testid="stSidebar"]{ background:linear-gradient(180deg,#FFFFFF,#F3F4FB) !important; }
.st-key-lang_sw_top div[role="radiogroup"]{ background:#fff !important; }
.qf-act:hover{ background:rgba(22,28,72,.035); }
section[data-testid="stSidebar"] [data-testid="stExpander"]{ background:#F7F8FD; }
.stTabs [data-baseweb="tab-list"]{ background:rgba(255,255,255,.88); }
</style>
"""


st.markdown(BASE_CSS, unsafe_allow_html=True)
if LIGHT:
    st.markdown(LIGHT_CSS, unsafe_allow_html=True)
st.markdown(i18n.LANG_CSS, unsafe_allow_html=True)  # language switcher + Devanagari styling
st.markdown(UI_CSS, unsafe_allow_html=True)  # modern UI layer (overrides the rules above)
if LIGHT:
    st.markdown(UI_LIGHT_CSS, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# API KEY / CLIENT
# ─────────────────────────────────────────────────────────────
try:
    api_key = st.secrets.get("GROQ_API_KEY")
except Exception:
    api_key = None
api_key = api_key or os.getenv("GROQ_API_KEY")

if not api_key:
    st.error(tr("err.no_api_key"))
    st.stop()


@st.cache_resource
def get_client(key: str):
    return Groq(api_key=key)


client = get_client(api_key)


def _secret(name):
    try:
        v = st.secrets.get(name)
    except Exception:
        v = None
    return v or os.getenv(name)


SB_URL, SB_KEY = _secret("SUPABASE_URL"), _secret("SUPABASE_ANON_KEY")
AUTH_CONFIGURED = bool(SB_URL and SB_KEY)
AUTH_ENABLED = AUTH_CONFIGURED and create_client is not None

MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
MAX_CHARS = 24000
MAX_IMG_BYTES = 3 * 1024 * 1024  # size sent to the AI (after compression)
MAX_RAW_IMG_BYTES = 15 * 1024 * 1024  # biggest photo we accept from the user
MAX_TOTAL_Q = 200  # cap for one quiz, including 'add more questions' extensions
XP_BASE = {1: 10, 2: 15, 3: 20}
LEVEL_NAME = {1: "Easy", 2: "Medium", 3: "Hard"}
DIFF_LEVEL = {"Easy": 1, "Medium": 2, "Hard": 3}
LIVES = 3

TYPE_MAP = {
    "Multiple Choice": "mcq",
    "True / False": "tf",
    "Multi-select": "multi",
    "Fill in the blank": "blank",
    "Short answer (AI check)": "short",
    "Numerical value": "num",
}
TYPE_ALIASES = {
    "mcq": "mcq", "multiple choice": "mcq", "multiple_choice": "mcq",
    "tf": "tf", "true/false": "tf", "true_false": "tf", "true / false": "tf", "truefalse": "tf",
    "multi": "multi", "multi-select": "multi", "multiselect": "multi", "multi_select": "multi",
    "blank": "blank", "fill": "blank", "fill in the blank": "blank", "fill_in_the_blank": "blank",
    "short": "short", "short answer": "short", "short_answer": "short",
    "num": "num", "numerical": "num", "numeric": "num", "numerical value": "num", "integer": "num", "nvq": "num",
}
TYPE_SPECS = {
    "mcq": '{"type":"mcq","question":"...","options":["A","B","C","D"],"answer":"<exact text of the correct option>"}',
    "tf": '{"type":"tf","question":"<a statement>","options":["True","False"],"answer":"True"}',
    "multi": '{"type":"multi","question":"... (select all that apply)","options":["..","..","..","..",".."],"answers":["<exact option>","<exact option>"]}',
    "blank": '{"type":"blank","question":"A sentence with ____ in place of the missing word","answer":"missing word or phrase","accept":["acceptable alternative"]}',
    "short": '{"type":"short","question":"open question answerable in 1-3 sentences","answer":"model answer in 1-2 sentences"}',
    "num": '{"type":"num","question":"a problem whose final answer is a single number","answer":"<number only, no units>"}',
}

# ─────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────
def fresh_run_state():
    return {
        "quiz": [], "idx": 0, "answers": {}, "locked": {}, "hints_used": {}, "times": {}, "timed_out": {},
        "grades": {}, "cur_level": 2, "quiz_time_up": False, "elapsed_before": 0.0, "result": None, "study_plan": "", "celebrated": False,
        "start_time": None, "end_time": None,
    }


GLOBAL_DEFAULTS = {
    "stage": "setup", "quiz_id": 0, "history": [], "meta": {}, "total_xp": 0, "bookmarks": {}, "deep": {},
    "flash_cards": [], "flash_i": 0, "flash_show": False, "flash_return": "setup",
    "q_key": None, "q_start": time.time(), "_picked": "",
    "pyq_uploaded": [], "doubt_thread": [], "doubt_pending": False, "doubt_opts": {},
    "user": None, "sb": None, "tokens": {}, "is_admin": False, "seen_local": {}, "bank_cache": {}, "otp": {},
}
for _k, _v in {**GLOBAL_DEFAULTS, **fresh_run_state()}.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────────────────────
# GENERAL HELPERS
# ─────────────────────────────────────────────────────────────
def esc(s) -> str:
    return html.escape(str(s))


def fmt_time(seconds):
    seconds = int(seconds)
    return tr("time.fmt", m=seconds // 60, s=seconds % 60)


def level_of(xp):
    return xp // 100 + 1


def explanation_text(q) -> str:
    """Explanation shown to the user. Empty explanations get a placeholder in the CURRENT language."""
    return str(q.get("explanation") or "").strip() or tr("fb.no_expl")


def grade_feedback(g) -> str:
    """AI feedback for a short answer; built-in fallback messages follow the current language."""
    return tr(g["fb_key"]) if g.get("fb_key") else str(g.get("feedback", ""))


def deep_key(q) -> str:
    """Cache key for 'explain in more detail' — one entry per language, so switching language re-explains."""
    return f"{i18n.cur()}::{q['question']}"


def disp(q, v):
    """True/False options keep English values internally; show them translated."""
    return i18n.fmt("tf")(v) if q.get("type") == "tf" else v


def topic_label(s) -> str:
    """History/report labels are stored in English; show them in the current language."""
    s = str(s)
    if s == "Pasted notes":
        return tr("lbl.pasted")
    for pre, key in (("Retry · ", "lbl.retry"), ("PDF: ", "lbl.pdf"), ("Photo: ", "lbl.photo"), ("Doubt: ", "lbl.doubt")):
        if s.startswith(pre):
            inner = s[len(pre):]
            return tr(key, n=topic_label(inner) if key == "lbl.retry" else inner)
    for suf, key in ((" · Mock", "lbl.mock"), (" · PYQ", "lbl.pyq")):
        if s.endswith(suf):
            return tr(key, n=s[: -len(suf)])
    return s


def friendly_error(e: Exception) -> str:
    msg = str(e)
    low = msg.lower()
    if ("rate" in low and "limit" in low) or "429" in low:
        return tr("err.rate")
    if "api key" in low or "401" in low or "invalid_api_key" in low:
        return tr("err.apikey")
    if "model" in low and ("not found" in low or "decommissioned" in low or "does not exist" in low):
        return tr("err.model")
    return tr("err.generic", msg=msg)


def llm(messages, model, json_mode=False, temperature=0.6):
    kwargs = dict(model=model, messages=messages, temperature=temperature)
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    if model.startswith("openai/gpt-oss"):
        kwargs["extra_body"] = {"reasoning_effort": "low"}
    r = client.chat.completions.create(**kwargs)
    return r.choices[0].message.content or ""


def llm_stream(messages, model, temperature=0.5):
    """Yield text chunks so answers appear word by word (used by the Doubt Solver)."""
    kwargs = dict(model=model, messages=messages, temperature=temperature, stream=True)
    if model.startswith("openai/gpt-oss"):
        kwargs["extra_body"] = {"reasoning_effort": "low"}
    for chunk in client.chat.completions.create(**kwargs):
        try:
            piece = chunk.choices[0].delta.content
        except Exception:
            piece = None
        if piece:
            yield piece


def clean_json(raw: str):
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.lower().startswith("json"):
            raw = raw[4:]
    data = json.loads(raw.strip())
    if isinstance(data, dict):
        if isinstance(data.get("questions"), list):
            return data["questions"]
        for v in data.values():
            if isinstance(v, list):
                return v
    return data


# ─────────────────────────────────────────────────────────────
# QUESTION MODEL: validation, answers, scoring
# ─────────────────────────────────────────────────────────────
def to_number(s):
    """Parse '12', '-3.5', '1,200', '4.2e3', '12 m/s' -> float (or None)."""
    if s is None:
        return None
    t = str(s).strip().replace(",", "").replace("−", "-")
    pat = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?"
    m = re.fullmatch(pat, t) or re.search(pat, t)
    try:
        return float(m.group()) if m else None
    except Exception:
        return None


def fmt_num(v):
    return str(int(round(v))) if abs(v - round(v)) < 1e-9 else f"{v:.6g}"


def prepare_image(data, mime="image/jpeg", max_side=1600):
    """Fix phone-photo rotation, shrink big photos and re-encode as JPEG so they fit the AI size limit."""
    try:
        from PIL import Image, ImageOps

        img = ImageOps.exif_transpose(Image.open(io.BytesIO(data)))
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            img = img.convert("RGBA")
            bg = Image.new("RGB", img.size, "white")
            bg.paste(img, mask=img.split()[-1])
            img = bg
        elif img.mode != "RGB":
            img = img.convert("RGB")
        img.thumbnail((max_side, max_side))
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85, optimize=True)
        return buf.getvalue(), "image/jpeg"
    except Exception:
        return data, mime


def norm_text(s) -> str:
    s = re.sub(r"[^\w\s]", "", str(s).casefold())
    return " ".join(s.split())


def blank_match(answer, q) -> bool:
    na = norm_text(answer)
    if not na:
        return False
    for cand in [q.get("answer", "")] + list(q.get("accept", [])):
        nc = norm_text(cand)
        if nc and (na == nc or difflib.SequenceMatcher(None, na, nc).ratio() >= 0.86):
            return True
    return False


def resolve_option(val, options):
    val = str(val).strip()
    if val in options:
        return val
    letters = "ABCDEFGH"
    if len(val) == 1 and val.upper() in letters[: len(options)]:
        return options[letters.index(val.upper())]
    m = [o for o in options if o.lower() == val.lower()]
    return m[0] if m else None


def validate_and_shuffle(items, default_level=2, adaptive=False):
    good = []
    if not isinstance(items, list):
        return good
    for q in items:
        try:
            if not isinstance(q, dict):
                continue
            t = TYPE_ALIASES.get(str(q.get("type", "mcq")).lower().strip(), "mcq")
            question = str(q["question"]).strip()
            if not question:
                continue
            item = {
                "type": t,
                "question": question,
                "options": [],
                "answer": "",
                "answers": [],
                "accept": [],
                "explanation": str(q.get("explanation", "")).strip(),
                "hint": str(q.get("hint", "")).strip(),
                "topic": (str(q.get("topic", "General")).strip()[:30] or "General"),
                "level": default_level,
            }
            if adaptive:
                try:
                    item["level"] = min(3, max(1, int(q.get("level", 2))))
                except Exception:
                    item["level"] = 2

            if t in ("mcq", "tf", "multi"):
                options = [str(o).strip() for o in q["options"]]
                if len(options) < 2:
                    continue
                if t == "multi":
                    raw = q.get("answers") or ([q["answer"]] if "answer" in q else [])
                    if isinstance(raw, str):
                        raw = [raw]
                    ans = [resolve_option(a, options) for a in raw]
                    ans = [a for a in dict.fromkeys(ans) if a]
                    if not ans:
                        continue
                    if len(ans) == 1:
                        t, item["type"], item["answer"] = "mcq", "mcq", ans[0]
                    else:
                        item["answers"] = ans
                else:
                    a = resolve_option(q["answer"], options)
                    if a is None:
                        continue
                    item["answer"] = a
                    if {o.lower() for o in options} == {"true", "false"}:
                        t, item["type"] = "tf", "tf"
                if t != "tf":
                    random.shuffle(options)
                item["options"] = options
            elif t == "num":
                val = to_number(q.get("answer"))
                if val is None:
                    continue
                item["answer"] = fmt_num(val)
                try:
                    tol = float(q.get("tolerance", 0) or 0)
                except Exception:
                    tol = 0.0
                item["tol"] = tol if tol > 0 else (0.0 if abs(val - round(val)) < 1e-9 else 0.011)
            elif t == "blank":
                ans = str(q["answer"]).strip()
                if not ans or "__" not in question:
                    continue
                accept = q.get("accept") or []
                if isinstance(accept, str):
                    accept = [accept]
                item["answer"] = ans
                item["accept"] = [str(a).strip() for a in accept if str(a).strip()]
            else:  # short
                ans = str(q["answer"]).strip()
                if not ans:
                    continue
                item["answer"] = ans
            good.append(item)
        except Exception:
            continue
    return good


def is_skipped(i) -> bool:
    return st.session_state.answers.get(i) in (None, "", [])


def is_correct(i) -> bool:
    ss = st.session_state
    q, a = ss.quiz[i], ss.answers.get(i)
    if a in (None, "", []):
        return False
    t = q["type"]
    if t in ("mcq", "tf"):
        return a == q["answer"]
    if t == "multi":
        return set(a) == set(q["answers"])
    if t == "num":
        ua, ca = to_number(a), to_number(q["answer"])
        return ua is not None and ca is not None and abs(ua - ca) <= q.get("tol", 0.0) + 1e-9
    if t == "blank":
        return blank_match(a, q)
    return ss.grades.get(i, {}).get("score", 0) >= 0.6


def correct_text(q) -> str:
    return " · ".join(q["answers"]) if q["type"] == "multi" else q["answer"]


def user_text(i) -> str:
    a = st.session_state.answers.get(i)
    if a in (None, "", []):
        return "—"
    return " | ".join(a) if isinstance(a, list) else str(a)


def norm_answer(a):
    if isinstance(a, str):
        a = a.strip()
    return None if a in (None, "", []) else a


def has_answer(a) -> bool:
    return norm_answer(a) is not None


def reshuffle(q):
    q = dict(q)
    if q["type"] in ("mcq", "multi"):
        opts = list(q["options"])
        random.shuffle(opts)
        q["options"] = opts
    return q


def speech_text(q) -> str:
    """Text read aloud by the browser. Follows the language the QUIZ is written in."""
    ss = st.session_state
    lang = (ss.meta.get("language") if ss.get("stage") == "quiz" else None) or ss.get("language", "English")
    w = i18n.SPEECH.get(lang, i18n.SPEECH["English"])
    t = q["question"].replace("____", w["blank"]).replace("___", w["blank"])
    if q["type"] in ("mcq", "multi"):
        t += ". " + " ".join(f"{w['option']} {n + 1}. {o}." for n, o in enumerate(q["options"]))
    elif q["type"] == "tf":
        t += ". " + w["tf"]
    return t


# ─────────────────────────────────────────────────────────────
# AI CALLS
# ─────────────────────────────────────────────────────────────
def generate_quiz(text, num_q, diff, type_keys, lang, model, media=None, avoid=None, adaptive=False, exam=None):
    type_keys = [t for t in type_keys if t in TYPE_SPECS] or ["mcq"]
    shapes = "\n".join(f"- {t}: {TYPE_SPECS[t]}" for t in type_keys)
    level_rule = (
        '- Give each question a numeric "level": 1 (easy), 2 (medium) or 3 (hard), roughly a third each.'
        if adaptive
        else f'- Every question has "level": {DIFF_LEVEL[diff]}. Overall difficulty: {diff}.'
    )
    avoid_rule = ""
    if avoid:
        avoid_rule = "- Do NOT repeat or rephrase these earlier questions:\n  " + "\n  ".join(f"* {a}" for a in avoid[-40:])
    exam_rule = (
        f"- Write in the style, difficulty and syllabus of {exam} previous-year papers. "
        "Do NOT claim any question is from a real past paper and do NOT invent exam years."
        if exam
        else ""
    )
    content_block = (
        "Use the attached image as the content. Read it carefully, including handwriting if present."
        if media
        else f'Content:\n"""\n{text[:MAX_CHARS]}\n"""'
    )

    prompt = f"""You are an expert teacher and quiz designer.
Create exactly {num_q} quiz questions from the content below.

Allowed question types and their JSON shapes (spread the questions roughly evenly across them):
{shapes}

Every question object must ALSO contain: "explanation", "hint", "topic".

Rules:
{level_rule}
- Write questions, options, hints and explanations in: {lang}.
- Exactly one correct option for mcq/tf; multi needs 2-3 correct options out of 5.
- Distractors must be plausible. Avoid "All of the above".
- Cover different parts of the content; no duplicate questions.
- "hint": a short nudge WITHOUT revealing the answer.
- "explanation": 1-2 short sentences why the answer is correct.
- "topic": a 1-3 word sub-topic label.
{avoid_rule}
{exam_rule}
- Prefer fresh sub-topics and angles every time (variation seed {random.randint(1000, 9999)}).

Return ONLY a JSON object: {{"questions": [ ...question objects... ]}}

{content_block}
"""
    system = {"role": "system", "content": "You are a JSON generator. Respond only with valid JSON."}
    if media:
        b64 = base64.b64encode(media["bytes"]).decode()
        user = {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{media['mime']};base64,{b64}"}},
            ],
        }
        model = VISION_MODEL
    else:
        user = {"role": "user", "content": prompt}

    last_err = None
    for attempt in range(2):
        try:
            raw = llm([system, user], model, json_mode=True, temperature=0.6 + 0.2 * attempt)
            quiz = validate_and_shuffle(clean_json(raw), DIFF_LEVEL[diff], adaptive)
            if quiz:
                return quiz
        except json.JSONDecodeError as e:
            last_err = e
    if last_err:
        raise last_err
    return []


def generate_quiz_batched(text, num_q, diff, type_keys, lang, model, media=None, avoid=None, adaptive=False, progress=None, exam=None):
    """Generate in batches of 10; drops anything already seen (exact or near-identical) so repeats never reach the user."""
    quiz = []
    avoid_list = list(avoid or [])
    seen_h = {qhash(a) for a in avoid_list}
    seen_n = [norm_text(a) for a in avoid_list]
    attempts, max_attempts = 0, num_q // 5 + 5
    while len(quiz) < num_q and attempts < max_attempts:
        attempts += 1
        n = min(10, num_q - len(quiz))
        try:
            batch = generate_quiz(text, n, diff, type_keys, lang, model, media=media, avoid=avoid_list, adaptive=adaptive, exam=exam)
        except Exception:
            if quiz:
                break  # keep what we already have
            raise
        for b in batch:
            if not is_duplicate(b["question"], seen_h, seen_n):
                seen_h.add(qhash(b["question"]))
                seen_n.append(norm_text(b["question"]))
                quiz.append(b)
        avoid_list += [b["question"] for b in batch]
        if progress:
            progress(min(len(quiz) / num_q, 1.0), tr("gen.progress", done=min(len(quiz), num_q), total=num_q))
    return quiz[:num_q]


def generate_with_progress(text, num_q, diff, type_keys, lang, model, media=None, avoid=None, adaptive=False, exam=None):
    bar = st.progress(0.0, text=tr("gen.making"))

    def cb(frac, msg):
        bar.progress(min(max(frac, 0.0), 1.0), text=msg)

    try:
        return generate_quiz_batched(text, num_q, diff, type_keys, lang, model, media, avoid, adaptive, progress=cb, exam=exam)
    finally:
        bar.empty()


def grade_short(i):
    ss = st.session_state
    if i in ss.grades:
        return ss.grades[i]
    q, a = ss.quiz[i], (ss.answers.get(i) or "")
    lang = i18n.ai_lang()  # AI feedback follows the app language
    if not str(a).strip():
        g = {"score": 0.0, "feedback": "", "fb_key": "grade.none"}
    else:
        prompt = f"""Grade a student's short answer. Language for feedback: {lang}.
Question: {q['question']}
Model answer: {q['answer']}
Student answer: {a}

Be fair: accept correct ideas worded differently. Return ONLY JSON:
{{"score": <number 0 to 1>, "feedback": "<one or two sentences: what was good, what was missing>"}}"""
        try:
            raw = llm([{"role": "user", "content": prompt}], ss.meta.get("model", MODELS[0]), json_mode=True, temperature=0.2)
            d = json.loads(raw)
            g = {"score": min(1.0, max(0.0, float(d.get("score", 0)))), "feedback": str(d.get("feedback", "")).strip()}
        except Exception:
            g = {"score": 0.0, "feedback": "", "fb_key": "grade.fail"}
    ss.grades[i] = g
    return g


def explain_more(q, user_ans, lang, model):
    key = deep_key(q)
    if key in st.session_state.deep:
        return st.session_state.deep[key]
    prompt = f"""Explain this quiz question in more depth for a student. Language: {lang}.
Question: {q['question']}
Options: {q['options'] or 'n/a'}
Correct answer: {correct_text(q)}
Student's answer: {user_ans or 'skipped'}
Give: (1) why the correct answer is right, (2) why the student's choice (if wrong) is tempting but wrong,
(3) one simple real-life example or memory trick. Under 150 words, short bullet points."""
    text = llm([{"role": "user", "content": prompt}], model)
    st.session_state.deep[key] = text
    return text


def make_study_plan(wrong_qs, lang, model):
    items = "\n".join(f"- [{q['topic']}] {q['question']} (correct: {correct_text(q)})" for q in wrong_qs)
    prompt = f"""A student got these quiz questions wrong or skipped them. Language: {lang}.
{items}

Write a compact revision plan in markdown:
1. **Weak areas** - 2-4 bullets naming concepts to revise.
2. **Quick notes** - key facts to remember, short bullets.
3. **Next steps** - 3 concrete practice tips.
Under 220 words."""
    return llm([{"role": "user", "content": prompt}], model)


# ─────────────────────────────────────────────────────────────
# ACCOUNT (email / phone OTP), DATABASE AND "ALREADY SEEN" MEMORY
# ─────────────────────────────────────────────────────────────
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def qhash(text) -> str:
    return hashlib.sha1(norm_text(text).encode("utf-8")).hexdigest()[:16]


def topic_key_for(kind, label) -> str:
    return f"{kind}::{norm_text(label)[:80]}"


def is_duplicate(question, seen_hashes, seen_norms):
    """Exact repeat or a near-identical rewording of something already seen."""
    if qhash(question) in seen_hashes:
        return True
    n = norm_text(question)
    return any(difflib.SequenceMatcher(None, n, x).ratio() >= 0.88 for x in seen_norms[-120:])


def db_on() -> bool:
    ss = st.session_state
    return bool(AUTH_ENABLED and ss.get("user") and ss.get("sb"))


def db_uid():
    return st.session_state["user"]["id"]


def db_try(fn, default=None):
    """Run a DB call; never crash the quiz because of a database hiccup."""
    try:
        return fn()
    except Exception as e:
        st.session_state["_db_err"] = str(e)[:200]
        return default


def fetch_all(make_query, page=1000, cap=20000):
    rows = []
    for start in range(0, cap, page):
        data = make_query().range(start, start + page - 1).execute().data or []
        rows += data
        if len(data) < page:
            break
    return rows


def _local_time(iso):
    try:
        from zoneinfo import ZoneInfo

        return datetime.fromisoformat(str(iso).replace("Z", "+00:00")).astimezone(ZoneInfo("Asia/Kolkata")).strftime("%d %b, %H:%M")
    except Exception:
        return str(iso)[:16].replace("T", " ")


def db_load_user_data():
    ss = st.session_state
    sb, uid = ss["sb"], db_uid()
    prof = db_try(lambda: sb.table("profiles").select("xp").eq("user_id", uid).execute().data, [])
    if prof:
        ss.total_xp = int(prof[0].get("xp") or 0)
    else:
        ss.total_xp = 0
        db_try(lambda: sb.table("profiles").upsert({"user_id": uid, "xp": 0}).execute())
    rows = db_try(lambda: sb.table("quiz_history").select("*").eq("user_id", uid).order("created_at", desc=True).limit(200).execute().data, []) or []
    hist = []
    for r in reversed(rows):
        try:
            hist.append(
                {
                    "id": r["id"], "time": _local_time(r.get("created_at", "")), "topic": r.get("topic") or "Quiz",
                    "difficulty": r.get("difficulty") or "-", "score": int(r.get("score") or 0), "total": max(1, int(r.get("total") or 1)),
                    "marks": float(r.get("marks") or 0), "max": float(r.get("max_marks") or 0),
                    "acc": int(r.get("accuracy") or 0), "pct": int(r.get("pct") or 0),
                }
            )
        except Exception:
            continue
    ss.history = hist
    bms = db_try(lambda: sb.table("bookmarks").select("data").eq("user_id", uid).execute().data, []) or []
    ss.bookmarks = {b["data"]["question"]: b["data"] for b in bms if isinstance(b.get("data"), dict) and b["data"].get("question")}
    ss.is_admin = bool(db_try(lambda: sb.table("admins").select("user_id").eq("user_id", uid).execute().data, []))


def db_save_result(entry):
    if not db_on():
        return None
    ss, uid = st.session_state, db_uid()
    row = {
        "user_id": uid, "topic": entry["topic"], "difficulty": entry["difficulty"], "score": entry["score"], "total": entry["total"],
        "marks": entry["marks"], "max_marks": entry["max"], "accuracy": entry["acc"], "pct": entry["pct"],
    }
    res = db_try(lambda: ss["sb"].table("quiz_history").insert(row).execute().data)
    db_try(lambda: ss["sb"].table("profiles").upsert({"user_id": uid, "xp": ss.total_xp, "updated_at": datetime.now(timezone.utc).isoformat()}).execute())
    return res[0]["id"] if res else None


def db_undo_result(hist_id):
    if not db_on():
        return
    ss, uid = st.session_state, db_uid()
    if hist_id:
        db_try(lambda: ss["sb"].table("quiz_history").delete().eq("id", hist_id).eq("user_id", uid).execute())
    db_try(lambda: ss["sb"].table("profiles").upsert({"user_id": uid, "xp": ss.total_xp, "updated_at": datetime.now(timezone.utc).isoformat()}).execute())


def db_clear_history():
    if db_on():
        ss, uid = st.session_state, db_uid()
        db_try(lambda: ss["sb"].table("quiz_history").delete().eq("user_id", uid).execute())


def db_sync_bookmark(q, added):
    if not db_on():
        return
    ss, uid = st.session_state, db_uid()
    h = qhash(q["question"])
    if added:
        db_try(lambda: ss["sb"].table("bookmarks").upsert({"user_id": uid, "qhash": h, "data": q}, on_conflict="user_id,qhash").execute())
    else:
        db_try(lambda: ss["sb"].table("bookmarks").delete().eq("user_id", uid).eq("qhash", h).execute())


# ── "already seen" memory: same topic again => different questions ──
def get_seen_questions(tkey, limit=80):
    ss = st.session_state
    if not tkey:
        return []
    if db_on():
        uid = db_uid()
        rows = db_try(
            lambda: ss["sb"].table("seen_questions").select("question").eq("user_id", uid).eq("topic_key", tkey)
            .order("created_at", desc=True).limit(limit).execute().data, [],
        ) or []
        return [r["question"] for r in rows if r.get("question")]
    return list(reversed(ss.seen_local.get(tkey, [])))[:limit]


def get_seen_hashes(tkey):
    ss = st.session_state
    if not tkey:
        return set()
    if db_on():
        uid = db_uid()
        rows = db_try(lambda: fetch_all(lambda: ss["sb"].table("seen_questions").select("qhash").eq("user_id", uid).eq("topic_key", tkey)), []) or []
        return {r["qhash"] for r in rows}
    return {qhash(x) for x in ss.seen_local.get(tkey, [])}


def mark_seen(tkey, quiz):
    ss = st.session_state
    if not tkey or not quiz:
        return
    items = {qhash(q["question"]): q["question"] for q in quiz}
    if db_on():
        uid = db_uid()
        rows = [{"user_id": uid, "topic_key": tkey, "qhash": h, "question": t[:400]} for h, t in items.items()]
        db_try(lambda: ss["sb"].table("seen_questions").upsert(rows, on_conflict="user_id,topic_key,qhash", ignore_duplicates=True).execute())
    else:
        lst = ss.seen_local.setdefault(tkey, [])
        have = {qhash(x) for x in lst}
        lst += [t for h, t in items.items() if h not in have]
        del lst[:-500]


def reset_seen(tkey):
    ss = st.session_state
    if db_on():
        uid = db_uid()
        db_try(lambda: ss["sb"].table("seen_questions").delete().eq("user_id", uid).eq("topic_key", tkey).execute())
    else:
        ss.seen_local.pop(tkey, None)


# ── shared PYQ bank (admins write, everyone reads) ──
def bank_hash(x):
    return qhash(f"{x['exam']}|{x['question']}")


def db_load_bank(exam):
    ss = st.session_state
    if not db_on():
        return []
    cached = ss.bank_cache.get(exam)
    if cached and time.time() - cached[0] < 600:
        return cached[1]
    rows = db_try(lambda: fetch_all(lambda: ss["sb"].table("pyq_bank").select("*").eq("exam", exam)), []) or []
    items = normalize_pyq(
        [
            {
                "exam": r.get("exam"), "subject": r.get("subject") or "General", "year": r.get("year") or "", "type": r.get("qtype") or "mcq",
                "question": r.get("question"), "options": r.get("options") or [], "answer": r.get("answer"),
                "explanation": r.get("explanation") or "", "tolerance": r.get("tolerance") or 0,
            }
            for r in rows
        ]
    )
    ss.bank_cache[exam] = (time.time(), items)
    return items


def db_save_bank(items):
    ss = st.session_state
    rows = [
        {
            "qhash": bank_hash(x), "exam": x["exam"], "subject": x["subject"], "year": x["year"], "qtype": x.get("type", "mcq"),
            "question": x["question"], "options": x.get("options") or [], "answer": x["answer"],
            "explanation": x.get("explanation") or "", "tolerance": x.get("tol") or 0,
        }
        for x in items
    ]
    for i in range(0, len(rows), 500):
        ss["sb"].table("pyq_bank").upsert(rows[i : i + 500], on_conflict="qhash", ignore_duplicates=True).execute()
    ss.bank_cache = {}
    return len(rows)


# ── login ──
def normalize_phone(s):
    d = re.sub(r"[^\d+]", "", s or "")
    if d.startswith("+"):
        digits = d[1:]
        return "+" + digits if digits.isdigit() and 10 <= len(digits) <= 15 else None
    d = d.lstrip("0")
    if d.startswith("91") and len(d) == 12:
        return "+" + d
    if len(d) == 10 and d.isdigit():
        return "+91" + d
    return None


def mask_ident(ident):
    if "@" in ident:
        name, dom = ident.split("@", 1)
        return name[:1] + "***@" + dom
    return ident[:3] + "*" * max(len(ident) - 7, 2) + ident[-4:]


def auth_friendly(e, channel, verifying=False):
    msg = str(e)
    low = msg.lower()
    if channel == "phone" and any(k in low for k in ("provider", "sms", "twilio", "unsupported phone")):
        return tr("auth.sms")
    if any(k in low for k in ("rate limit", "too many", "after", "seconds")) and not verifying:
        return tr("auth.ratelimit")
    if verifying and any(k in low for k in ("expired", "invalid", "token", "otp")):
        return tr("auth.otp_bad")
    if "signups not allowed" in low or "signup" in low and "disabled" in low:
        return tr("auth.signup_off")
    return tr("err.generic", msg=msg)


def sb_client():
    ss = st.session_state
    if ss.get("sb") is None:
        ss["sb"] = create_client(SB_URL, SB_KEY)  # one client PER session, never shared between users
    return ss["sb"]


def otp_send(channel, ident):
    payload = {"email": ident} if channel == "email" else {"phone": ident}
    payload["options"] = {"should_create_user": True}
    sb_client().auth.sign_in_with_otp(payload)


def otp_verify(channel, ident, code):
    sb = sb_client()
    last = None
    for kind in (("email", "signup", "magiclink") if channel == "email" else ("sms",)):
        try:
            payload = {"token": code, "type": kind, ("email" if channel == "email" else "phone"): ident}
            res = sb.auth.verify_otp(payload)
            if res and res.session and res.user:
                return res
        except Exception as e:
            last = e
    raise last or ValueError(tr("auth.otp_bad"))


def remember_login(cm, refresh_token):
    if cm is None or not refresh_token:
        return
    try:
        cm.set("qa_rt", refresh_token, expires_at=datetime.now() + timedelta(days=30), key=f"set_rt_{int(time.time() * 1000)}")
    except Exception:
        pass


def complete_login(session, user, cm):
    ss = st.session_state
    ss["user"] = {"id": str(user.id), "email": getattr(user, "email", "") or "", "phone": getattr(user, "phone", "") or ""}
    ss["tokens"] = {"refresh": session.refresh_token, "access": session.access_token, "exp": float(session.expires_at or (time.time() + 3000))}
    try:
        ss["sb"].postgrest.auth(session.access_token)
    except Exception:
        pass
    ss["_just_logged_out"] = False
    remember_login(cm, session.refresh_token)
    db_load_user_data()


def do_logout(cm=None, rerun=True):
    ss = st.session_state
    try:
        ss["sb"].auth.sign_out({"scope": "local"})
    except Exception:
        pass
    if cm is not None:
        try:
            cm.delete("qa_rt", key=f"del_rt_{int(time.time() * 1000)}")
            time.sleep(0.6)  # give the browser a moment to apply the cookie change
        except Exception:
            pass
    keep = {k: ss[k] for k in ("ui_lang", "ui_lang_explicit", "language", "d_lang") if k in ss}  # language survives logout
    ss.clear()
    ss.update(keep)
    ss["_just_logged_out"] = True
    if rerun:
        st.rerun()


def ensure_fresh_token(cm):
    ss = st.session_state
    tk = ss.get("tokens") or {}
    if time.time() < tk.get("exp", 0) - 90:
        return
    try:
        res = ss["sb"].auth.refresh_session(tk["refresh"])
        sess = res.session
        ss["tokens"] = {"refresh": sess.refresh_token, "access": sess.access_token, "exp": float(sess.expires_at or (time.time() + 3000))}
        try:
            ss["sb"].postgrest.auth(sess.access_token)
        except Exception:
            pass
        remember_login(cm, sess.refresh_token)
    except Exception:
        do_logout(cm, rerun=False)  # session expired -> show the login screen


def try_cookie_login(cm):
    ss = st.session_state
    if cm is None or ss.get("_just_logged_out") or ss.get("_cookie_tried"):
        return
    rt = cm.get("qa_rt")
    if not rt:
        return
    ss["_cookie_tried"] = True
    try:
        res = sb_client().auth.refresh_session(rt)
        complete_login(res.session, res.user, cm)
    except Exception:
        try:
            cm.delete("qa_rt", key="del_bad_rt")
        except Exception:
            pass


def render_login(cm):
    """Draws the login screen. Returns True the moment the user is logged in."""
    ss = st.session_state

    # language switcher is available on the login screen too (the sidebar isn't shown here)
    with st.container(key="langbar"):
        i18n.render_switcher("login")
    components.html(i18n.bridge_js(), height=0)

    st.markdown(
        f"""<div class="qf-hero plain"><span class="qf-blob b1"></span><span class="qf-blob b2"></span><div class="qf-title qf-display">{APP_NAME}</div>
<div class="qf-sub">{esc(tr('login.sub'))}</div></div>""",
        unsafe_allow_html=True,
    )
    otp = ss.get("otp") or {}
    with st.container(key="panel_login"):
        if not otp:
            ch = st.radio(tr("login.how"), ["email", "phone"], format_func=lambda v: tr(f"login.{v}"), horizontal=True, key="login_ch")
            is_email = ch == "email"
            raw = st.text_input(
                tr("login.email_label") if is_email else tr("login.phone_label"),
                key="login_id_email" if is_email else "login_id_phone",
                placeholder="you@example.com" if is_email else tr("login.phone_ph"),
            )
            if not is_email:
                st.caption(tr("login.phone_hint"))
            if st.button(tr("login.send"), type="primary", use_container_width=True, key="otp_send_btn"):
                ident = (raw or "").strip().lower() if is_email else normalize_phone(raw)
                if (is_email and not EMAIL_RE.match(ident or "")) or (not is_email and not ident):
                    st.error(tr("login.bad_email") if is_email else tr("login.bad_phone"))
                else:
                    channel = "email" if is_email else "phone"
                    with st.spinner(tr("login.sending")):
                        try:
                            otp_send(channel, ident)
                            ss["otp"] = {"channel": channel, "ident": ident, "sent": time.time()}
                            st.rerun()
                        except Exception as e:
                            st.error(auth_friendly(e, channel))
            return False

        st.success(tr("login.sent", to=mask_ident(otp["ident"])))
        code = st.text_input(tr("login.enter_otp"), max_chars=10, key="otp_code", placeholder="123456")
        c1, c2 = st.columns(2)
        if c1.button(tr("login.verify"), type="primary", use_container_width=True, key="otp_verify_btn"):
            token = re.sub(r"\s", "", code or "")
            if not token:
                st.warning(tr("login.need_otp"))
            else:
                with st.spinner(tr("login.verifying")):
                    try:
                        res = otp_verify(otp["channel"], otp["ident"], token)
                        complete_login(res.session, res.user, cm)
                        ss["otp"] = {}
                        return True
                    except Exception as e:
                        st.error(auth_friendly(e, otp["channel"], verifying=True))
        if c2.button(tr("login.resend"), use_container_width=True, key="otp_resend_btn"):
            wait = 60 - (time.time() - otp.get("sent", 0))
            if wait > 0:
                st.warning(tr("login.wait", n=int(wait) + 1))
            else:
                try:
                    otp_send(otp["channel"], otp["ident"])
                    ss["otp"]["sent"] = time.time()
                    st.success(tr("login.resent"))
                except Exception as e:
                    st.error(auth_friendly(e, otp["channel"]))
        if st.button(tr("login.back"), key="otp_back"):
            ss["otp"] = {}
            st.rerun()
    return False


def ensure_auth():
    """Login gate. Returns the cookie manager (or None). Stops the script until the user is logged in."""
    ss = st.session_state
    if not AUTH_CONFIGURED:
        return None
    if create_client is None:
        st.error(tr("err.no_supabase"))
        st.stop()
    cm = None
    if stx is not None:
        try:
            cm = stx.CookieManager(key="qa_cm")
        except Exception:
            cm = None
    if ss.get("user"):
        ensure_fresh_token(cm)
        if ss.get("user"):
            return cm
    try_cookie_login(cm)
    if ss.get("user"):
        return cm
    box = st.empty()
    with box.container():
        logged_in = render_login(cm)
    if not logged_in:
        st.stop()
    box.empty()
    return cm


# ─────────────────────────────────────────────────────────────
# QUIZ FLOW
# ─────────────────────────────────────────────────────────────
def start_quiz(quiz, meta):
    st.session_state.update(fresh_run_state())
    st.session_state.update(
        quiz=quiz, quiz_id=st.session_state.quiz_id + 1, start_time=time.time(), stage="quiz", meta=meta, q_key=None
    )
    mark_seen(meta.get("tkey"), quiz)


def record_time(i):
    if i not in st.session_state.times:
        st.session_state.times[i] = time.time() - st.session_state.q_start


def queue_sound(name):
    st.session_state["sound"] = name


def lives_left():
    ss = st.session_state
    lost = sum(1 for j in ss.locked if not is_correct(j))
    return max(LIVES - lost, 0)


def advance(i):
    """Move to the next question; in adaptive mode pick the next one by current level."""
    ss = st.session_state
    q = ss.quiz[i]
    if ss.meta.get("adaptive"):
        if q["type"] != "short" or i in ss.grades:
            if is_correct(i):
                ss.cur_level = min(3, ss.cur_level + 1)
            elif not is_skipped(i):
                ss.cur_level = max(1, ss.cur_level - 1)
        rest = list(range(i + 1, len(ss.quiz)))
        if rest:
            best = min(rest, key=lambda j: (abs(ss.quiz[j]["level"] - ss.cur_level), random.random()))
            ss.quiz[i + 1], ss.quiz[best] = ss.quiz[best], ss.quiz[i + 1]
    ss.idx += 1


def fmt_marks(x):
    return f"{round(float(x), 2):g}"


def question_marks(i):
    """+marks for correct, -penalty for a wrong attempt, 0 for skip. Short answers get partial credit."""
    ss = st.session_state
    q = ss.quiz[i]
    m = ss.meta.get("marks", 1.0)
    pen = 0.0 if q["type"] in ss.meta.get("no_neg_types", []) else m * ss.meta.get("neg", 0.0)
    if is_skipped(i):
        return 0.0
    if q["type"] == "short":
        return round(m * ss.grades.get(i, {}).get("score", 0.0), 2)
    return m if is_correct(i) else (-pen if pen else 0.0)


def compute_badges(pct, best_streak, avg_time, hints, diff, survival_win, n_types, perfect):
    badges = []
    if perfect:
        badges.append("perfect")
    if best_streak >= 5:
        badges.append("streak")
    if avg_time and avg_time < 8 and pct >= 70:
        badges.append("speed")
    if hints == 0 and pct >= 80:
        badges.append("nohints")
    if diff == "Hard" and pct >= 80:
        badges.append("hard")
    if survival_win:
        badges.append("survivor")
    if n_types >= 3 and pct >= 70:
        badges.append("allround")
    if len(st.session_state.history) >= 3:
        badges.append("regular")
    return badges


def finish_quiz():
    ss = st.session_state
    ss.end_time = time.time()
    quiz = ss.quiz
    diff = ss.meta.get("difficulty", "Medium")

    pending = [i for i, q in enumerate(quiz) if q["type"] == "short" and not is_skipped(i) and i not in ss.grades]
    if pending:
        with st.spinner(tr("qz.checking_short")):
            for i in pending:
                grade_short(i)

    xp = streak = best = correct = 0
    for i, q in enumerate(quiz):
        if is_correct(i):
            correct += 1
            streak += 1
            best = max(best, streak)
            pts = XP_BASE.get(q.get("level", 2), 15)
            if ss.hints_used.get(i):
                pts = max(pts - 5, 5)
            if streak >= 3:
                pts += min(streak - 2, 5) * 2
            xp += pts
        else:
            streak = 0

    total = len(quiz)
    per_q = [question_marks(i) for i in range(total)]
    marks = round(sum(per_q), 2)
    max_marks = round(total * ss.meta.get("marks", 1.0), 2)
    neg_lost = round(-sum(x for x in per_q if x < 0), 2)
    attempted = sum(1 for i in range(total) if not is_skipped(i))
    accuracy = round(correct / attempted * 100) if attempted else 0
    pct = max(0, round(marks / max_marks * 100)) if max_marks else 0
    avg_time = sum(ss.times.values()) / len(ss.times) if ss.times else 0
    hints = sum(1 for v in ss.hints_used.values() if v)
    survival_win = ss.meta.get("mode") == "Survival" and len(ss.locked) == total and lives_left() > 0
    n_types = len({q["type"] for q in quiz})

    old_level = level_of(ss.total_xp)
    ss.total_xp += xp
    entry = {
        "time": datetime.now().strftime("%d %b, %H:%M"), "topic": ss.meta.get("label", "Quiz"), "difficulty": diff,
        "score": correct, "total": total, "marks": marks, "max": max_marks, "acc": accuracy, "pct": pct,
    }
    entry["id"] = db_save_result(entry)
    ss.history.append(entry)
    ss.result = {
        "score": correct, "total": total, "pct": pct, "xp": xp, "best_streak": best, "avg_time": avg_time, "hints": hints,
        "marks": marks, "max_marks": max_marks, "neg_lost": neg_lost, "attempted": attempted, "accuracy": accuracy,
        "time_up": ss.quiz_time_up,
        "leveled_up": level_of(ss.total_xp) > old_level,
        "badges": compute_badges(pct, best, avg_time, hints, diff, survival_win, n_types, correct == total),
    }
    queue_sound("win" if pct >= 50 else "lose")
    ss.stage = "result"


# ─────────────────────────────────────────────────────────────
# PYQ DATABASE, MORE-QUESTIONS, PROGRESS BACKUP
# ─────────────────────────────────────────────────────────────
PYQ_FILE = "pyq_data.json"
EXAM_CONFIG = {
    "SSC CGL": {
        "marks": 2.0, "neg": 0.25, "minutes": 60,
        "sections": [("Reasoning", {"mcq": 25}), ("General Awareness", {"mcq": 25}), ("Quantitative Aptitude", {"mcq": 25}), ("English Comprehension", {"mcq": 25})],
    },
    "RRB NTPC": {
        "marks": 1.0, "neg": 1 / 3, "minutes": 90,
        "sections": [("Mathematics", {"mcq": 30}), ("Reasoning", {"mcq": 30}), ("General Awareness", {"mcq": 40})],
    },
    "Banking (IBPS/SBI)": {
        "marks": 1.0, "neg": 0.25, "minutes": 60,
        "sections": [("English", {"mcq": 30}), ("Quantitative Aptitude", {"mcq": 35}), ("Reasoning", {"mcq": 35})],
    },
    "UP Police Constable": {
        "marks": 2.0, "neg": 0.25, "minutes": 120,
        "sections": [("General Knowledge", {"mcq": 38}), ("General Hindi", {"mcq": 37}), ("Numerical Ability", {"mcq": 38}), ("Reasoning", {"mcq": 37})],
    },
    "UPSC / State PCS": {
        "marks": 2.0, "neg": 1 / 3, "minutes": 120,
        "sections": [("History", {"mcq": 17}), ("Polity", {"mcq": 16}), ("Economy", {"mcq": 16}), ("Geography", {"mcq": 15}), ("Environment", {"mcq": 14}), ("Science & Tech", {"mcq": 11}), ("Current Affairs", {"mcq": 11})],
    },
    "UP CNET (Nursing)": {
        "marks": 1.0, "neg": 0.0, "minutes": 140,
        "sections": [("Physics", {"mcq": 24}), ("Chemistry", {"mcq": 24}), ("Biology", {"mcq": 24}), ("English", {"mcq": 24}), ("Nursing Aptitude", {"mcq": 24})],
    },
    "NEET UG": {
        "marks": 4.0, "neg": 0.25, "minutes": 180,
        "sections": [("Physics", {"mcq": 45}), ("Chemistry", {"mcq": 45}), ("Botany", {"mcq": 45}), ("Zoology", {"mcq": 45})],
    },
    "JEE Main": {
        "marks": 4.0, "neg": 0.25, "minutes": 180,
        "sections": [("Physics", {"mcq": 20, "num": 5}), ("Chemistry", {"mcq": 20, "num": 5}), ("Mathematics", {"mcq": 20, "num": 5})],
    },
}
EXAM_LIST = list(EXAM_CONFIG) + ["General All Exams"]
EXAM_SUBJECTS = {k: [name for name, _ in v["sections"]] for k, v in EXAM_CONFIG.items()}
EXAM_SUBJECTS["General All Exams"] = ["Mixed"]
NEG_CHOICES = {"Official": None, "None": 0.0, "¼": 0.25, "⅓": 1 / 3, "½": 0.5, "Full": 1.0}  # labels via i18n "negc.*"
# sidebar negative-marking choices (value = fraction of the marks lost on a wrong answer)
NEG_FRAC = {"none": 0.0, "q": 0.25, "t": 1 / 3, "h": 0.5, "f": 1.0}
_NEG_FIXED = {"q": "¼ (−0.25)", "t": "⅓ (−0.33)", "h": "½ (−0.5)"}


def _neg_label(k):
    return tr("neg.none") if k == "none" else (tr("neg.full") if k == "f" else _NEG_FIXED[k])
PYQ_TEMPLATE = json.dumps(
    [
        {"exam": "SSC CGL", "subject": "General Awareness", "year": "2022", "question": "SAMPLE (replace me): Which planet is known as the Red Planet?",
         "options": ["Venus", "Mars", "Jupiter", "Saturn"], "answer": "Mars", "explanation": "Mars looks red due to iron oxide."},
        {"exam": "SSC CGL", "subject": "Quantitative Aptitude", "year": "2021", "question": "SAMPLE (replace me): 15% of 200 = ?",
         "options": ["20", "25", "30", "35"], "answer": "C", "explanation": "0.15 x 200 = 30. 'answer' can be the option text or its letter A-D."},
        {"exam": "JEE Main", "subject": "Physics", "year": "2023", "type": "num", "question": "SAMPLE (replace me): A body of mass 2 kg moves at 3 m/s. Its kinetic energy (in J) is?",
         "answer": "9", "explanation": "KE = 1/2 x 2 x 9 = 9 J. For numerical questions use type 'num' and a number as answer."},
    ],
    ensure_ascii=False,
    indent=2,
)


def normalize_pyq(items):
    out = []
    if not isinstance(items, list):
        return out
    for it in items:
        try:
            question = str(it["question"]).strip()
            if not question:
                continue
            base = {
                "exam": str(it.get("exam", "General All Exams")).strip() or "General All Exams",
                "subject": str(it.get("subject", "General")).strip() or "General",
                "year": str(it.get("year", "")).strip(),
                "question": question,
                "explanation": str(it.get("explanation", "")).strip(),
            }
            if str(it.get("type", "mcq")).lower().strip() in ("num", "numerical", "nvq", "integer"):
                val = to_number(it.get("answer", it.get("correct", "")))
                if val is None:
                    continue
                try:
                    tol = float(it.get("tolerance", 0) or 0)
                except Exception:
                    tol = 0.0
                out.append({**base, "type": "num", "options": [], "answer": fmt_num(val), "tol": tol if tol > 0 else (0.0 if abs(val - round(val)) < 1e-9 else 0.011)})
            else:
                opts = [str(o).strip() for o in it["options"] if str(o).strip()]
                ans = resolve_option(it.get("answer", it.get("correct", "")), opts)
                if len(opts) < 2 or ans is None:
                    continue
                out.append({**base, "type": "mcq", "options": opts, "answer": ans})
        except Exception:
            continue
    return out


@st.cache_data(show_spinner=False)
def _load_pyq_file(path, mtime):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return normalize_pyq(json.load(f))
    except Exception:
        return []


def load_pyq_dataset(exam=None):
    """PYQs from pyq_data.json + the shared bank (database) + this session's uploads, de-duplicated."""
    base = _load_pyq_file(PYQ_FILE, os.path.getmtime(PYQ_FILE)) if os.path.exists(PYQ_FILE) else []
    bank = db_load_bank(exam) if exam else []
    out, seen = [], set()
    for x in list(base) + list(bank) + list(st.session_state.get("pyq_uploaded", [])):
        if exam and x["exam"] != exam:
            continue
        h = bank_hash(x)
        if h not in seen:
            seen.add(h)
            out.append(x)
    return out


def parse_pyq_upload(f):
    raw = f.getvalue()
    if f.name.lower().endswith(".json"):
        data = json.loads(raw.decode("utf-8-sig"))
        if isinstance(data, dict):
            data = data.get("questions") or next((v for v in data.values() if isinstance(v, list)), [])
        return normalize_pyq(data)
    df = pd.read_csv(io.BytesIO(raw))
    df.columns = [str(c).strip().lower() for c in df.columns]

    def cell(r, k, d=""):
        v = r.get(k, d)
        return d if pd.isna(v) else str(v).strip()

    items = []
    for _, r in df.iterrows():
        opts = [cell(r, c) for c in ("option_a", "option_b", "option_c", "option_d", "option_e") if cell(r, c)]
        if not opts and cell(r, "options"):
            opts = [o.strip() for o in cell(r, "options").split("|")]
        items.append(
            {
                "exam": cell(r, "exam", "General All Exams"), "subject": cell(r, "subject", "General"), "year": cell(r, "year"),
                "type": cell(r, "type", "mcq"), "question": cell(r, "question"), "options": opts, "answer": cell(r, "answer"),
                "tolerance": cell(r, "tolerance", "0"), "explanation": cell(r, "explanation"),
            }
        )
    return normalize_pyq(items)


def pyq_to_item(x):
    kind = x.get("type", "mcq")
    opts = list(x["options"])
    if kind == "mcq":
        random.shuffle(opts)
    return {
        "type": kind, "question": x["question"], "options": opts, "answer": x["answer"], "answers": [], "accept": [],
        "tol": x.get("tol", 0.0),
        "explanation": x.get("explanation") or "",
        "hint": "", "topic": (x.get("subject") or "General")[:30],
        "level": 2, "src": f"{x['exam']} {x['year']}".strip(),
    }


def pick_from_pool(pool, n, exclude):
    """exclude = set of qhash() values that must not be picked again."""
    fresh = [x for x in pool if qhash(x["question"]) not in exclude]
    return [pyq_to_item(x) for x in random.sample(fresh, min(n, len(fresh)))]


def more_questions(n, avoid_texts):
    """Next n questions for the running quiz: unseen real PYQs first (if any), then AI for the rest (only if allowed)."""
    m = st.session_state.meta
    tkey = m.get("tkey")
    seen_h = set(get_seen_hashes(tkey)) | {qhash(t) for t in avoid_texts}
    pool = m.get("pyq_pool") or []
    got = pick_from_pool(pool, n, seen_h) if pool else []
    need = n - len(got)
    if need > 0 and (not pool or m.get("pyq_fill_ai", False)):
        past = list(avoid_texts) + get_seen_questions(tkey)
        got += generate_with_progress(
            m.get("source", ""), need, m.get("difficulty", "Medium"), m.get("types", ["mcq"]),
            m.get("language", "English"), m.get("model", MODELS[0]), media=m.get("media"),
            avoid=past + [g["question"] for g in got], adaptive=m.get("adaptive", False), exam=m.get("exam"),
        )
    return got


HIST_KEYS = ("time", "topic", "difficulty", "score", "total", "marks", "max", "acc", "pct")


def restore_progress(data):
    ss = st.session_state
    if not isinstance(data, dict):
        raise ValueError(tr("err.bad_file"))
    hist = []
    for h in data.get("history", []):
        if isinstance(h, dict) and all(k in h for k in HIST_KEYS):
            try:
                hist.append(
                    {
                        "time": str(h["time"]), "topic": str(h["topic"]), "difficulty": str(h["difficulty"]),
                        "score": int(h["score"]), "total": max(1, int(h["total"])), "marks": float(h["marks"]),
                        "max": float(h["max"]), "acc": int(h["acc"]), "pct": int(h["pct"]),
                    }
                )
            except Exception:
                continue
    bms = validate_and_shuffle(data.get("bookmarks", []), 2, False)
    ss.total_xp = max(0, int(data.get("xp", 0)))
    ss.history = hist[-200:]
    ss.bookmarks = {b["question"]: b for b in bms}
    return len(ss.history), len(ss.bookmarks)


def extend_quiz(n):
    """Append n fresh questions (no repeats) to the current quiz and resume from the first new one."""
    ss = st.session_state
    m = ss.meta
    new = more_questions(n, [q["question"] for q in ss.quiz])
    if not new:
        return 0

    if ss.result:
        ss.total_xp = max(0, ss.total_xp - ss.result["xp"])
        if ss.history:
            db_undo_result(ss.history.pop().get("id"))

    if m.get("quiz_limit"):
        per_q = m.get("quiz_per_q") or m["quiz_limit"] / max(len(ss.quiz), 1)
        m["quiz_per_q"] = per_q
        m["quiz_limit"] = max(30, round(per_q * len(new)))

    ss.elapsed_before += (ss.end_time or time.time()) - (ss.start_time or time.time())
    ss.start_time = time.time()
    start = len(ss.quiz)
    ss.quiz.extend(new)
    mark_seen(m.get("tkey"), new)
    ss.idx = start
    ss.result = None
    ss.end_time = None
    ss.celebrated = False
    ss.study_plan = ""
    ss.quiz_time_up = False
    ss.q_key = None
    ss.stage = "quiz"
    return len(new)


def reset_all():
    st.session_state.update(fresh_run_state())
    st.session_state.stage = "setup"


def read_pdf(file, start_page, end_page):
    reader = PdfReader(file)
    text = ""
    for p in reader.pages[start_page - 1 : end_page]:
        t = p.extract_text()
        if t:
            text += t + "\n"
    return text, len(reader.pages)


def toggle_bookmark(q):
    bm = st.session_state.bookmarks
    if q["question"] in bm:
        bm.pop(q["question"], None)
        db_sync_bookmark(q, False)
    else:
        bm[q["question"]] = q
        db_sync_bookmark(q, True)


def current_choice(q, qid, i):
    s, t = st.session_state, q["type"]
    if t in ("mcq", "tf"):
        return s.get(f"radio_{qid}_{i}")
    if t == "multi":
        return [o for n, o in enumerate(q["options"]) if s.get(f"cb_{qid}_{i}_{n}")]
    if t in ("blank", "num"):
        return s.get(f"txt_{qid}_{i}")
    return s.get(f"ta_{qid}_{i}")


def answer_widget(q, qid, i, locked, prev):
    t = q["type"]
    if t in ("mcq", "tf"):
        idx = q["options"].index(prev) if prev in q["options"] else None
        return st.radio(
            tr("qz.choose"), q["options"], index=idx, key=f"radio_{qid}_{i}", disabled=locked, label_visibility="collapsed",
            format_func=(i18n.fmt("tf") if t == "tf" else str),
        )
    if t == "multi":
        st.caption(tr("qz.multi_cap"))
        chosen = set(prev or [])
        sel = []
        for n, o in enumerate(q["options"]):
            if st.checkbox(o, value=(o in chosen), key=f"cb_{qid}_{i}_{n}", disabled=locked):
                sel.append(o)
        return sel
    if t == "num":
        return st.text_input(tr("qz.num_label"), value=prev or "", key=f"txt_{qid}_{i}", disabled=locked, placeholder=tr("qz.num_ph"))
    if t == "blank":
        return st.text_input(tr("qz.blank_label"), value=prev or "", key=f"txt_{qid}_{i}", disabled=locked, placeholder=tr("qz.blank_ph"))
    return st.text_area(tr("qz.short_label"), value=prev or "", key=f"ta_{qid}_{i}", height=120, disabled=locked, placeholder=tr("qz.short_ph"))


def feedback_html(i, q, timed_out):
    ss = st.session_state
    prev = ss.answers.get(i)
    ok = is_correct(i)

    if q["type"] == "short":
        g = ss.grades.get(i, {"score": 0, "feedback": ""})
        cls = "ok" if ok else ("mid" if g["score"] >= 0.3 else "no")
        head = tr("fb.short_ok") if ok else tr("fb.short_bad")
        return (
            f"<div class='qf-fb {cls}'>{head} {tr('fb.ai_score')} <b>{g['score']:.1f} / 1</b><br>{esc(grade_feedback(g))}"
            f"<br><br><b>{tr('fb.model_ans')}</b> {esc(q['answer'])}<br>{esc(explanation_text(q))}</div>"
        )
    if ok:
        return f"<div class='qf-fb ok'>{tr('fb.correct')}<br>{esc(explanation_text(q))}</div>"

    why = tr("fb.timeup") if timed_out else (tr("fb.skipped") if prev is None else tr("fb.wrong"))
    shown = " · ".join(disp(q, a) for a in q["answers"]) if q["type"] == "multi" else disp(q, q["answer"])
    return f"<div class='qf-fb no'>{why}{tr('fb.correct_is')} <b>{esc(shown)}</b><br>{esc(explanation_text(q))}</div>"


def build_report_html():
    ss = st.session_state
    r = ss.result
    rows = ""
    for i, q in enumerate(ss.quiz):
        ok = is_correct(i)
        rows += (
            f"<tr><td>{i + 1}</td><td>{esc(q['question'])}</td><td>{esc(user_text(i))}</td>"
            f"<td>{esc(correct_text(q))}</td><td style='color:{'#1FA67A' if ok else '#E5484D'}'>{'✔' if ok else '✘'}</td>"
            f"<td>{esc(explanation_text(q))}</td></tr>"
        )
    title = esc(tr("report.title", app=APP_NAME))
    html_lang = i18n.LANGS[i18n.cur()]["html"]
    return f"""<!doctype html><html lang="{html_lang}"><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:Arial,'Noto Sans Devanagari',sans-serif;max-width:900px;margin:30px auto;padding:0 16px;color:#222}}
h1{{color:#4B3FD1}} table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #ddd;padding:8px;font-size:14px;vertical-align:top}}
th{{background:#4B3FD1;color:#fff}} .s{{font-size:20px;margin:10px 0}}</style></head><body>
<h1>{title}</h1>
<p>{esc(topic_label(ss.meta.get('label', 'Quiz')))} · {esc(i18n.fmt('diff')(ss.meta.get('difficulty', '')))} · {i18n.localize_time(datetime.now().strftime('%d %b %Y, %H:%M'))}</p>
<p class="s"><b>{tr('res.marks')}:</b> {fmt_marks(r['marks'])}/{fmt_marks(r['max_marks'])} &nbsp; <b>{tr('res.accuracy')}:</b> {r['accuracy']}% &nbsp; <b>{tr('res.correct')}:</b> {r['score']}/{r['total']} &nbsp; <b>XP:</b> {r['xp']} &nbsp; <b>{tr('res.best_streak')}:</b> {r['best_streak']}</p>
<table><tr><th>#</th><th>{tr('report.q')}</th><th>{tr('report.your')}</th><th>{tr('report.correct')}</th><th></th><th>{tr('report.expl')}</th></tr>{rows}</table>
</body></html>"""


# ─────────────────────────────────────────────────────────────
# BROWSER LAYER: sound effects, text-to-speech, keyboard shortcuts
# ─────────────────────────────────────────────────────────────
QF_VERSION = 4
QF_JS = r"""
(function(){
  var old = window.qf; if (old && old.off) { try { old.off(); } catch(e) {} }
  var qf = {v:__V__, muted:false, lang:'en-IN', rate:1, cur:null, ac:null, lastAuto:null};
  qf.ctx = function(){
    var C = window.AudioContext || window.webkitAudioContext; if(!C) return null;
    if(!qf.ac) qf.ac = new C(); if(qf.ac.state === 'suspended') qf.ac.resume(); return qf.ac;
  };
  qf.tone = function(f, t0, d, type, vol){
    var c = qf.ctx(); if(!c) return;
    var o = c.createOscillator(), g = c.createGain(), t = c.currentTime + t0;
    o.type = type || 'sine'; o.frequency.value = f;
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(vol || 0.16, t + 0.02);
    g.gain.exponentialRampToValueAtTime(0.0001, t + d);
    o.connect(g); g.connect(c.destination); o.start(t); o.stop(t + d + 0.05);
  };
  qf.play = function(name){
    if(qf.muted) return;
    try {
      if(name === 'correct'){ qf.tone(659,0,.14); qf.tone(880,.11,.22); }
      else if(name === 'wrong'){ qf.tone(196,0,.22,'sawtooth',.10); qf.tone(147,.14,.32,'sawtooth',.10); }
      else if(name === 'win'){ [523,659,784,1047].forEach(function(f,i){ qf.tone(f,i*.12,i===3?.5:.18,'triangle',.18); }); }
      else if(name === 'lose'){ [392,330,262].forEach(function(f,i){ qf.tone(f,i*.16,.3,'triangle',.14); }); }
    } catch(e) {}
  };
  qf.speak = function(text){
    var s = window.speechSynthesis; if(!s || !text) return;
    s.cancel();
    var u = new SpeechSynthesisUtterance(text); u.lang = qf.lang; u.rate = qf.rate;
    var vs = s.getVoices() || [], pre = qf.lang.slice(0,2);
    var v = vs.find(function(x){ return x.lang === qf.lang; }) || vs.find(function(x){ return x.lang.indexOf(pre) === 0; });
    if(v) u.voice = v; s.speak(u);
  };
  qf.speakCur = function(){ if(qf.cur) qf.speak(qf.cur.text); };
  var onKey = function(e){
    var t = e.target, tag = ((t && t.tagName) || '').toLowerCase();
    if(tag === 'input' || tag === 'textarea' || tag === 'select' || (t && t.isContentEditable)) return;
    if(e.ctrlKey || e.metaKey || e.altKey) return;
    var clickBtn = function(re){
      var b = Array.prototype.slice.call(document.querySelectorAll('button')).find(function(x){
        return re.test(x.innerText) && !x.disabled && x.offsetParent !== null; });
      if(b){ b.click(); return true; } return false;
    };
    if(/^[1-9]$/.test(e.key)){
      var labels = document.querySelectorAll('.st-key-optbox label[data-baseweb="radio"], .st-key-optbox label[data-baseweb="checkbox"]');
      var n = parseInt(e.key, 10) - 1;
      if(labels[n]){ labels[n].click(); e.preventDefault(); }
    } else if(e.key === 'Enter'){
      if(tag === 'button') return;
      if(clickBtn(new RegExp(qf.reEnter || 'Check answer|Next|Finish|Submit'))) e.preventDefault();
    } else if(e.key === 'h' || e.key === 'H'){ clickBtn(new RegExp(qf.reHint || 'Hint')); }
    else if(e.key === 's' || e.key === 'S'){ clickBtn(new RegExp(qf.reSkip || 'Skip')); }
    else if(e.key === 'r' || e.key === 'R'){ qf.speakCur(); }
  };
  document.addEventListener('keydown', onKey, true);
  qf.off = function(){ document.removeEventListener('keydown', onKey, true); };
  window.qf = qf;
})();
""".replace("__V__", str(QF_VERSION))

BOOT_TEMPLATE = """<script>(function(){var P=window.parent;try{
if(!P.qf||P.qf.v!==__V__){var s=P.document.createElement('script');s.textContent=__CODE__;P.document.head.appendChild(s);}
var qf=P.qf;Object.assign(qf,__CFG__);qf.cur=__CUR__;
__SOUND__
__AUTO__
}catch(e){console.warn('qf',e);}})();</script><!--__NONCE__-->"""

SPEAK_BTN_TEMPLATE = """<style>
body{margin:0;display:flex;gap:6px;font-family:'Plus Jakarta Sans',Arial,sans-serif}
button{flex:1;height:40px;border-radius:13px;border:1px solid __LINE__;background:__BG__;color:__FG__;font-weight:700;font-size:14px;cursor:pointer}
button:hover{border-color:#22D3EE}
#stop{flex:0 0 44px}
</style>
<button id="b" title="__LISTENTIP__">🔊 __LISTEN__</button><button id="stop" title="__STOP__">⏹</button>
<script>
var T=__TEXT__;
document.getElementById('b').onclick=function(){var q=window.parent.qf;if(q){q.cur={text:T};q.speakCur();}};
document.getElementById('stop').onclick=function(){var s=window.parent.speechSynthesis;if(s)s.cancel();};
</script>"""


def render_browser_layer(sound_on, tts_lang, tts_rate, auto_read):
    ss = st.session_state
    sound = ss.pop("sound", None)
    cur, auto_key = "null", None
    if ss.stage == "quiz" and ss.quiz and ss.idx < len(ss.quiz):
        q = ss.quiz[ss.idx]
        cur = json.dumps({"text": speech_text(q)})
        if auto_read and not ss.locked.get(ss.idx):
            auto_key = f"{ss.quiz_id}-{ss.idx}"
    js = (
        BOOT_TEMPLATE.replace("__V__", str(QF_VERSION))
        .replace("__CODE__", json.dumps(QF_JS))
        .replace("__CFG__", json.dumps({"muted": not sound_on, "lang": tts_lang, "rate": tts_rate, "reEnter": i18n.shortcut_regex("enter"), "reHint": i18n.shortcut_regex("hint"), "reSkip": i18n.shortcut_regex("skip")}))
        .replace("__CUR__", cur)
        .replace("__SOUND__", f"qf.play({json.dumps(sound)});" if sound else "")
        .replace(
            "__AUTO__",
            f"if(qf.lastAuto!=={json.dumps(auto_key)}){{qf.lastAuto={json.dumps(auto_key)};setTimeout(function(){{qf.speakCur();}},250);}}"
            if auto_key
            else "",
        )
        .replace("__NONCE__", str(time.time()))
    )
    components.html(i18n.bridge_js() + js, height=0)  # bridge = save/restore the chosen language in localStorage


def speak_button(text):
    colors = (
        {"__LINE__": "rgba(30,35,80,.2)", "__BG__": "#ffffff", "__FG__": "#1B1F3B"}
        if LIGHT
        else {"__LINE__": "rgba(255,255,255,.14)", "__BG__": "rgba(255,255,255,.07)", "__FG__": "#E8EAF6"}
    )
    code = (
        SPEAK_BTN_TEMPLATE.replace("__TEXT__", json.dumps(text))
        .replace("__LISTENTIP__", tr("qz.listen_tip"))
        .replace("__LISTEN__", tr("qz.listen"))
        .replace("__STOP__", tr("qz.stop"))
    )
    for k, v in colors.items():
        code = code.replace(k, v)
    components.html(code, height=42)


# ─────────────────────────────────────────────────────────────
# COUNTDOWN (auto-refreshing fragment)
# ─────────────────────────────────────────────────────────────
def _countdown(limit, qid, i, total, instant):
    ss = st.session_state
    left = limit - (time.time() - ss.q_start)
    if left > 0:
        st.progress(max(left / limit, 0.0), text=tr("qz.countdown", n=math.ceil(left)))
        return
    q = ss.quiz[i]
    ss.answers[i] = norm_answer(current_choice(q, qid, i))
    record_time(i)
    if instant:
        if q["type"] == "short" and ss.answers[i]:
            grade_short(i)
        ss.locked[i] = True
        ss.timed_out[i] = True
        queue_sound("wrong")
    elif i == total - 1:
        finish_quiz()
    else:
        advance(i)
    st.rerun()


def _quiz_countdown(total_secs, qid, i):
    ss = st.session_state
    left = total_secs - (time.time() - ss.start_time)
    if left > 0:
        m, sec = divmod(math.ceil(left), 60)
        st.progress(max(left / total_secs, 0.0), text=tr("qz.quiz_countdown", m=m, s=sec))
        return
    q = ss.quiz[i]
    if not ss.locked.get(i):
        ss.answers[i] = norm_answer(current_choice(q, qid, i))
        record_time(i)
    ss.quiz_time_up = True
    finish_quiz()
    st.rerun()


_fragment = getattr(st, "fragment", None)
countdown = _fragment(run_every=1)(_countdown) if _fragment else None
quiz_countdown = _fragment(run_every=1)(_quiz_countdown) if _fragment else None

# ─────────────────────────────────────────────────────────────
# LOGIN GATE
# ─────────────────────────────────────────────────────────────
CM = ensure_auth()

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    lvl = level_of(st.session_state.total_xp)
    st.markdown(tr("side.level", n=lvl))
    st.progress(
        (st.session_state.total_xp % 100) / 100,
        text=tr("side.xp", xp=st.session_state.total_xp, n=100 - st.session_state.total_xp % 100),
    )

    st.markdown(tr("side.settings"))

    # ── Language: app (UI) language switcher + quiz-content language ──
    st.markdown(tr("lang.app_title"))
    i18n.render_switcher("side")
    language = st.selectbox(
        tr("lang.quiz"), ["English", "Hindi", "Hinglish"], format_func=i18n.fmt("qlang"), key="language", help=tr("lang.quiz_help"),
    )

    num_questions = st.slider(tr("side.questions"), 3, 50, 5, key="num_questions", help=tr("side.questions_help"))
    difficulty = st.select_slider(
        tr("side.difficulty"), ["Easy", "Medium", "Hard"], value="Medium", key="difficulty", format_func=i18n.fmt("diff"),
    )
    adaptive = st.toggle(tr("side.adaptive"), value=False, key="adaptive", help=tr("side.adaptive_help"))
    type_sel = st.multiselect(
        tr("side.qtypes"), list(TYPE_MAP.keys()), default=["Multiple Choice", "True / False"], key="type_sel",
        format_func=lambda x: tr(f"qtype.long.{TYPE_MAP[x]}"),
    )
    type_keys = [TYPE_MAP[x] for x in type_sel] or ["mcq"]

    mode = st.radio(
        tr("side.mode"), ["Practice", "Exam", "Survival"], key="mode", format_func=i18n.fmt("mode"), help=tr("side.mode_help"),
    )
    st.markdown(tr("side.timer"))
    timer_mode = st.selectbox(
        tr("side.timer_type"), ["off", "per_q", "whole"], key="timer_mode", format_func=i18n.fmt("timer"), label_visibility="collapsed",
    )
    _pick_fmt = lambda v: tr("common.custom") if v == "Custom" else str(v)
    time_limit = quiz_limit = 0
    if timer_mode == "per_q":
        pick = st.selectbox(tr("side.secs"), [10, 15, 20, 30, 45, 60, 90, 120, "Custom"], index=3, key="pick_secs", format_func=_pick_fmt)
        time_limit = int(st.number_input(tr("side.secs_custom"), 5, 600, 30, 5, key="custom_secs")) if pick == "Custom" else int(pick)
        st.caption(tr("side.secs_help"))
    elif timer_mode == "whole":
        pick = st.selectbox(tr("side.mins"), [5, 10, 15, 20, 30, 45, 60, 90, "Custom"], index=1, key="pick_mins", format_func=_pick_fmt)
        mins = int(st.number_input(tr("side.mins_custom"), 1, 180, 10, 1, key="custom_mins")) if pick == "Custom" else int(pick)
        quiz_limit = mins * 60
        st.caption(tr("side.mins_cap", n=f"{quiz_limit / max(num_questions, 1):.0f}"))
    if (time_limit or quiz_limit) and countdown is None:
        st.warning(tr("side.timer_need"))

    st.markdown(tr("side.marking"))
    marks_correct = float(st.selectbox(tr("side.marks_per"), [1, 2, 4, 5], index=0, key="marks_sel"))
    neg_key = st.selectbox(tr("side.neg"), list(NEG_FRAC), key="neg_sel", format_func=_neg_label, help=tr("side.neg_help"))
    neg_frac = NEG_FRAC[neg_key]
    st.caption(tr("side.marks_cap", c=fmt_marks(marks_correct), w=fmt_marks(marks_correct * neg_frac)))

    with st.expander(tr("side.sound_look")):
        sound_on = st.toggle(tr("side.sound"), value=True, key="sound_on")
        auto_read = st.toggle(tr("side.auto_read"), value=False, key="auto_read", help=tr("side.auto_read_help"))
        tts_rate = st.slider(tr("side.speed"), 0.6, 1.4, 1.0, 0.1, key="tts_rate")
        st.toggle(tr("side.light"), value=False, key="light")
        st.toggle(tr("side.tutor"), value=True, key="tutor_on")
        st.selectbox(tr("side.tutor_char"), ["girl", "boy"], key="tutor_char", format_func=lambda k: tr("av.char_" + k))
    with st.expander(tr("side.advanced")):
        model = st.selectbox(tr("side.model"), MODELS, key="model_sel", help=tr("side.model_help"))

    st.divider()
    nb = len(st.session_state.bookmarks)
    st.markdown(tr("side.saved"))
    if nb:
        st.caption(tr("side.saved_n", n=nb))
        if st.session_state.stage != "quiz" and st.button(tr("side.flash_btn"), use_container_width=True):
            st.session_state.flash_cards = list(st.session_state.bookmarks.values())
            st.session_state.flash_i = 0
            st.session_state.flash_show = False
            st.session_state.flash_return = st.session_state.stage
            st.session_state.stage = "flash"
            st.rerun()
    else:
        st.caption(tr("side.saved_hint"))

    st.divider()
    st.markdown(tr("side.history"))
    if st.session_state.history:
        for h in reversed(st.session_state.history[-6:]):
            st.markdown(
                f"**{esc(topic_label(h['topic']))[:28]}**  \n"
                + tr("side.hist_item", marks=fmt_marks(h["marks"]), max=fmt_marks(h["max"]), acc=h["acc"], diff=i18n.fmt("diff")(h["difficulty"]))
                + f"  \n<small style='opacity:.6'>{i18n.localize_time(h['time'])}</small>",
                unsafe_allow_html=True,
            )
        st.caption(tr("side.best", n=max(h["pct"] for h in st.session_state.history)))
        if st.button(tr("side.clear_hist")):
            db_clear_history()
            st.session_state.history = []
            st.rerun()
    else:
        st.caption(tr("side.no_hist"))

    st.divider()
    if AUTH_ENABLED and st.session_state.get("user"):
        _u = st.session_state["user"]
        st.markdown(tr("side.account"))
        st.caption(_u.get("email") or _u.get("phone") or tr("side.logged_in"))
        if st.session_state.get("is_admin"):
            st.caption(tr("side.admin"))
        if st.session_state.get("_db_err"):
            st.warning(tr("side.db_warn"))
            st.caption(st.session_state["_db_err"])
        if st.button(tr("side.logout"), use_container_width=True):
            do_logout(CM)
    else:
        if not AUTH_CONFIGURED:
            st.caption(tr("side.guest"))
        st.markdown(tr("side.backup"))
        st.caption(tr("side.backup_cap"))
        _backup = json.dumps(
            {"v": 1, "xp": st.session_state.total_xp, "history": st.session_state.history, "bookmarks": list(st.session_state.bookmarks.values())},
            ensure_ascii=False,
        )
        st.download_button(tr("side.backup_dl"), _backup.encode("utf-8"), file_name="quiz_progress.json", mime="application/json", use_container_width=True)
        _up = st.file_uploader(tr("side.backup_up"), type=["json"], key="prog_up")
        if _up is not None:
            _sig = (_up.name, _up.size)
            if st.session_state.get("_prog_sig") != _sig:
                try:
                    _nh, _nb = restore_progress(json.loads(_up.getvalue().decode("utf-8-sig")))
                    st.session_state["_prog_sig"] = _sig
                    st.session_state["_prog_msg"] = (_nh, _nb)
                    st.rerun()
                except Exception as e:
                    st.error(tr("err.load_failed", e=e))
        if st.session_state.get("_prog_msg"):
            _h, _b = st.session_state["_prog_msg"]
            st.success(tr("side.backup_ok", h=_h, b=_b))

# ─────────────────────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────────────────────
_order = {"setup": 0, "quiz": 1, "result": 2}
_cur = _order.get(st.session_state.stage, -1)
_steps = ""
step_names = [tr("hero.step1"), tr("hero.step2"), tr("hero.step3")]

for n, name in enumerate(step_names):
    cls = "on" if n == _cur else ("done" if 0 <= _cur and n < _cur else "")
    _steps += f"<span class='qf-step {cls}'><i>{'✓' if cls == 'done' else n + 1}</i>{name}</span>"

hero_sub = tr("hero.sub")

# top bar: brand + language switcher (always reachable, even when the sidebar is collapsed on mobile)
_LOGO = "<svg viewBox='0 0 24 24'><path d='M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z'/><path d='M19 3v4M17 5h4'/></svg>"
with st.container(key="navbar"):
    st.markdown(f"<div class='qf-brand'><span class='mk'>{_LOGO}</span>{esc(APP_NAME)}</div>", unsafe_allow_html=True)
    with st.container(key="langbar"):
        i18n.render_switcher("top")


def _greeting_text():
    h = (datetime.utcnow() + timedelta(hours=5, minutes=30)).hour  # IST
    return tr("th.gm" if 5 <= h < 12 else "th.ga" if 12 <= h < 17 else "th.ge" if 17 <= h < 22 else "th.gn")


def _who_text():
    u = st.session_state.get("user") or {}
    try:
        if u.get("email"):
            return u["email"].split("@")[0]
        if u.get("phone"):
            return mask_ident(u["phone"])
    except Exception:
        pass
    return tr("th.guest")


_xp_into = st.session_state.total_xp % 100
_hero_cls = "qf-hero" if st.session_state.stage == "setup" else "qf-hero compact"
st.markdown(
    f"<div class=\"{_hero_cls}\"><span class=\"qf-blob b1\"></span><span class=\"qf-blob b2\"></span>"
    f"<div class=\"qf-hero-main\"><div class=\"qf-eyebrow\"><span class=\"dot\"></span><span class=\"nm\">{esc(_greeting_text())}, {esc(_who_text())}</span></div>"
    f"<div class=\"qf-title qf-display\">{tr('hero.h1')}</div><div class=\"qf-sub\">{hero_sub}</div>"
    f"<div class=\"qf-steps\">{_steps}</div></div>"
    f"<div class=\"qf-xp\"><div class=\"qf-xpring\" style=\"--p:{_xp_into}\"><b>{lvl}</b></div>"
    f"<div><div class=\"a\">{tr('th.lvl')} {lvl}</div><div class=\"b\">{tr('th.xp_next', n=100 - _xp_into)}</div></div></div></div>",
    unsafe_allow_html=True,
)

# ═════════════════════════════════════════════════════════════
# STAGE · SETUP
# ═════════════════════════════════════════════════════════════
def base_meta(cfg, label, source, media=None, **extra):
    m = {
        "label": label, "difficulty": cfg["difficulty"], "mode": cfg["mode"], "source": source, "media": media,
        "types": cfg["type_keys"], "adaptive": cfg["adaptive"], "language": cfg["language"], "model": cfg["model"],
        "time_limit": cfg["time_limit"], "quiz_limit": cfg["quiz_limit"], "marks": cfg["marks"], "neg": cfg["neg"],
    }
    m.update(extra)
    return m


def launch_quiz(input_text, label, cfg, media=None):
    with st.spinner(tr("qt.spinner")):
        try:
            if input_text.startswith("Topic:"):
                ident = label
            elif media:
                ident = f"{label}|{hashlib.md5(media['bytes']).hexdigest()[:8]}"
            else:
                ident = f"{label}|{qhash(input_text[:2000])[:8]}"
            tkey = topic_key_for("ai", ident)
            quiz = generate_with_progress(
                input_text, cfg["num_questions"], cfg["difficulty"], cfg["type_keys"], cfg["language"], cfg["model"],
                media=media, adaptive=cfg["adaptive"], avoid=get_seen_questions(tkey),
            )
            if not quiz:
                st.error(tr("err.no_valid"))
                return
            start_quiz(quiz, base_meta(cfg, label, input_text, media, tkey=tkey))
            st.session_state["_picked"] = ""
            st.rerun()
        except json.JSONDecodeError:
            st.error(tr("err.ai_parse"))
        except Exception as e:
            st.error(friendly_error(e))


# ── TAB 1 · QUIZ ARENA ───────────────────────────────────────
def render_quiz_tab(cfg):
    with st.container(key="srcpick"):
        source = st.radio(tr("qt.where"), ["topic", "pdf", "photo", "notes"], format_func=i18n.fmt("src"), horizontal=True, key="src_pick")

    input_text, label, media = "", "", None

    with st.container(key="panel"):
        if source == "topic":
            topic = st.text_input(tr("qt.topic_label"), placeholder=tr("qt.topic_ph"), key="topic_in")
            st.caption(tr("qt.quick"))
            cols = st.columns(4)
            for c, n in zip(cols, range(1, 5)):
                pick = tr(f"pick.{n}")
                if c.button(pick, use_container_width=True, key=f"pick_{n}"):
                    st.session_state["_picked"] = pick
                    st.rerun()
            if st.session_state.get("_picked") and not topic:
                topic = st.session_state["_picked"]
                st.info(tr("qt.selected_topic", t=topic))
            if topic.strip():
                input_text = f"Topic: {topic.strip()}\nUse your own knowledge to cover this topic accurately."
                label = topic.strip()

        elif source == "pdf":
            up = st.file_uploader(tr("qt.upload_pdf"), type=["pdf"], key="quiz_pdf")
            if up is not None:
                try:
                    _, total_pages = read_pdf(up, 1, 1)
                    up.seek(0)
                    rng = (
                        st.slider(tr("qt.page_range"), 1, total_pages, (1, min(total_pages, 10)), key=f"pdf_rng_{up.name}_{total_pages}")
                        if total_pages > 1
                        else (1, 1)
                    )
                    pdf_text, _ = read_pdf(up, rng[0], rng[1])
                    if pdf_text.strip():
                        st.success(tr("qt.pdf_ok", n=rng[1] - rng[0] + 1, c=len(pdf_text)))
                        if len(pdf_text) > MAX_CHARS:
                            st.warning(tr("qt.pdf_long", m=MAX_CHARS))
                        input_text, label = pdf_text, f"PDF: {up.name}"
                    else:
                        st.error(tr("qt.pdf_scanned"))
                except Exception as e:
                    st.error(tr("qt.pdf_err", e=e))

        elif source == "photo":
            st.caption(tr("qt.photo_cap"))
            photo_mode = st.radio(tr("qt.photo_mode"), ["upload", "camera"], format_func=i18n.fmt("photo"), horizontal=True, key="quiz_photo_mode")
            mf = (
                st.file_uploader(tr("qt.photo_up"), type=["png", "jpg", "jpeg", "webp"], key="media_up")
                if photo_mode == "upload"
                else st.camera_input(tr("qt.photo_cam"), key="quiz_cam")
            )
            if mf is not None:
                raw = mf.getvalue()
                if len(raw) > MAX_RAW_IMG_BYTES:
                    st.error(tr("err.photo_big"))
                else:
                    data, mime = prepare_image(raw, getattr(mf, "type", None) or "image/jpeg")
                    if len(data) > MAX_IMG_BYTES:
                        st.error(tr("err.photo_big2"))
                    else:
                        st.image(data, caption=tr("qt.selected_photo"), use_container_width=True)
                        media = {"bytes": data, "mime": mime}
                        input_text, label = "(attached image)", f"Photo: {getattr(mf, 'name', 'Camera picture')}"

        else:
            pasted = st.text_area(tr("qt.notes_label"), height=200, placeholder=tr("qt.notes_ph"), key="notes_in")
            if pasted.strip():
                st.caption(tr("qt.chars", n=len(pasted)))
                input_text, label = pasted, "Pasted notes"

    st.write("")
    if st.button(tr("qt.make"), type="primary", use_container_width=True):
        if not input_text.strip():
            st.warning(tr("qt.need_input"))
        else:
            launch_quiz(input_text, label, cfg, media)


def plan_sections(conf, n_total, subject, mock, factor):
    """Return [(subject, qtype, count)] following the exam's section pattern."""
    secs = conf["sections"] if conf else [("Mixed", {"mcq": 1})]
    if subject != "All subjects":
        secs = [x for x in secs if x[0] == subject] or [(subject, {"mcq": 1})]
    entries = [(subj, t, cnt) for subj, mix in secs for t, cnt in mix.items()]
    if mock:
        return [(subj, t, max(1, round(cnt * factor))) for subj, t, cnt in entries]
    total_w = sum(c for _, _, c in entries) or 1
    raw = [n_total * c / total_w for _, _, c in entries]
    alloc = [int(x) for x in raw]
    for k in sorted(range(len(raw)), key=lambda k: raw[k] - alloc[k], reverse=True)[: n_total - sum(alloc)]:
        alloc[k] += 1
    return [(subj, t, a) for (subj, t, _), a in zip(entries, alloc) if a > 0]


def build_pyq_quiz(exam, cfg, pool, fill_ai, plan):
    quiz, notes = [], []
    for subj, t, n in plan:
        sec_pool = [x for x in pool if x.get("type", "mcq") == t and (subj == "Mixed" or x["subject"].strip().lower() == subj.lower())]
        taken = {qhash(q["question"]) for q in quiz}
        got = pick_from_pool(sec_pool, n, taken)
        need = n - len(got)
        if need > 0 and (fill_ai or not pool):
            subj_txt = "mixed subjects of the syllabus" if subj == "Mixed" else subj
            src = f"Exam: {exam}\nSubject: {subj_txt}\nCreate practice questions matching the real exam pattern."
            if t == "num":
                src += " The answer of every question must be a single number."
            try:
                got += generate_with_progress(
                    src, need, cfg["difficulty"], [t], cfg["language"], cfg["model"],
                    avoid=[q["question"] for q in quiz] + [g["question"] for g in got], adaptive=False, exam=f"{exam} · {subj}",
                )
            except Exception as e:
                notes.append(tr("pyq.ai_fill_fail", subj=subj, err=friendly_error(e)))
                for g in got:
                    g["topic"] = subj[:30]
                quiz += got
                break
        for g in got:
            g["topic"] = subj[:30]  # subject-wise analytics
        quiz += got
    return quiz, notes


def render_pyq_tab(cfg):
    ss = st.session_state
    st.markdown(tr("pyq.title"))
    st.caption(tr("pyq.intro"))

    with st.container(key="panel_pyq"):
        exam = st.selectbox(tr("pyq.exam"), EXAM_LIST, key="pyq_exam", format_func=i18n.fmt("exam"))
        conf = EXAM_CONFIG.get(exam)
        dataset = load_pyq_dataset(exam)
        known = sorted({q["subject"] for q in dataset})
        base_subjects = EXAM_SUBJECTS.get(exam, [])
        subjects = ["All subjects"] + base_subjects + [k for k in known if k not in base_subjects]
        subject = st.selectbox(tr("pyq.subject"), subjects, key=f"pyq_subject_{exam}", format_func=i18n.fmt("subj"))
        pool_all = [q for q in dataset if subject == "All subjects" or q["subject"].strip().lower() == subject.lower()]
        years = sorted({q["year"] for q in pool_all if q["year"]}, reverse=True)
        sel_years = st.multiselect(tr("pyq.year"), years, key=f"pyq_years_{exam}_{subject}") if years else []
        pool = [q for q in pool_all if not sel_years or q["year"] in sel_years]

        tkey = f"pyq::{exam}"
        seen_h = get_seen_hashes(tkey)
        fresh_pool = [q for q in pool if qhash(q["question"]) not in seen_h]
        if not dataset:
            st.error(tr("pyq.no_dataset", exam=i18n.fmt("exam")(exam)))
        elif not pool:
            st.info(tr("pyq.no_pool"))
        elif not fresh_pool:
            st.warning(tr("pyq.all_done", n=len(pool)))
            if st.button(tr("pyq.reset_seen"), key="pyq_reset_seen"):
                reset_seen(tkey)
                st.rerun()
        else:
            st.success(tr("pyq.avail", n=len(fresh_pool), d=len(pool) - len(fresh_pool)))
        fill_ai = st.toggle(tr("pyq.fill_ai"), value=False, key=f"pyq_fill_{exam}", help=tr("pyq.fill_help"))

        official, neg_override, num_neg = False, None, True
        if conf:
            official = st.radio(tr("pyq.mark_scheme"), ["official", "sidebar"], format_func=i18n.fmt("mark"), horizontal=True, key=f"pyq_mark_{exam}") == "official"
            if official:
                st.caption(tr("pyq.official_cap", m=fmt_marks(conf["marks"]), p=fmt_marks(conf["marks"] * conf["neg"]), note=tr(f"note.{exam}")))
                with st.expander(tr("pyq.adjust")):
                    neg_override = NEG_CHOICES[st.selectbox(tr("pyq.neg"), list(NEG_CHOICES), key=f"pyq_neg_{exam}", format_func=i18n.fmt("negc"))]
                    if any("num" in mix for _, mix in conf["sections"]):
                        num_neg = st.toggle(tr("pyq.num_neg"), value=True, key=f"pyq_numneg_{exam}")
        else:
            st.caption(tr("pyq.sidebar_marking"))

        use_pattern, factor = False, 1.0
        if conf:
            use_pattern = st.toggle(tr("pyq.mock"), key=f"pyq_pattern_{exam}")
            if use_pattern:
                size = st.radio(tr("pyq.mock_size"), ["Full", "Half", "Quarter"], format_func=i18n.fmt("size"), horizontal=True, key=f"pyq_size_{exam}")
                factor = {"Full": 1.0, "Half": 0.5, "Quarter": 0.25}[size]

    if conf and official:
        marks_used = conf["marks"]
        neg_used = conf["neg"] if neg_override is None else neg_override
        no_neg = ["num"] if (any("num" in mix for _, mix in conf["sections"]) and not num_neg) else []
    else:
        marks_used, neg_used, no_neg = cfg["marks"], cfg["neg"], []
    plan = plan_sections(conf, cfg["num_questions"], subject, use_pattern, factor)
    plan_n = sum(n for _, _, n in plan)
    full_total = sum(sum(m.values()) for _, m in conf["sections"]) if conf else 0

    if use_pattern:
        mins_plan = max(5, round(conf["minutes"] * plan_n / full_total)) if full_total else 0
        st.info(tr("pyq.mock_info", n=plan_n, m=mins_plan, mx=fmt_marks(plan_n * marks_used), a=fmt_marks(marks_used), b=fmt_marks(marks_used * neg_used)))
        if len(fresh_pool) < plan_n and not fill_ai:
            st.caption(tr("pyq.mock_short", n=len(fresh_pool)))
    else:
        st.caption(tr("pyq.practice_cap", n=min(plan_n, len(fresh_pool)) if not fill_ai else plan_n))

    with st.expander(tr("pyq.bank")):
        st.caption(tr("pyq.bank_cap", exams=", ".join(EXAM_LIST)))
        if ss.get("is_admin"):
            st.success(tr("pyq.admin_ok"))
        elif db_on():
            st.caption(tr("pyq.bank_note"))
        st.download_button(tr("pyq.template"), PYQ_TEMPLATE.encode("utf-8"), file_name="pyq_template.json", mime="application/json")
        up = st.file_uploader(tr("pyq.file"), type=["json", "csv"], key="pyq_up")
        if up is not None:
            sig = (up.name, up.size)
            if ss.get("_pyq_sig") != sig:
                try:
                    items = parse_pyq_upload(up)
                    have = {bank_hash(q) for q in ss.pyq_uploaded}
                    fresh = [q for q in items if bank_hash(q) not in have]
                    ss.pyq_uploaded += fresh
                    ss["_pyq_items"] = items
                    ss["_pyq_sig"] = sig
                    ss["_pyq_msg"] = (len(fresh), len(items) - len(fresh))
                    st.rerun()
                except Exception as e:
                    st.error(tr("pyq.file_err", e=e))
        if ss.get("_pyq_msg"):
            st.success(tr("pyq.added", n=ss["_pyq_msg"][0], d=ss["_pyq_msg"][1]))
        if ss.get("is_admin") and ss.get("_pyq_items"):
            if st.button(tr("pyq.save_bank", n=len(ss["_pyq_items"])), key="pyq_bank_save"):
                try:
                    st.success(tr("pyq.bank_saved", n=db_save_bank(ss["_pyq_items"])))
                    ss["_pyq_items"] = []
                except Exception as e:
                    st.error(tr("pyq.bank_fail", e=e))
        if ss.pyq_uploaded:
            st.caption(tr("pyq.uploaded_n", n=len(ss.pyq_uploaded)))
            if st.button(tr("pyq.clear"), key="pyq_clear"):
                ss.pyq_uploaded = []
                ss["_pyq_sig"] = None
                ss["_pyq_msg"] = None
                ss["_pyq_items"] = []
                st.rerun()

    st.write("")
    can_start = bool(fresh_pool) or fill_ai
    start_label = tr("pyq.start_mock" if use_pattern else "pyq.start_prac", exam=i18n.fmt("exam")(exam))
    if st.button(start_label, type="primary", use_container_width=True, key="btn_start_pyq", disabled=not can_start):
        label_exam = exam if subject == "All subjects" else f"{exam} · {subject}"
        subj_txt = "mixed subjects of the syllabus" if subject == "All subjects" else subject
        src_main = f"Exam: {exam}\nSubject: {subj_txt}\nCreate practice questions matching the real exam pattern."
        with st.spinner(tr("pyq.preparing")):
            try:
                quiz, notes = build_pyq_quiz(exam, cfg, fresh_pool, fill_ai, plan)
            except Exception as e:
                st.error(friendly_error(e))
                return
        if not quiz:
            st.error(tr("pyq.none_found", notes=" ".join(notes)))
            return
        if len(quiz) < plan_n:
            notes.append(tr("pyq.got_fewer", got=len(quiz), plan=plan_n))
        if not use_pattern:
            random.shuffle(quiz)
        minutes = max(5, round(conf["minutes"] * len(quiz) / full_total)) if (use_pattern and conf and full_total) else 0
        meta = base_meta(
            cfg, f"{label_exam} · {'Mock' if use_pattern else 'PYQ'}", src_main, None,
            types=sorted({t for _, t, _ in plan}), adaptive=False, exam=label_exam, pyq_pool=pool, pyq_fill_ai=fill_ai, tkey=tkey,
            mode="Exam" if use_pattern else cfg["mode"], marks=marks_used, neg=neg_used, no_neg_types=no_neg,
            time_limit=0 if use_pattern else cfg["time_limit"], quiz_limit=minutes * 60 if use_pattern else cfg["quiz_limit"],
            gen_note=" ".join(notes),
        )
        start_quiz(quiz, meta)
        st.rerun()



DEPTH_RULES = {
    "Step-by-step": "Give a clear step-by-step solution, then a short concept explanation.",
    "Quick answer": "Give the final answer first in 1-2 lines, then a brief reason (max 5 lines).",
    "ELI5": "Explain like I am 12: very simple words, one everyday analogy, no jargon.",
    "Exam-ready notes": "Give crisp exam-ready notes: definition, key formulae/points, one example, common mistakes.",
}
LANG_RULES = {
    "Simple English": "very simple, clear English",
    "Hinglish": "Hinglish (Hindi written in Roman script, mixed with common English words)",
    "Hindi": "Hindi in Devanagari script",
}
REMEMBER_LABEL = {"Simple English": "Remember:", "Hinglish": "Yaad rakho:", "Hindi": "याद रखें:"}


def doubt_system_prompt(lang, depth):
    return (
        f"You are a patient, friendly tutor. Answer in {LANG_RULES.get(lang, 'very simple, clear English')}. {DEPTH_RULES[depth]} "
        "Use Markdown and short sentences; show calculations clearly. If the question is ambiguous or the photo is unreadable, "
        f"say so and state your assumption. End with '**{REMEMBER_LABEL.get(lang, 'Remember:')}**' and 2-3 bullets."
    )


def doubt_llm_messages(thread, system_prompt, with_image):
    msgs = [{"role": "system", "content": system_prompt}]
    for n, t in enumerate(thread):
        if n == 0 and t["role"] == "user" and t.get("image"):
            if with_image:
                b64 = base64.b64encode(t["image"]["bytes"]).decode()
                msgs.append(
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": t["content"] or "Solve and explain this question."},
                            {"type": "image_url", "image_url": {"url": f"data:{t['image']['mime']};base64,{b64}"}},
                        ],
                    }
                )
            else:
                msgs.append({"role": "user", "content": (t["content"] or "Question from a photo") + " (the photo was shared earlier; see the solution below)"})
        else:
            msgs.append({"role": t["role"], "content": t["content"]})
    return msgs


def render_doubt_tab(cfg):
    ss = st.session_state
    st.markdown(tr("doubt.title"))
    st.caption(tr("doubt.intro"))
    thread = ss.doubt_thread

    if not thread:
        with st.container(key="panel_doubt"):
            c1, c2 = st.columns(2)
            lang_opts = list(LANG_RULES.keys())
            d_lang = c1.selectbox(tr("doubt.lang"), lang_opts, key="d_lang", format_func=i18n.fmt("dlang"))
            d_depth = c2.selectbox(tr("doubt.style"), list(DEPTH_RULES.keys()), key="d_depth", format_func=i18n.fmt("depth"))
            src = st.radio(tr("doubt.how"), ["text", "camera", "photo", "pdf"], format_func=i18n.fmt("dsrc"), horizontal=True, key="d_src")
            q_text, d_media = "", None

            if src == "text":
                q_text = st.text_area(tr("doubt.txt"), height=140, placeholder=tr("doubt.txt_ph"), key="d_txt")
            elif src in ("camera", "photo"):
                if src == "camera":
                    st.caption(tr("doubt.cam_cap"))
                    d_file = st.camera_input(tr("doubt.cam"), key="d_cam")
                else:
                    d_file = st.file_uploader(tr("doubt.photo"), type=["png", "jpg", "jpeg", "webp"], key="d_img")
                if d_file is not None:
                    raw = d_file.getvalue()
                    if len(raw) > MAX_RAW_IMG_BYTES:
                        st.error(tr("err.photo_big"))
                    else:
                        data, mime = prepare_image(raw, getattr(d_file, "type", None) or "image/jpeg")
                        if len(data) > MAX_IMG_BYTES:
                            st.error(tr("err.photo_big2"))
                        else:
                            st.image(data, caption=tr("doubt.q_photo"), use_container_width=True)
                            d_media = {"bytes": data, "mime": mime}
                q_text = st.text_input(tr("doubt.extra"), placeholder=tr("doubt.extra_ph"), key="d_img_txt")
            else:
                d_pdf = st.file_uploader(tr("doubt.pdf"), type=["pdf"], key="d_pdf")
                extra = st.text_input(tr("doubt.pdf_q"), placeholder=tr("doubt.pdf_q_ph"), key="d_pdf_txt")
                if d_pdf is not None:
                    try:
                        pdf_text, _ = read_pdf(d_pdf, 1, 5)
                        if pdf_text.strip():
                            st.success(tr("doubt.pdf_loaded"))
                            q_text = f"Document text:\n{pdf_text[:MAX_CHARS]}\n\nRequest: {extra or 'Explain the key ideas simply.'}"
                        else:
                            st.error(tr("doubt.pdf_empty"))
                    except Exception as e:
                        st.error(tr("doubt.pdf_err", e=e))

        st.write("")
        if st.button(tr("doubt.explain"), type="primary", use_container_width=True, key="btn_solve_doubt"):
            if not q_text.strip() and not d_media:
                st.warning(tr("doubt.need"))
            else:
                ss.doubt_thread = [{"role": "user", "content": q_text.strip(), "image": d_media}]
                ss.doubt_opts = {"lang": d_lang, "depth": d_depth}
                ss.doubt_pending = True
                st.rerun()
        return

    for t in thread:
        with st.chat_message(t["role"]):
            if t.get("image"):
                st.image(t["image"]["bytes"], width=280)
            st.markdown(t["content"] or tr("doubt.photo_doubt"))

    opts = ss.doubt_opts or {"lang": "Simple English", "depth": "Step-by-step"}
    if ss.doubt_pending:
        use_vision = len(thread) == 1 and bool(thread[0].get("image"))
        msgs = doubt_llm_messages(thread, doubt_system_prompt(opts["lang"], opts["depth"]), use_vision)
        with st.chat_message("assistant"):
            try:
                text = st.write_stream(llm_stream(msgs, VISION_MODEL if use_vision else cfg["model"]))
                text = "".join(text) if isinstance(text, list) else str(text)
                if text.strip():
                    thread.append({"role": "assistant", "content": text})
            except Exception as e:
                st.error(friendly_error(e))
        ss.doubt_pending = False

    if thread and thread[-1]["role"] == "user":
        if st.button(tr("doubt.retry"), key="d_retry"):
            ss.doubt_pending = True
            st.rerun()

    with st.form("doubt_follow", clear_on_submit=True):
        fu = st.text_input(tr("doubt.follow"), placeholder=tr("doubt.follow_ph"), key="d_follow_txt")
        sent = st.form_submit_button(tr("doubt.send"))
    if sent and fu.strip():
        thread.append({"role": "user", "content": fu.strip()})
        ss.doubt_pending = True
        st.rerun()

    a1, a2, a3 = st.columns(3)
    if a1.button(tr("doubt.new"), use_container_width=True, key="d_new"):
        ss.doubt_thread = []
        ss.doubt_pending = False
        st.rerun()
    can_quiz = any(t["role"] == "assistant" for t in thread)
    if a2.button(tr("doubt.make_quiz"), use_container_width=True, disabled=not can_quiz, key="d_quiz"):
        transcript = "\n\n".join(t["content"] for t in thread if t["content"])[-MAX_CHARS:]
        launch_quiz(transcript, "Doubt: " + (thread[0]["content"] or "photo")[:40], cfg)
    md = "\n\n".join(f"**{tr('doubt.you') if t['role'] == 'user' else tr('doubt.ai')}:** {t['content']}" for t in thread if t["content"])
    a3.download_button(tr("doubt.notes_dl"), md.encode("utf-8"), file_name="doubt_notes.md", mime="text/markdown", use_container_width=True, key="d_dl")


# ═════════════════════════════════════════════════════════════
# STAGE · SETUP
# ═════════════════════════════════════════════════════════════
if st.session_state.stage == "setup":
    if st.session_state.get("tutor_on", True):
        avatar3d.render("idle", say=tr("av.hello"), height=230, char=st.session_state.get('tutor_char', 'girl'))
    hist = st.session_state.history
    best_pct = max(h["pct"] for h in hist) if hist else 0
    _ico = {
        "lvl": "<circle cx='12' cy='8' r='6'/><path d='M15.5 12.9 17 22l-5-3-5 3 1.5-9.1'/>",
        "xp": "<path d='M13 2 3 14h9l-1 8 10-12h-9l1-8z'/>",
        "played": "<circle cx='12' cy='12' r='10'/><circle cx='12' cy='12' r='6'/><circle cx='12' cy='12' r='2'/>",
        "best": "<path d='M6 9H4.5a2.5 2.5 0 0 1 0-5H6'/><path d='M18 9h1.5a2.5 2.5 0 0 0 0-5H18'/><path d='M4 22h16'/><path d='M10 14.7V17c0 .6-.5 1-1 1.2C7.9 18.8 7 20.2 7 22'/><path d='M14 14.7V17c0 .6.5 1 1 1.2 1.1.6 2 2 2 3.8'/><path d='M18 2H6v7a6 6 0 0 0 12 0V2Z'/>",
    }
    _svg = lambda k: f"<svg viewBox='0 0 24 24'>{_ico[k]}</svg>"
    st.markdown(
        f"<div class='qf-kpis'>"
        f"<div class='qf-kpi k1'><div class='ic'>{_svg('lvl')}</div><div class='v'>{lvl}</div><div class='l'>{tr('tile.level')}</div><div class='bar'><i style='width:{_xp_into}%'></i></div></div>"
        f"<div class='qf-kpi k2'><div class='ic'>{_svg('xp')}</div><div class='v'>{st.session_state.total_xp}</div><div class='l'>{tr('tile.xp')}</div></div>"
        f"<div class='qf-kpi k3'><div class='ic'>{_svg('played')}</div><div class='v'>{len(hist)}</div><div class='l'>{tr('tile.played')}</div></div>"
        f"<div class='qf-kpi k4'><div class='ic'>{_svg('best')}</div><div class='v'>{best_pct}%</div><div class='l'>{tr('tile.best')}</div><div class='bar'><i style='width:{best_pct}%'></i></div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    cfg = {
        "num_questions": num_questions, "difficulty": difficulty, "adaptive": adaptive, "type_keys": type_keys,
        "language": language, "mode": mode, "time_limit": time_limit, "quiz_limit": quiz_limit,
        "marks": marks_correct, "neg": neg_frac, "model": model,
    }
    tab_quiz, tab_pyq, tab_doubt = st.tabs([tr("tab.quiz"), tr("tab.pyq"), tr("tab.doubt")])
    with tab_quiz:
        render_quiz_tab(cfg)
    with tab_pyq:
        render_pyq_tab(cfg)
    with tab_doubt:
        render_doubt_tab(cfg)

    # recent activity (last 3 quizzes) or a friendly empty state
    if hist:
        _rows = ""
        for h in reversed(hist[-3:]):
            try:
                p = int(h.get("pct", 0))
                _rows += (
                    f"<div class='qf-act {'g' if p >= 80 else 'm' if p >= 50 else 'b'}'><div class='pct'>{p}%</div>"
                    f"<div class='t'>{esc(topic_label(h['topic']))[:46]}</div>"
                    f"<div class='s'>{h['score']}/{h['total']} · {esc(i18n.fmt('diff')(h['difficulty']))} · {esc(i18n.localize_time(h['time']))}</div>"
                    f"<div class='w'><i style='width:{p}%'></i></div></div>"
                )
            except Exception:
                continue
        if _rows:
            st.markdown(f"<div class='qf-card'><div class='hd'>{tr('dash.recent')}</div>{_rows}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='qf-empty'><div class='ei'>✨</div><div>{tr('dash.empty')}</div></div>", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════
# STAGE · QUIZ
# ═════════════════════════════════════════════════════════════
elif st.session_state.stage == "quiz":
    ss = st.session_state
    quiz = ss.quiz
    total = len(quiz)
    i = ss.idx
    q = quiz[i]
    qid = ss.quiz_id
    qtype_now = q["type"]
    choice_type = qtype_now in ("mcq", "tf", "multi")
    mode_now = ss.meta.get("mode", "Practice")
    survival = mode_now == "Survival"
    instant = mode_now in ("Practice", "Survival")
    limit = ss.meta.get("time_limit", 0)
    quiz_limit = ss.meta.get("quiz_limit", 0)
    is_adaptive = ss.meta.get("adaptive", False)
    mdl = ss.meta.get("model", MODELS[0])

    if ss.q_key != (qid, i):
        ss.q_key = (qid, i)
        ss.q_start = time.time()

    answered = sum(1 for a in ss.answers.values() if a not in (None, "", []))
    top_l, top_r = st.columns([4, 1.4])
    top_l.progress(i / total, text=tr("qz.q_of", i=i + 1, n=total))
    if survival:
        left = lives_left()
        top_r.markdown(f"<div class='qf-hearts'>{'❤️' * left}{'🖤' * (LIVES - left)}</div>", unsafe_allow_html=True)
    else:
        running = f"🎯 {fmt_marks(sum(question_marks(j) for j in ss.locked))} · " if instant else ""
        top_r.markdown(f"<div style='text-align:right;font-weight:700'>{running}✅ {answered}/{total}</div>", unsafe_allow_html=True)

    if ss.meta.get("gen_note") and i == 0:
        st.warning(ss.meta["gen_note"])
    locked = ss.locked.get(i, False)
    if limit and countdown is not None and not locked:
        countdown(limit, qid, i, total, instant)
    if quiz_limit and quiz_countdown is not None:
        quiz_countdown(quiz_limit, qid, i)

    if ss.get("tutor_on", True):
        if locked and instant:
            _ok = is_correct(i)
            _mood, _say = ("correct", tr("av.correct")) if _ok else ("wrong", tr("av.timeup") if ss.timed_out.get(i) else tr("av.wrong"))
        else:
            _mood, _say = "think", tr("av.think")
        avatar3d.render(_mood, say=_say, height=230, char=st.session_state.get('tutor_char', 'girl'), nonce=f"{qid}-{i}-{int(bool(locked))}")

    type_label = tr(f"qtype.{qtype_now}")
    lv_tag = f"<span class='qf-tag lv'>🎚️ {esc(i18n.fmt('diff')(LEVEL_NAME[q['level']]))}</span>" if is_adaptive else ""
    src_tag = f"<span class='qf-tag lv'>📜 {esc(q['src'])}</span>" if q.get("src") else ""
    _m, _pen = ss.meta.get("marks", 1.0), ss.meta.get("marks", 1.0) * ss.meta.get("neg", 0.0)
    mk_tag = f"<span class='qf-tag'>+{fmt_marks(_m)}" + (f" / −{fmt_marks(_pen)}" if _pen and qtype_now != "short" and qtype_now not in ss.meta.get("no_neg_types", []) else "") + "</span>"
    st.markdown(
        f"""<div class="qf-qcard"><div class="qf-tags">{src_tag}{lv_tag}{mk_tag}<span class='qf-tag'>{type_label}</span><span class='qf-tag'>{esc(q['topic'])}</span></div>
        <div class="qf-qnum">{tr('qz.qnum', i=i + 1)}</div>
        <div class="qf-qtext">{esc(q['question'])}</div></div>""",
        unsafe_allow_html=True,
    )

    h1, h2, h3, _sp = st.columns([1.35, 1.0, 1.35, 0.4])
    if q.get("hint") and not locked and not ss.hints_used.get(i):
        if h1.button(tr("qz.hint"), key=f"hint_{qid}_{i}", use_container_width=True):
            ss.hints_used[i] = True
            st.rerun()
    is_saved = q["question"] in ss.bookmarks
    if h2.button(tr("qz.saved") if is_saved else tr("qz.save"), key=f"bm_{qid}_{i}", use_container_width=True):
        toggle_bookmark(q)
        st.rerun()
    with h3:
        speak_button(speech_text(q))
    if ss.hints_used.get(i) and q.get("hint"):
        st.markdown(f"<div class='qf-hint'>💡 {esc(q['hint'])}</div>", unsafe_allow_html=True)

    prev = ss.answers.get(i)
    with st.container(key="optbox"):
        choice = answer_widget(q, qid, i, locked, prev)

    if choice_type and not locked:
        extra = tr("qz.kbd_skip") if instant else ""
        st.markdown(f"<div class='qf-kbd'>{tr('qz.kbd', n=len(q['options']), extra=extra)}</div>", unsafe_allow_html=True)

    game_over = survival and locked and lives_left() <= 0

    if instant and locked:
        st.markdown(feedback_html(i, q, ss.timed_out.get(i)), unsafe_allow_html=True)
        if game_over:
            st.error(tr("qz.game_over"))
        if st.button(tr("qz.explain"), key=f"deep_{qid}_{i}"):
            with st.spinner(tr("qz.processing")):
                try:
                    explain_more(q, user_text(i), i18n.ai_lang(), mdl)
                except Exception as e:
                    st.error(friendly_error(e))
        if deep_key(q) in ss.deep:
            st.info(ss.deep[deep_key(q)])

    st.write("")
    if not instant and not limit and not is_adaptive and total > 1:
        with st.expander(tr("qz.palette")):
            st.caption(tr("qz.palette_cap"))
            per_row = 8
            for r0 in range(0, total, per_row):
                pal_cols = st.columns(per_row)
                for k, pc in enumerate(pal_cols):
                    j = r0 + k
                    if j >= total:
                        break
                    done_j = ss.answers.get(j) not in (None, "", [])
                    if pc.button(f"{'✅' if done_j else ''}{j + 1}", key=f"pal_{qid}_{j}", type="primary" if j == i else "secondary", use_container_width=True):
                        ss.answers[i] = norm_answer(choice)
                        ss.idx = j
                        st.rerun()

    b1, b2, b3 = st.columns(3)
    last = i == total - 1

    if not instant and not limit and not is_adaptive and i > 0:
        if b1.button(tr("qz.back"), use_container_width=True):
            ss.answers[i] = norm_answer(choice)
            ss.idx -= 1
            st.rerun()

    if instant and not locked:
        if b2.button(tr("qz.check"), type="primary", use_container_width=True, disabled=(choice_type and not has_answer(choice))):
            ss.answers[i] = norm_answer(choice)
            if qtype_now == "short":
                with st.spinner(tr("qz.checking")):
                    grade_short(i)
            ss.locked[i] = True
            record_time(i)
            queue_sound("correct" if is_correct(i) else "wrong")
            st.rerun()
        if b3.button(tr("qz.skip"), use_container_width=True):
            ss.answers[i] = None
            ss.locked[i] = True
            record_time(i)
            queue_sound("wrong")
            if last:
                finish_quiz()
            else:
                advance(i)
            st.rerun()
    else:
        btn_label = tr("qz.view_results") if game_over else (tr("qz.finish") if last else tr("qz.next"))

        if b3.button(btn_label, type="primary", use_container_width=True):
            if not instant:
                ss.answers[i] = norm_answer(choice)
                record_time(i)
            if last or game_over:
                finish_quiz()
            else:
                advance(i)
            st.rerun()

    st.write("")
    if st.button(tr("qz.leave")):
        reset_all()
        st.rerun()

# ═════════════════════════════════════════════════════════════
# STAGE · FLASHCARDS
# ═════════════════════════════════════════════════════════════
elif st.session_state.stage == "flash":
    ss = st.session_state
    cards = ss.flash_cards
    fi = ss.flash_i
    card = cards[fi]
    st.markdown(tr("flash.title"))
    st.progress((fi + 1) / len(cards), text=tr("flash.card", i=fi + 1, n=len(cards)))

    if ss.flash_show:
        st.markdown(
            f"<div class='qf-flash back'><div>✅ {esc(disp(card, correct_text(card)))}"
            f"<div style='font-family:Plus Jakarta Sans;font-size:.95rem;font-weight:400;color:var(--mute);margin-top:10px'>{esc(explanation_text(card))}</div></div></div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"<div class='qf-flash'>{esc(card['question'])}</div>", unsafe_allow_html=True)

    f1, f2, f3 = st.columns(3)
    if f1.button(tr("flash.prev"), use_container_width=True, disabled=fi == 0):
        ss.flash_i -= 1
        ss.flash_show = False
        st.rerun()
    if f2.button(tr("flash.show_ans") if not ss.flash_show else tr("flash.show_q"), type="primary", use_container_width=True):
        ss.flash_show = not ss.flash_show
        st.rerun()
    if f3.button(tr("flash.next"), use_container_width=True, disabled=fi == len(cards) - 1):
        ss.flash_i += 1
        ss.flash_show = False
        st.rerun()

    st.write("")
    if st.button(tr("flash.back")):
        ss.stage = "result" if (ss.flash_return == "result" and ss.result) else "setup"
        st.rerun()

# ═════════════════════════════════════════════════════════════
# STAGE · RESULT
# ═════════════════════════════════════════════════════════════
else:
    ss = st.session_state
    quiz, answers, res = ss.quiz, ss.answers, ss.result
    total = len(quiz)
    mdl = ss.meta.get("model", MODELS[0])

    correct_idx = [i for i in range(total) if is_correct(i)]
    skipped_idx = [i for i in range(total) if is_skipped(i)]
    wrong_idx = [i for i in range(total) if i not in correct_idx and i not in skipped_idx]
    pct, score = res["pct"], res["score"]
    elapsed = ss.elapsed_before + (ss.end_time or time.time()) - (ss.start_time or time.time())

    if pct >= 80:
        color, title, msg = "#34D399", tr("res.great"), tr("res.great_msg")
    elif pct >= 50:
        color, title, msg = "#FFC857", tr("res.good"), tr("res.good_msg")
    else:
        color, title, msg = "#FB7185", tr("res.keep"), tr("res.keep_msg")

    if not ss.celebrated:
        if pct >= 80:
            st.balloons()
        ss.celebrated = True

    st.markdown(f"## {title}")
    st.caption(msg)
    if ss.get("tutor_on", True):
        _rm, _rs = ("correct", tr("av.great")) if pct >= 80 else (("idle", tr("av.good")) if pct >= 50 else ("wrong", tr("av.keep")))
        avatar3d.render(_rm, say=_rs, height=240, char=st.session_state.get('tutor_char', 'girl'), nonce=f"res-{ss.quiz_id}")
    _m = ss.meta.get("marks", 1.0)
    st.caption(
        tr("res.marking", m=fmt_marks(_m), p=fmt_marks(_m * ss.meta.get("neg", 0.0)), nn=tr("res.no_neg_num") if ss.meta.get("no_neg_types") else "")
    )
    if res.get("time_up"):
        st.warning(tr("res.time_up"))
    _sec = tr("unit.sec")
    st.markdown(
        f"""
<div class="qf-ring" style="--t:{pct};--ring-color:{color}">
  <div class="qf-ring-in"><div class="big">{pct}%</div><div class="sm">{tr('res.marks_of', a=fmt_marks(res['marks']), b=fmt_marks(res['max_marks']))}</div></div>
</div>
<div class="qf-tiles">
  <div class="qf-tile"><div class="v" style="color:#FFC857">{fmt_marks(res['marks'])}<span style="font-size:.9rem;opacity:.7"> / {fmt_marks(res['max_marks'])}</span></div><div class="l">{tr('res.marks')}</div></div>
  <div class="qf-tile"><div class="v" style="color:#22D3EE">{res['accuracy']}%</div><div class="l">{tr('res.accuracy')}</div></div>
  <div class="qf-tile"><div class="v">{res['attempted']}<span style="font-size:.9rem;opacity:.7"> / {total}</span></div><div class="l">{tr('res.attempted')}</div></div>
  <div class="qf-tile"><div class="v" style="color:#FB7185">−{fmt_marks(res['neg_lost'])}</div><div class="l">{tr('res.neg_marks')}</div></div>
</div>
<div class="qf-tiles">
  <div class="qf-tile"><div class="v" style="color:#34D399">{score}</div><div class="l">{tr('res.correct')}</div></div>
  <div class="qf-tile"><div class="v" style="color:#FB7185">{len(wrong_idx)}</div><div class="l">{tr('res.wrong')}</div></div>
  <div class="qf-tile"><div class="v">{len(skipped_idx)}</div><div class="l">{tr('res.skipped')}</div></div>
  <div class="qf-tile"><div class="v">{fmt_time(elapsed)}</div><div class="l">{tr('res.total_time')}</div></div>
  <div class="qf-tile"><div class="v" style="color:#FFC857">+{res['xp']}</div><div class="l">{tr('res.xp')}</div></div>
  <div class="qf-tile"><div class="v">{res['best_streak']}🔥</div><div class="l">{tr('res.best_streak')}</div></div>
  <div class="qf-tile"><div class="v">{res['avg_time']:.1f}{_sec}</div><div class="l">{tr('res.avg_q')}</div></div>
  <div class="qf-tile"><div class="v">{res['hints']}</div><div class="l">{tr('res.hints')}</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    if res["leveled_up"]:
        st.success(tr("res.level_up", n=level_of(ss.total_xp)))
    if res["badges"]:
        st.markdown(
            "<div class='qf-badges'>" + "".join(f"<span class='qf-badge'>{esc(tr('badge.' + b))}</span>" for b in res["badges"]) + "</div>",
            unsafe_allow_html=True,
        )

    with st.container(key="morebox"):
        game_over_now = ss.meta.get("mode") == "Survival" and lives_left() <= 0
        st.markdown(tr("res.more_title", n=total))
        mc1, mc2 = st.columns([1, 2])
        more_n = int(mc1.number_input(tr("res.more_n"), 1, 50, 10, 1, key="more_n", label_visibility="collapsed"))
        can_more = (not game_over_now) and total + more_n <= MAX_TOTAL_Q
        if mc2.button(tr("res.more_btn", n=more_n), type="primary", use_container_width=True, disabled=not can_more):
            with st.spinner(tr("res.more_spin")):
                try:
                    if extend_quiz(more_n):
                        st.rerun()
                    else:
                        st.error(tr("res.more_fail"))
                except Exception as e:
                    st.error(friendly_error(e))
        note = tr("res.more_note")
        if game_over_now:
            note = tr("res.more_note_over")
        elif total + more_n > MAX_TOTAL_Q:
            note = tr("res.more_note_max", n=MAX_TOTAL_Q)
        st.caption(note)
    st.write("")

    a1, a2 = st.columns(2)
    if a1.button(tr("res.new_quiz"), use_container_width=True, type="primary"):
        reset_all()
        st.rerun()
    if a2.button(tr("res.redo_wrong"), use_container_width=True, disabled=not (wrong_idx or skipped_idx), help=tr("res.redo_help")):
        redo = [reshuffle(quiz[i]) for i in wrong_idx + skipped_idx]
        meta = dict(ss.meta)
        meta["label"] = "Retry · " + meta.get("label", "Quiz")
        start_quiz(redo, meta)
        st.rerun()

    a3, a4 = st.columns(2)
    if a3.button(tr("res.same_again"), use_container_width=True):
        start_quiz([reshuffle(q) for q in quiz], dict(ss.meta))
        st.rerun()
    if a4.button(tr("res.new_qs"), use_container_width=True):
        m = ss.meta
        with st.spinner(tr("res.more_spin")):
            try:
                new_quiz = more_questions(len(quiz), [q["question"] for q in quiz])
                if new_quiz:
                    start_quiz(new_quiz, dict(m))
                    st.rerun()
                else:
                    st.error(tr("res.new_qs_fail"))
            except Exception as e:
                st.error(friendly_error(e))

    if st.button(tr("res.flash"), use_container_width=True):
        ss.flash_cards = [dict(q) for q in quiz]
        ss.flash_i, ss.flash_show, ss.flash_return = 0, False, "result"
        ss.stage = "flash"
        st.rerun()

    st.markdown(tr("res.topic_perf"))
    topic_df = pd.DataFrame([{"Topic": q["topic"], "Correct": int(is_correct(i))} for i, q in enumerate(quiz)])
    agg = topic_df.groupby("Topic")["Correct"].agg(["sum", "count"]).reset_index()
    agg["Accuracy %"] = (agg["sum"] / agg["count"] * 100).round(0)
    if len(agg) > 1:
        _chart = agg.set_index("Topic")["Accuracy %"].rename(tr("res.col_acc"))
        _chart.index.name = tr("res.col_topic")
        st.bar_chart(_chart)
    weak = agg[agg["Accuracy %"] < 60]["Topic"].tolist()
    strong = agg[agg["Accuracy %"] >= 80]["Topic"].tolist()
    if strong:
        st.success(tr("res.strong", l=", ".join(strong)))
    if weak:
        st.warning(tr("res.weak", l=", ".join(weak)))

    if wrong_idx or skipped_idx:
        if st.button(tr("res.plan_btn"), use_container_width=True):
            with st.spinner(tr("res.plan_spin")):
                try:
                    ss.study_plan = make_study_plan([quiz[i] for i in wrong_idx + skipped_idx], i18n.ai_lang(), mdl)
                except Exception as e:
                    st.error(friendly_error(e))
        if ss.study_plan:
            st.markdown(ss.study_plan)

    st.markdown(tr("res.review"))
    for i, q in enumerate(quiz):
        icon = "✅" if is_correct(i) else ("⏭️" if is_skipped(i) else "❌")
        with st.expander(f"{icon}  Q{i + 1}. {q['question'][:90]}"):
            st.markdown(f"**{q['question']}**")
            sel = answers.get(i)
            if q["type"] in ("mcq", "tf"):
                for o in q["options"]:
                    if o == q["answer"]:
                        st.markdown(f"- ✅ **{disp(q, o)}**")
                    elif o == sel:
                        st.markdown(f"- ❌ ~~{disp(q, o)}~~{tr('res.your_tag')}")
                    else:
                        st.markdown(f"- {disp(q, o)}")
            elif q["type"] == "multi":
                chosen = set(sel or [])
                for o in q["options"]:
                    right = o in q["answers"]
                    if right and o in chosen:
                        st.markdown(f"- ✅ **{o}**")
                    elif right:
                        st.markdown(f"- ✅ **{o}**{tr('res.missed')}")
                    elif o in chosen:
                        st.markdown(f"- ❌ ~~{o}~~{tr('res.wrong_pick')}")
                    else:
                        st.markdown(f"- {o}")
            else:
                st.markdown(tr("res.your_answer", a=user_text(i)))
                st.markdown(tr("res.correct_answer", a=q["answer"]))
                if q["type"] == "short" and i in ss.grades:
                    g = ss.grades[i]
                    st.markdown(tr("res.ai_score", s=g["score"], f=grade_feedback(g)))
            if is_skipped(i):
                st.caption(tr("res.skipped_note"))
            _mk = question_marks(i)
            st.caption(tr("res.marks_line", m=f"{'+' if _mk > 0 else ''}{fmt_marks(_mk)}"))
            st.info(f"💡 {explanation_text(q)}")
            c1, c2 = st.columns(2)
            if c1.button(tr("qz.explain"), key=f"rv_deep_{ss.quiz_id}_{i}"):
                with st.spinner(tr("doubt.thinking")):
                    try:
                        explain_more(q, user_text(i), i18n.ai_lang(), mdl)
                    except Exception as e:
                        st.error(friendly_error(e))
            saved = q["question"] in ss.bookmarks
            if c2.button(tr("qz.saved") if saved else tr("qz.save"), key=f"rv_bm_{ss.quiz_id}_{i}"):
                toggle_bookmark(q)
                st.rerun()
            if deep_key(q) in ss.deep:
                st.markdown(ss.deep[deep_key(q)])

    st.markdown(tr("res.download"))
    df = pd.DataFrame(
        [
            {
                tr("csv.no"): i + 1,
                tr("csv.type"): q["type"],
                tr("csv.topic"): q["topic"],
                tr("csv.question"): q["question"],
                tr("csv.options"): " | ".join(q["options"]),
                tr("csv.your"): user_text(i),
                tr("csv.correct"): correct_text(q),
                tr("csv.result"): tr("csv.r_ok") if is_correct(i) else tr("csv.r_bad"),
                tr("csv.marks"): question_marks(i),
                tr("csv.expl"): explanation_text(q),
            }
            for i, q in enumerate(quiz)
        ]
    )
    d1, d2, d3 = st.columns(3)
    d1.download_button(tr("res.dl_html"), build_report_html().encode("utf-8"), file_name="quiz_report.html", mime="text/html", use_container_width=True)
    d2.download_button(tr("res.dl_csv"), df.to_csv(index=False).encode("utf-8-sig"), file_name="quiz_results.csv", mime="text/csv", use_container_width=True)
    d3.download_button(tr("res.dl_json"), json.dumps(quiz, ensure_ascii=False, indent=2).encode("utf-8"), file_name="quiz.json", mime="application/json", use_container_width=True)

# ─────────────────────────────────────────────────────────────
# Browser layer (sound / voice / shortcuts)
# ─────────────────────────────────────────────────────────────
_run_lang = st.session_state.meta.get("language", language) if st.session_state.stage == "quiz" else language
render_browser_layer(
    sound_on=sound_on,
    tts_lang="hi-IN" if _run_lang == "Hindi" else "en-IN",
    tts_rate=tts_rate,
    auto_read=auto_read,
)
