"""Regenerate index.html from posts.json. Run after adding a post."""
import json, os, html
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
cfg = json.load(open(os.path.join(HERE, "posts.json"), encoding="utf-8"))
site, posts = cfg["site"], cfg["posts"]
posts = sorted(posts, key=lambda p: p["date"], reverse=True)

def esc(s):
    return html.escape(s, quote=False).replace("&amp;", "&")

def pretty(d):
    y, m, dd = (int(x) for x in d.split("-"))
    months = ["January","February","March","April","May","June","July",
              "August","September","October","November","December"]
    return f"{months[m-1]} {dd}, {y}"

tagline_html = (f'    <p class="tagline">{esc(site["tagline"])}</p>'
                if site.get("tagline") else "")

cards = "\n".join(f"""    <li class="post">
      <a href="posts/{p['slug']}/">
        <h2>{esc(p['title'])}</h2>
        <p>{esc(p['description'])}</p>
        <div class="meta"><span class="tag">{esc(p.get('tag','Post'))}</span>
          <span>{pretty(p['date'])}</span></div>
      </a>
    </li>""" for p in posts)

doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta name="description" content="{esc(site["tagline"] or site["title"] + " — " + site["author"])}">
<title>{esc(site['title'])}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;700;800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="wrap">
  <header>
    <div class="eyebrow">{esc(site['author'])}</div>
    <h1><a href="./">{esc(site['title'])}</a></h1>
{tagline_html}
  </header>

  <ul class="posts">
{cards}
  </ul>

  <footer>
    <span>&copy; {date.today().year} {esc(site['author'])}</span>
    <span><a href="{site['github']}">GitHub</a></span>
  </footer>
</div>
<script>
(function(){{
  var b=document.createElement('button'); b.className='themebtn'; b.type='button';
  var root=document.documentElement;
  function cur(){{ return root.getAttribute('data-theme')
    || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'); }}
  function paint(){{ b.textContent = cur()==='dark' ? 'Light' : 'Dark';
    b.setAttribute('aria-label','Switch to '+(cur()==='dark'?'light':'dark')+' theme'); }}
  b.addEventListener('click', function(){{
    root.setAttribute('data-theme', cur()==='dark' ? 'light' : 'dark'); paint(); }});
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', paint);
  document.body.appendChild(b); paint();
}})();
</script>
</body>
</html>
"""
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(doc)
print(f"wrote index.html — {len(posts)} post(s)")
