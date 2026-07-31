"""
Generate dashboard from output folders — auto labels, dark/light mode,
usage tracking (localStorage). One dashboard to rule them all.
"""

import argparse
import base64
import http.server
import json
import os
import socketserver
import webbrowser
from pathlib import Path


def _img_b64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _collect(output_dir):
    out = Path(output_dir)
    batches = []

    if out.is_dir():
        entries = sorted(out.iterdir())
        has_root = bool(list(out.glob("*.mp4")) or list(out.glob("*.png")) or list(out.glob("*.jpg")))
        if has_root:
            entries = [out]
        else:
            entries = [e for e in entries if e.is_dir() and (list(e.rglob("*.mp4")) or list(e.rglob("*.png")) or list(e.rglob("*.jpg")))]
    else:
        entries = []

    for entry in entries:
        # Use rglob so we pick up media in subdirs (photos/, videos/) too
        mp4s = sorted(entry.rglob("*.mp4"))
        pngs = sorted(entry.rglob("*.png"))
        jpgs = sorted(entry.rglob("*.jpg"))
        txts = {f.stem: f for f in entry.rglob("*.txt")}

        meta = {}
        meta_path = entry / "meta.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                meta = {}

        seen = set()
        items = []
        for path in mp4s + pngs + jpgs:
            stem = path.stem
            if stem in seen:
                continue
            seen.add(stem)
            txt = txts.get(stem)
            txt_content = txt.read_text(encoding="utf-8").strip() if txt else ""
            labels = meta.get(stem, {}).get("labels", "") if isinstance(meta.get(stem), dict) else ""
            items.append({
                "stem": stem,
                "path": str(path.resolve()),
                "is_video": path.suffix == ".mp4",
                "txt_content": txt_content,
                "filename": path.name,
                "labels": labels,
            })

        if items:
            batches.append({"name": entry.name, "items": items, "dir": str(entry.resolve())})

    return batches


def generate_dashboard(output_dir=None, all_flag=False, serve=False, port=8000):
    if all_flag and output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "outputs")
    if not output_dir:
        print("Specify --dir or use --all")
        return

    batches = _collect(output_dir)
    if not batches:
        print(f"No media found in {output_dir}")
        return

    total = sum(len(b["items"]) for b in batches)
    uid = os.path.basename(os.path.abspath(output_dir))

    sections = ""
    for bidx, batch in enumerate(batches):
        bid = batch['name'].replace(" ", "_")
        rows = ""
        for idx, r in enumerate(batch["items"], 1):
            vid = f"v-{bid}-{idx}"
            tid = f"t-{bid}-{idx}"
            mid = f"m-{bid}-{idx}"
            sid = f"s-{bid}-{idx}"

            rel = os.path.relpath(r["path"], output_dir)
            src = rel.replace("\\", "/")

            media_tag = (
                f'<video id="{vid}" muted loop playsinline preload="metadata">'
                f'<source src="{src}" type="video/mp4"></video>'
                if r["is_video"] else
                f'<img id="{vid}" src="{src}" loading="lazy">'
            )

            escaped_txt = r["txt_content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            txt_cell = (
                f'<div class="txt" id="{tid}" title="{escaped_txt}">{escaped_txt}</div>'
                if r["txt_content"] else '<span class="muted">—</span>'
            )
            cpy_svg = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'
            dl_svg = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>'
            check_svg = '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>'
            cpy = (
                f'<button class="cp" onclick="cp(\'{tid}\',\'{mid}\')"'
                f'{" disabled" if not r["txt_content"] else ""} title="Copy text">{cpy_svg}</button>'
            )
            dl = f'<a class="dl" href="{src}" download="{r["filename"]}" title="Download">{dl_svg}</a>'
            lbl_html = f'<div class="lbl">{r["labels"]}</div>' if r["labels"] else ""

            rows += f"""
            <tr id="row-{sid}" class="">
                <td class="n">{idx}</td>
                <td class="m" onclick="fullscreen('{vid}',{str(r['is_video']).lower()})">
                    {media_tag}
                </td>
                <td class="tc">{lbl_html}{txt_cell}</td>
                <td class="ac">
                    {cpy}
                    <div class="msg" id="{mid}"></div>
                </td>
                <td class="dc">{dl}</td>
                <td class="sc"><button class="st" id="{sid}" onclick="toggleStatus('{sid}')" title="Mark used/not used">{check_svg}</button></td>
            </tr>"""

        sections += f"""
        <div class="b{' collapsed' if bidx > 0 else ''}" id="batch-{bid}">
            <h2 onclick="toggleBatch('{bid}')">
                <span class="chevron">{'▸' if bidx > 0 else '▾'}</span>
                {batch['name']} <span class="c">{len(batch['items'])}</span>
                <span class="batch-progress" id="bp-{bid}"></span>
            </h2>
            <div class="tw"><table><thead><tr><th>#</th><th>Media</th><th>Text</th><th></th><th></th><th></th></tr></thead>
            <tbody>{rows}</tbody></table></div>
        </div>"""

    # Sidebar nav items
    nav_items = '<a class="si active" onclick="filterBatch(\'all\')">All <span class="sc">{}</span></a>'.format(total)
    for b in batches:
        bid = b['name'].replace(" ", "_")
        nav_items += '<a class="si" onclick="filterBatch(\'{}\')">{} <span class="sc">{}</span></a>'.format(bid, b['name'], len(b['items']))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Outputs</title>
<style>
:root {{ --bg: #0d0d0d; --bg2: #1a1a1a; --bg3: #222; --fg: #ddd; --fg2: #bbb; --fg3: #888; --border: #222; --th-bg: #0d0d0d; --row-hover: #111; --btn-bg: #222; --btn-hover: #333; --dl-bg: #1a3a2a; --dl-hover: #1f4a35; --used: #2a2a2a; --used-text: #555; --accent: #4caf50; --sidebar: #111; --sidebar-hover: #1a1a1a; --sidebar-active: #1a1a1a; }}
.light {{ --bg: #f5f5f5; --bg2: #fff; --bg3: #eee; --fg: #222; --fg2: #444; --fg3: #777; --border: #ddd; --th-bg: #f5f5f5; --row-hover: #fafafa; --btn-bg: #eee; --btn-hover: #ddd; --dl-bg: #d4edda; --dl-hover: #c3e6cb; --used: #f0f0f0; --used-text: #aaa; --accent: #28a745; --sidebar: #fafafa; --sidebar-hover: #eee; --sidebar-active: #eee; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--fg); transition: background .2s, color .2s; }}
.app {{ display: flex; min-height: 100vh; }}
.sidebar {{ width: 200px; min-width: 200px; background: var(--sidebar); padding: 20px 0; display: flex; flex-direction: column; border-right: 1px solid var(--border); }}
.s-h {{ font-size: 16px; font-weight: 600; padding: 0 16px 2px; color: var(--fg); }}
.s-sub {{ font-size: 10px; color: var(--fg3); padding: 0 16px 16px; }}
.s-nav {{ flex: 1; display: flex; flex-direction: column; gap: 2px; padding: 0 8px; }}
.si {{ display: flex; align-items: center; justify-content: space-between; padding: 7px 10px; border-radius: 6px; font-size: 12px; color: var(--fg3); cursor: pointer; text-decoration: none; transition: background .1s, color .1s; }}
.si:hover {{ background: var(--sidebar-hover); color: var(--fg); }}
.si.active {{ background: var(--sidebar-active); color: var(--fg); font-weight: 500; }}
.sc {{ background: var(--bg3); border-radius: 10px; padding: 0 6px; font-size: 9px; line-height: 18px; min-width: 20px; text-align: center; }}
.si.active .sc {{ background: var(--accent); color: #fff; }}
.s-foot {{ display: flex; align-items: center; justify-content: space-between; padding: 16px; border-top: 1px solid var(--border); }}
.s-foot .progress-bar {{ font-size: 10px; color: var(--fg3); }}
.toggle-btn {{ background: var(--btn-bg); border: none; border-radius: 4px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; color: var(--fg); padding: 5px; }}
.toggle-btn:hover {{ background: var(--btn-hover); }}
.toggle-btn svg {{ display: block; width: 100%; height: 100%; }}
.main {{ flex: 1; padding: 24px; min-width: 0; }}
.b {{ margin-bottom: 28px; }}
.b.hidden {{ display: none; }}
.b.collapsed .tw {{ display: none; }}
h2 {{ font-size: 13px; color: var(--fg3); margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; display: flex; align-items: center; gap: 6px; cursor: pointer; user-select: none; }}
h2 .c {{ font-size: 10px; color: var(--fg3); }}
.chevron {{ display: inline-block; width: 12px; font-size: 10px; transition: transform .15s; color: var(--fg3); }}
.batch-progress {{ font-size: 10px; color: var(--accent); }}
.tw {{ overflow-x: auto; }}
table {{ width: 100%; border-collapse: collapse; min-width: 440px; }}
th {{ text-align: left; font-size: 10px; color: var(--fg3); padding: 6px 8px; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: var(--th-bg); }}
td {{ padding: 6px 8px; vertical-align: middle; }}
tr {{ border-bottom: 1px solid var(--border); }}
tr:hover {{ background: var(--row-hover); }}
tr.used {{ opacity: .5; }}
tr.used .txt {{ color: var(--used-text); }}
tr.used .lbl {{ color: var(--used-text); }}
.n {{ width: 24px; font-size: 11px; color: var(--fg3); text-align: center; font-family: monospace; }}
.m {{ width: 56px; min-width: 48px; cursor: pointer; position: relative; }}
.m video, .m img {{ display: block; width: 44px; height: 78px; object-fit: cover; border-radius: 3px; background: #000; cursor: pointer; }}
#hover-preview {{ display: none; position: fixed; z-index: 1000; width: 200px; height: 356px; border-radius: 8px; overflow: hidden; box-shadow: 0 8px 40px rgba(0,0,0,.8); background: #000; pointer-events: none; }}
#hover-preview video, #hover-preview img {{ width: 100%; height: 100%; object-fit: cover; }}
#fs-modal {{ display: none; position: fixed; z-index: 9999; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,.95); cursor: zoom-out; align-items: center; justify-content: center; }}
#fs-modal.show {{ display: flex; }}
#fs-modal video, #fs-modal img {{ max-width: 98vw; max-height: 98vh; border-radius: 8px; object-fit: contain; }}
#fs-modal video {{ width: auto; height: auto; max-height: 98vh; }}
.tc {{ min-width: 160px; max-width: 300px; }}
.lbl {{ font-size: 10px; color: var(--fg3); margin-bottom: 4px; padding: 2px 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; letter-spacing: 0.3px; }}
.txt {{ font-size: 11px; line-height: 1.4; color: var(--fg2); padding: 4px 8px; background: var(--bg2); border-radius: 3px; user-select: all; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: default; }}
td.ac, td.dc, td.sc {{ padding: 6px 4px; vertical-align: middle; position: relative; }}
.ac {{ width: 36px; text-align: center; }}
.dc {{ width: 36px; text-align: center; }}
.sc {{ width: 36px; text-align: center; }}
.cp, .dl, .st {{ background: var(--btn-bg); border: none; border-radius: 4px; cursor: pointer; display: inline-flex; align-items: center; justify-content: center; width: 30px; height: 30px; text-decoration: none; vertical-align: middle; color: var(--fg); }}
.cp:hover, .st:hover {{ background: var(--btn-hover); }}
.dl {{ background: var(--dl-bg); }}
.dl:hover {{ background: var(--dl-hover); }}
.cp:disabled {{ opacity: .2; cursor: default; }}
.cp svg, .dl svg, .st svg {{ display: block; }}
.st.checked svg {{ stroke: var(--accent); }}
.msg {{ font-size: 10px; color: var(--accent); line-height: 1; text-align: center; position: absolute; bottom: -2px; left: 0; right: 0; pointer-events: none; white-space: nowrap; }}
.muted {{ color: var(--fg3); font-style: italic; font-size: 11px; }}
</style>
</head>
<body>
<div class="app">
<aside class="sidebar">
<div class="s-h">Outputs</div>
<div class="s-sub">{total} items · {len(batches)} batches</div>
<nav class="s-nav">{nav_items}</nav>
<div class="s-foot">
<span class="progress-bar" id="global-progress">0/{total} used</span>
<button class="toggle-btn" onclick="toggleTheme()" title="Toggle dark/light mode">
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
</button>
</div>
</aside>
<main class="main">{sections}</main>
</div>
<div id="fs-modal" onclick="closeFS()"></div>
<script>
var uid = '{uid}';
var total = {total};
document.addEventListener('DOMContentLoaded', function() {{
    loadAllStatus();
    updateGlobalProgress();
    // Batch collapse state
    document.querySelectorAll('.b').forEach(function(b) {{
        var bid = b.id.replace('batch-', '');
        var saved = localStorage.getItem(uid + '_batch_' + bid);
        if (saved === '1') {{
            b.classList.add('collapsed');
            var ch = b.querySelector('.chevron');
            if (ch) ch.textContent = '\u25b8';
        }}
        if (saved === '0') {{
            var ch = b.querySelector('.chevron');
            if (ch) ch.textContent = '\u25be';
        }}
    }});
    // Theme
    var t = localStorage.getItem(uid + '_theme');
    if (t === 'light') document.body.classList.add('light');
    // Hover preview
    document.querySelectorAll('.m').forEach(function(cell) {{
        var media = cell.querySelector('video, img');
        if (!media) return;
        var isVid = media.tagName === 'VIDEO';
        var hp = null;
        cell.addEventListener('mouseenter', function(e) {{
            if (fsActive) return;
            if (!hp) {{
                hp = document.createElement('div');
                hp.id = 'hover-preview';
                document.body.appendChild(hp);
            }}
            var clone;
            if (isVid) {{
                clone = document.createElement('video');
                clone.src = media.querySelector('source').src;
                clone.muted = true; clone.loop = true; clone.autoplay = true; clone.playsinline = true;
            }} else {{
                clone = document.createElement('img');
                clone.src = media.src;
            }}
            hp.innerHTML = '';
            hp.appendChild(clone);
            var rect = cell.getBoundingClientRect();
            var left = rect.right + 10;
            var top = rect.top;
            if (left + 260 > window.innerWidth) left = rect.left - 260 - 10;
            if (top + 360 > window.innerHeight) top = window.innerHeight - 360 - 10;
            if (top < 10) top = 10;
            hp.style.left = left + 'px';
            hp.style.top = top + 'px';
            hp.style.display = 'flex';
        }});
        cell.addEventListener('mouseleave', function() {{
            var hp = document.getElementById('hover-preview');
            if (hp) hp.style.display = 'none';
        }});
        media.addEventListener('mouseenter', function() {{ if (isVid && !fsActive) media.play(); }});
        media.addEventListener('mouseleave', function() {{ if (isVid && !fsActive) {{ media.pause(); media.currentTime = 0; }} }});
    }});
}});
// Batch filter
function filterBatch(bid) {{
    document.querySelectorAll('.si').forEach(function(el) {{
        var match = el.getAttribute('onclick');
        el.classList.toggle('active', match && match.includes("'" + bid + "'"));
    }});
    document.querySelectorAll('.b').forEach(function(b) {{
        if (bid === 'all') {{
            b.classList.remove('hidden');
        }} else {{
            b.classList.toggle('hidden', b.id !== 'batch-' + bid);
        }}
    }});
}}
// Status tracking
function toggleStatus(sid) {{
    var key = uid + '_status_' + sid;
    var cur = localStorage.getItem(key) === '1';
    localStorage.setItem(key, cur ? '0' : '1');
    loadAllStatus();
    updateGlobalProgress();
}}
function loadStatus(sid) {{
    var row = document.getElementById('row-' + sid);
    var btn = document.getElementById(sid);
    if (!row || !btn) return;
    var key = uid + '_status_' + sid;
    var used = localStorage.getItem(key) === '1';
    if (used) {{ row.classList.add('used'); btn.classList.add('checked'); }}
    else {{ row.classList.remove('used'); btn.classList.remove('checked'); }}
}}
function loadAllStatus() {{
    document.querySelectorAll('.st').forEach(function(b) {{ loadStatus(b.id); }});
    document.querySelectorAll('.b').forEach(function(batch) {{
        var bid = batch.id.replace('batch-', '');
        var rows = batch.querySelectorAll('.st');
        var done = 0;
        rows.forEach(function(b) {{ if (localStorage.getItem(uid + '_status_' + b.id) === '1') done++; }});
        var el = document.getElementById('bp-' + bid);
        if (el && rows.length) el.textContent = done + '/' + rows.length + ' used';
    }});
}}
function updateGlobalProgress() {{
    var all = document.querySelectorAll('.st');
    var done = 0;
    all.forEach(function(b) {{ if (localStorage.getItem(uid + '_status_' + b.id) === '1') done++; }});
    document.getElementById('global-progress').textContent = done + '/' + total + ' used';
}}
// Batch collapse
function toggleBatch(bid) {{
    var b = document.getElementById('batch-' + bid);
    if (!b) return;
    b.classList.toggle('collapsed');
    localStorage.setItem(uid + '_batch_' + bid, b.classList.contains('collapsed') ? '1' : '0');
    var ch = b.querySelector('.chevron');
    if (ch) ch.textContent = b.classList.contains('collapsed') ? '\u25b8' : '\u25be';
}}
// Theme
function toggleTheme() {{
    document.body.classList.toggle('light');
    var isLight = document.body.classList.contains('light');
    localStorage.setItem(uid + '_theme', isLight ? 'light' : 'dark');
}}
// Fullscreen
var fsActive = false;
function fullscreen(vid, isVideo) {{
    if (fsActive) return;
    var modal = document.getElementById('fs-modal');
    var src = document.getElementById(vid);
    if (!src) return;
    modal.innerHTML = '';
    if (isVideo) {{
        var c = document.createElement('video');
        c.src = src.querySelector('source').src;
        c.muted = false; c.loop = true; c.autoplay = true; c.playsinline = true; c.controls = true;
        c.onclick = function(e) {{ e.stopPropagation(); }};
        modal.appendChild(c);
    }} else {{
        var c = document.createElement('img');
        c.src = src.src;
        c.onclick = function(e) {{ e.stopPropagation(); }};
        modal.appendChild(c);
    }}
    modal.classList.add('show');
    fsActive = true;
}}
function closeFS() {{
    var modal = document.getElementById('fs-modal');
    modal.classList.remove('show');
    modal.innerHTML = '';
    fsActive = false;
}}
// Copy
function cp(tid, mid) {{
    var t = document.getElementById(tid).innerText;
    navigator.clipboard.writeText(t).then(function() {{
        var m = document.getElementById(mid);
        m.innerText = 'Copied!';
        setTimeout(function() {{ m.innerText = ''; }}, 1500);
    }}).catch(function() {{
        var m = document.getElementById(mid); m.innerText = 'Failed';
    }});
}}
</script>
</body>
</html>"""

    out_path = Path(output_dir) / "dashboard.html"
    out_path.write_text(html, encoding="utf-8")

    print(f"Dashboard: {out_path} ({total} items, {len(batches)} batches)")

    if serve:
        _serve(output_dir, port)
    else:
        webbrowser.open(str(out_path.resolve()))

    return str(out_path)


def _serve(directory, port):
    os.chdir(directory)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"Serving at http://localhost:{port}")
        print(f"On phone: http://YOUR_IP:{port}")
        print("Press Ctrl+C to stop")
        webbrowser.open(f"http://localhost:{port}/dashboard.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dashboard")
    parser.add_argument("--dir", help="Output folder path")
    parser.add_argument("--all", action="store_true", help="Scan all batches in outputs/")
    parser.add_argument("--serve", action="store_true", help="Start local HTTP server for phone access")
    parser.add_argument("--port", type=int, default=8000, help="Port for HTTP server")
    args = parser.parse_args()

    if args.all:
        generate_dashboard(all_flag=True, serve=args.serve, port=args.port)
    elif args.dir:
        generate_dashboard(args.dir, serve=args.serve, port=args.port)
    else:
        print("Use --dir <path> or --all")
