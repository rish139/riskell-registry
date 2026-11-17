#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Rishabh Tiwari
"""index.json -> site/index.html: the storefront, one static page (search, tabs, a picture of every widget, a detail view, a copy-able install
command) plus site/previews/<id>.png and site/index.json. No server, no accounts.

    scripts/build-site.py                      the real registry (site/)
    scripts/build-site.py --sample             a preview with made-up sample listings and a banner (site-preview/)
    --repo riskell=/path/to/checkout           resolve previews of listings from that repository name locally (default: ../riskell-public when present);
                                               otherwise a listing's repository is cloned at its pinned commit
"""
import json, os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE = "--sample" in sys.argv
OUT = os.path.join(ROOT, "site-preview" if SAMPLE else "site")
local = {}
if os.path.isdir(os.path.join(ROOT, "..", "riskell-public")): local["riskell"] = os.path.abspath(os.path.join(ROOT, "..", "riskell-public"))
for i, a in enumerate(sys.argv):
    if a == "--repo" and i + 1 < len(sys.argv) and "=" in sys.argv[i + 1]:
        k, v = sys.argv[i + 1].split("=", 1); local[k] = os.path.abspath(v)

idx = json.load(open(os.path.join(ROOT, "index.json")))
items = idx["listings"]
if SAMPLE:
    for s in json.load(open(os.path.join(ROOT, "preview", "sample-listings.json"))): s["preview"] = "@sample/" + s["id"] + ".png"; items.append(s)
shutil.rmtree(OUT, ignore_errors=True); os.makedirs(os.path.join(OUT, "previews"))

clones = {}
def preview_file(l):
    p = l.get("preview")
    if not p: return None
    if p.startswith("@sample/"): f = os.path.join(ROOT, "preview", "samples", p[8:]); return f if os.path.exists(f) else None
    name = l["repo"].rstrip("/").split("/")[-1].removesuffix(".git")
    base = local.get(name)
    if base and os.path.exists(os.path.join(base, p)): return os.path.join(base, p)
    if l["repo"] not in clones:
        d = tempfile.mkdtemp(prefix="registry-site-")
        env = dict(os.environ, GIT_ALLOW_PROTOCOL="https", GIT_TERMINAL_PROMPT="0"); g = ["git", "-c", "protocol.ext.allow=never", "-c", "core.hooksPath=/dev/null"]
        ok = l["repo"].startswith("https://") and l["rev"].isalnum() and subprocess.run(g + ["clone", "--quiet", "--", l["repo"], d], capture_output=True, env=env).returncode == 0 and subprocess.run(g + ["checkout", "--quiet", l["rev"]], cwd=d, capture_output=True, env=env).returncode == 0
        clones[l["repo"]] = d if ok else None
    d = clones[l["repo"]]
    return os.path.join(d, p) if d and os.path.exists(os.path.join(d, p)) else None

for l in items:
    f = preview_file(l)
    if f: shutil.copy(f, os.path.join(OUT, "previews", l["id"] + ".png")); l["shot"] = "previews/%s.png" % l["id"]
    l.pop("preview", None)
for d in clones.values():
    if d: shutil.rmtree(d, ignore_errors=True)
shutil.copy(os.path.join(ROOT, "index.json"), os.path.join(OUT, "index.json"))
data = json.dumps(items).replace("</", "<\\/")

page = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>riskell extensions</title>
<style>
:root{--bg:#f6f5f1;--s1:#fff;--s2:#efede6;--line:#e2dfd5;--t1:#1d1f20;--t2:#5a6064;--t3:#868c90;--accent:#b7791f;--on:#fff;--ok:#4d7c0f;--shadow:0 1px 2px rgba(0,0,0,.06),0 8px 24px rgba(0,0,0,.06)}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){--bg:#0f1112;--s1:#16191b;--s2:#1d2124;--line:#262b2e;--t1:#ececea;--t2:#a2a8ab;--t3:#70777b;--accent:#f2b84b;--on:#1a1405;--ok:#9ccc4a;--shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px rgba(0,0,0,.35)}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--t1);font:15px/1.55 -apple-system,BlinkMacSystemFont,"SF Pro Text",system-ui,sans-serif;-webkit-font-smoothing:antialiased}
code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
a{color:inherit}
.top{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--bg) 82%,transparent);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border-bottom:1px solid var(--line)}
.top .in{max-width:1180px;margin:0 auto;padding:12px 20px;display:flex;gap:16px;align-items:center}
.brand{font-weight:700;letter-spacing:-.01em;font-size:17px;text-decoration:none;white-space:nowrap}.brand span{color:var(--t3);font-weight:500}
.search{flex:1;position:relative;max-width:520px;margin-left:auto}
.search input{width:100%;background:var(--s1);color:var(--t1);border:1px solid var(--line);border-radius:10px;padding:9px 12px 9px 34px;font:inherit}
.search svg{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--t3)}
.gh{color:var(--t2);text-decoration:none;font-size:14px}.gh:hover{color:var(--t1)}
main{max-width:1180px;margin:0 auto;padding:36px 20px 80px}
.hero h1{font-size:clamp(28px,4.4vw,44px);line-height:1.1;letter-spacing:-.02em;margin:0 0 10px;font-weight:750}
.hero p{margin:0;color:var(--t2);max-width:60ch;font-size:17px}
.banner{background:var(--accent);color:var(--on);border-radius:10px;padding:8px 14px;margin:0 0 22px;font-size:13px}
.tabs{display:flex;gap:6px;margin:28px 0 8px;flex-wrap:wrap}
.tab{background:none;border:1px solid transparent;color:var(--t2);padding:7px 14px;border-radius:999px;font:inherit;cursor:pointer}
.tab:hover{color:var(--t1)}.tab[aria-selected=true]{background:var(--s1);border-color:var(--line);color:var(--t1);box-shadow:var(--shadow)}
.tab small{color:var(--t3);margin-left:6px}
section{margin-top:34px}section h2{font-size:15px;letter-spacing:.01em;margin:0 0 14px;color:var(--t2);font-weight:600;display:flex;gap:10px;align-items:baseline}section h2 small{color:var(--t3);font-weight:500}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:18px}
.card{background:var(--s1);border:1px solid var(--line);border-radius:16px;overflow:hidden;cursor:pointer;display:flex;flex-direction:column;transition:transform .15s,box-shadow .15s,border-color .15s}
.card:hover,.card:focus-visible{transform:translateY(-2px);box-shadow:var(--shadow);border-color:color-mix(in srgb,var(--accent) 40%,var(--line));outline:none}
.shot{aspect-ratio:16/9;background:var(--s2);overflow:hidden;position:relative}.shot img{width:100%;height:100%;object-fit:cover;display:block}
.shot.ph{display:grid;place-items:center;color:var(--t3);font-size:38px;font-weight:700;background:linear-gradient(135deg,var(--s2),var(--bg))}
.body{padding:14px 16px 16px;display:flex;flex-direction:column;gap:6px;flex:1}
.row{display:flex;gap:8px;align-items:center;justify-content:space-between}
.body h3{margin:0;font-size:16px;letter-spacing:-.005em}
.kind{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--t3);border:1px solid var(--line);border-radius:6px;padding:1px 7px;white-space:nowrap}
.kind.ok{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 40%,var(--line))}
.body p{margin:0;color:var(--t2);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;min-height:3.1em}
.foot{display:flex;justify-content:space-between;align-items:center;margin-top:auto;padding-top:8px;color:var(--t3);font-size:12.5px;gap:8px}
.btn{background:var(--accent);color:var(--on);border:0;border-radius:9px;padding:6px 12px;font:inherit;font-weight:600;font-size:13px;cursor:pointer}
.btn.ghost{background:var(--s2);color:var(--t1)}
.btn:focus-visible,.tab:focus-visible,input:focus-visible,a:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.empty{color:var(--t3);padding:40px 0;text-align:center}
dialog{border:1px solid var(--line);background:var(--s1);color:var(--t1);border-radius:20px;padding:0;width:min(820px,calc(100vw - 24px));max-height:calc(100vh - 24px);box-shadow:0 30px 80px rgba(0,0,0,.45)}
dialog::backdrop{background:rgba(0,0,0,.55);backdrop-filter:blur(4px)}
.dshot{aspect-ratio:16/9;background:var(--s2)}.dshot img{width:100%;height:100%;object-fit:cover;display:block}
.dbody{padding:20px 24px 24px;display:grid;gap:16px}
.dbody h2{margin:0;font-size:24px;letter-spacing:-.015em;display:flex;gap:10px;align-items:center;flex-wrap:wrap}
.dbody p{margin:0;color:var(--t2);font-size:16px}
.cmd{display:flex;gap:8px;align-items:center;background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:8px 8px 8px 14px}.cmd code{flex:1;overflow-x:auto;white-space:nowrap}
dl{display:grid;grid-template-columns:max-content 1fr;gap:6px 18px;margin:0;font-size:14px}dt{color:var(--t3)}dd{margin:0;word-break:break-word}
.chips{display:flex;gap:6px;flex-wrap:wrap}.chips code{background:var(--s2);border-radius:6px;padding:1px 8px;font-size:12.5px}
.x{position:absolute;right:12px;top:12px;background:rgba(0,0,0,.5);color:#fff;border:0;border-radius:999px;width:34px;height:34px;font-size:18px;cursor:pointer}
.toast{position:fixed;left:50%;bottom:28px;transform:translateX(-50%) translateY(20px);background:var(--t1);color:var(--bg);padding:9px 16px;border-radius:10px;font-size:14px;opacity:0;pointer-events:none;transition:.2s;z-index:20}.toast.on{opacity:1;transform:translateX(-50%)}
footer{margin-top:60px;color:var(--t3);font-size:13px;border-top:1px solid var(--line);padding-top:20px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
</style></head><body>
<header class="top"><div class="in"><a class="brand" href="#">riskell <span>extensions</span></a>
<label class="search"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="7" cy="7" r="5"/><path d="m11 11 3.5 3.5"/></svg><input id="q" type="search" placeholder="Search widgets, pills and themes" aria-label="Search extensions"></label>
<a class="gh" href="https://github.com/rish139/riskell">GitHub</a></div></header>
<main>
__BANNER__
<div class="hero"><h1>Make your bar yours.</h1><p>Widgets, pills and themes for riskell, the native macOS shell. Each one is pinned to a single commit of its author's repository, and installs with one command.</p></div>
<div class="tabs" role="tablist" id="tabs"></div>
<div id="content"></div>
<footer>Install with <code>risk ext add &lt;name&gt;</code>. Listed something of your own? <code>risk ext publish</code> prints the listing; open a pull request on <a href="https://github.com/rish139/riskell-registry">riskell-registry</a>.</footer>
</main>
<dialog id="dlg" aria-label="Extension details"></dialog><div id="toast" class="toast" role="status"></div>
<script>
const L=__DATA__;
const $=s=>document.querySelector(s),esc=s=>String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const group=l=>l.kind==="theme"?"theme":l.kind==="pill"?"pill":l.kind==="preset"?"preset":"widget";
const NAMES={widget:"Widgets",pill:"Pills",theme:"Themes",preset:"Presets"},KIND={atom:"widget",reading:"widget",pill:"pill",theme:"theme",preset:"preset"};
let tab="all";
const count=g=>L.filter(l=>g==="all"||group(l)===g).length;
function tabs(){const gs=["all",...["widget","pill","theme","preset"].filter(g=>count(g))];
 $("#tabs").innerHTML=gs.map(g=>`<button class="tab" role="tab" data-t="${g}" aria-selected="${g===tab}">${g==="all"?"All":NAMES[g]}<small>${count(g)}</small></button>`).join("")}
$("#tabs").onclick=e=>{const b=e.target.closest(".tab");if(!b)return;tab=b.dataset.t;draw()};
function card(l){const shot=l.shot?`<div class="shot"><img loading="lazy" src="${esc(l.shot)}" alt="${esc(l.name)} on a riskell bar, and its hover card"></div>`:`<div class="shot ph" aria-hidden="true">${esc(l.name[0])}</div>`;
 return `<article class="card" tabindex="0" data-id="${esc(l.id)}">${shot}<div class="body"><div class="row"><h3>${esc(l.name)}</h3><span class="kind${l.bundled?" ok":""}">${l.bundled?"built in":esc(KIND[l.kind]||l.kind)}</span></div>
 <p>${esc(l.summary)}</p><div class="foot"><span>${l.authors?esc(l.authors[0])+" · ":""}v${esc(l.version)}</span><button class="btn" data-copy="${esc(l.id)}" aria-label="Copy the install command for ${esc(l.name)}">Install</button></div></div></article>`}
function section(t,list){return list.length?`<section><h2>${t}<small>${list.length}</small></h2><div class="grid">${list.map(card).join("")}</div></section>`:""}
function draw(){tabs();const q=$("#q").value.trim().toLowerCase();let r=L.filter(l=>tab==="all"||group(l)===tab);
 if(q){r=r.filter(l=>[l.id,l.name,l.summary,l.kind,...(l.keywords||[]),...(l.atoms||[]),...(l.authors||[])].join(" ").toLowerCase().includes(q));
  $("#content").innerHTML=r.length?section(`${r.length} result${r.length>1?"s":""}`,r):`<p class="empty">Nothing matches "${esc(q)}".</p>`;return}
 const by=(a,b)=>a.name.localeCompare(b.name);
 if(tab==="all"){const b=L.filter(l=>l.bundled);
  $("#content").innerHTML=section("Built in",b)+["widget","pill","theme","preset"].map(g=>section(NAMES[g],L.filter(l=>!l.bundled&&group(l)===g).sort(by))).join("")}
 else $("#content").innerHTML=section(NAMES[tab],r.sort((a,b)=>(b.bundled?1:0)-(a.bundled?1:0)||by(a,b)))}
function toast(t){const e=$("#toast");e.textContent=t;e.classList.add("on");clearTimeout(toast.t);toast.t=setTimeout(()=>e.classList.remove("on"),1600)}
function copy(id){const c="risk ext add "+id;(navigator.clipboard?navigator.clipboard.writeText(c):Promise.reject()).then(()=>toast("Copied: "+c),()=>toast(c))}
function open(id){const l=L.find(x=>x.id===id);if(!l)return;const d=$("#dlg");
 d.innerHTML=`<div style="position:relative">${l.shot?`<div class="dshot"><img src="${esc(l.shot)}" alt="${esc(l.name)} on a riskell bar, and its hover card"></div>`:""}<button class="x" aria-label="Close">×</button></div>
 <div class="dbody"><h2>${esc(l.name)} <span class="kind${l.bundled?" ok":""}">${l.bundled?"built in":esc(l.kind)}</span></h2><p>${esc(l.summary)}</p>
 ${l.bundled?`<p class="mono" style="font-size:14px;color:var(--t3)">Ships with riskell. <code>risk ext add ${esc(l.id)}</code> puts it back if you removed it.</p>`:`<div class="cmd"><code>risk ext add ${esc(l.id)}</code><button class="btn" data-copy="${esc(l.id)}">Copy</button></div>`}
 <dl><dt>Version</dt><dd>${esc(l.version)}</dd><dt>License</dt><dd>${esc(l.license)}</dd>${l.authors?`<dt>Authors</dt><dd>${esc(l.authors.join(", "))}</dd>`:""}${l.kit?`<dt>Needs</dt><dd>RiskellKit ${esc(l.kit)}</dd>`:""}
 ${(l.atoms||[]).length?`<dt>Adds</dt><dd class="chips">${l.atoms.map(a=>`<code>ext:${esc(a)}</code>`).join("")}</dd>`:""}
 <dt>Source</dt><dd><a href="${esc(l.repo)}">${esc(l.repo.replace("https://github.com/",""))}</a></dd><dt>Pinned to</dt><dd class="mono" style="font-size:12.5px">${esc(l.rev)}</dd></dl></div>`;
 d.showModal();history.replaceState(null,"","#"+id)}
$("#dlg").addEventListener("close",()=>history.replaceState(null,"",location.pathname+location.search));
$("#dlg").addEventListener("click",e=>{if(e.target.classList.contains("x")||e.target===$("#dlg"))$("#dlg").close()});
document.addEventListener("click",e=>{const b=e.target.closest("[data-copy]");if(b){e.stopPropagation();copy(b.dataset.copy);return}
 const c=e.target.closest(".card");if(c)open(c.dataset.id)});
document.addEventListener("keydown",e=>{if((e.key==="Enter"||e.key===" ")&&e.target.classList&&e.target.classList.contains("card")){e.preventDefault();open(e.target.dataset.id)}});
$("#q").oninput=draw;draw();if(location.hash.length>1)open(decodeURIComponent(location.hash.slice(1)));
</script></body></html>
"""
banner = '<div class="banner">Preview: the real listings plus made-up samples (github.com/example/...), to show what a populated storefront looks like. Not the registry.</div>' if SAMPLE else ""
open(os.path.join(OUT, "index.html"), "w").write(page.replace("__DATA__", data).replace("__BANNER__", banner))
print(f"{os.path.relpath(OUT, ROOT)}/index.html: {len(items)} listings, {sum(1 for l in items if l.get('shot'))} pictures")
