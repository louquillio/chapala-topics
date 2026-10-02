#!/usr/bin/env python3
"""Build the chapala-topics static section from content/*.md.

Run with the interpreter that has python-markdown:
    /usr/bin/python3 build.py

Output is portable: relative links only, one shared stylesheet, no absolute
domain anywhere. The same folder can be dropped at quillio.mx/chapala-topics,
at a subdomain, or at / on any static host.

Page chrome, defined once here:
  - header: brand + site nav
  - in-page breadcrumb above the title (notes only)
  - byline from front matter (author / author_url / place / date)
  - reverse-monochrome footer with the standing disclaimer
"""
import html as H
import pathlib
import re

import markdown

ROOT = pathlib.Path(__file__).resolve().parent
CONTENT = ROOT / "content"

SITE_NAME = "Chapala Topics"
FOOTER = (
    "Personal research and opinion by Lou Quillio. Independent, and not affiliated "
    "with any provider or publication. Published here because a local forum does not "
    "permit analytically critical posts about local providers."
)
BUILT = "October 2, 2026"

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{title} · {site}</title>
<link rel="stylesheet" href="{prefix}assets/style.css">
</head>
<body>
<header class="site"><div class="wrap">
<a class="brand" href="{prefix}">{site}</a>
<nav class="site">{nav}</nav>
</div></header>
<main class="wrap">
{crumbs}<h1>{title}</h1>
{byline}{body}
</main>
<footer class="site"><div class="wrap">
<p>{footer}</p>
<p class="meta">Built {built}.</p>
</div></footer>
</body>
</html>
"""


def front_matter(text):
    meta, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip().lower()] = v.strip()
        body = text[m.end():]
    return meta, body


def md2html(text):
    return markdown.markdown(
        text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html"],
        output_format="html5",
    )


pages = []
for f in sorted(CONTENT.glob("*.md")):
    meta, body = front_matter(f.read_text(encoding="utf-8"))
    slug = "" if f.stem == "index" else f.stem
    pages.append({"slug": slug, "meta": meta, "title": meta.get("title", f.stem), "body": body})

notes = sorted([p for p in pages if p["slug"]], key=lambda p: p["title"])


def nav_html(prefix, current):
    bits = [f'<a href="{prefix}">Notes</a>']
    for p in notes:
        cls = ' class="here"' if p["slug"] == current else ""
        bits.append(f'<a href="{prefix}{p["slug"]}/"{cls}>{H.escape(p["title"])}</a>')
    return " · ".join(bits)


def crumbs_html(prefix, title, slug):
    if not slug:
        return ""
    return (f'<nav class="crumbs"><a href="{prefix}">{SITE_NAME}</a> '
            f'<span>/</span> <span class="here">{H.escape(title)}</span></nav>\n')


def byline_html(meta):
    author = meta.get("author")
    if not author:
        return ""
    url = meta.get("author_url")
    name = f'<a href="{H.escape(url)}">{H.escape(author)}</a>' if url else H.escape(author)
    rest = " · ".join(x for x in (meta.get("place"), meta.get("date")) if x)
    tail = f" · {H.escape(rest)}" if rest else ""
    return f'<p class="byline">By {name}{tail}</p>\n'


for p in pages:
    slug = p["slug"]
    prefix = "" if slug == "" else "../"
    out_dir = ROOT if slug == "" else ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = TEMPLATE.format(
        title=H.escape(p["title"]),
        site=SITE_NAME,
        prefix=prefix,
        nav=nav_html(prefix, slug),
        crumbs=crumbs_html(prefix, p["title"], slug),
        byline=byline_html(p["meta"]),
        body=md2html(p["body"]),
        footer=FOOTER,
        built=BUILT,
    )
    out_file = out_dir / "index.html"
    out_file.write_text(doc, encoding="utf-8")
    print("wrote", out_file.relative_to(ROOT))

(ROOT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
(ROOT / ".nojekyll").write_text("\n", encoding="utf-8")
print("wrote robots.txt and .nojekyll")
