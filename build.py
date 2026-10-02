#!/usr/bin/env python3
"""Build the chapala-topics static section from content/*.md.

Run with the interpreter that has python-markdown:
    /usr/bin/python3 build.py

Output is portable: relative links only, one shared stylesheet, no absolute
domain anywhere. The same folder can be dropped at quillio.mx/chapala-topics,
at a subdomain, or at / on any static host.

Page chrome, defined once here:
  - header: the brand, and nothing else (no trail up there)
  - in-page trail above the title, delimited with >>
  - byline from front matter (author / author_url / place / date)
  - a prominent primary-source callout from front matter (primary_*)
  - an auto-generated Contents list for note pages
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
    "with any provider or publication."
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
</div></header>
<main class="wrap">
{crumbs}<h1>{title}</h1>
{byline}{primary}{toc}{body}
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


def render(text):
    md = markdown.Markdown(
        extensions=["tables", "fenced_code", "sane_lists", "attr_list", "md_in_html", "toc"],
        extension_configs={"toc": {"toc_depth": "2-3", "permalink": False}},
        output_format="html5",
    )
    return md.convert(text), getattr(md, "toc", "")


pages = []
for f in sorted(CONTENT.glob("*.md")):
    meta, body = front_matter(f.read_text(encoding="utf-8"))
    slug = "" if f.stem == "index" else f.stem
    pages.append({"slug": slug, "meta": meta, "title": meta.get("title", f.stem), "body": body})


def crumbs_html(prefix, slug):
    if not slug:
        return ""
    return (f'<nav class="crumbs"><a href="{prefix}">{SITE_NAME}</a>'
            f'<span class="sep">&gt;&gt;</span>'
            f'<a href="{prefix}#notes">Notes</a></nav>\n')


def byline_html(meta):
    author = meta.get("author")
    if not author:
        return ""
    url = meta.get("author_url")
    name = f'<a href="{H.escape(url)}">{H.escape(author)}</a>' if url else H.escape(author)
    rest = " · ".join(x for x in (meta.get("place"), meta.get("date")) if x)
    tail = f" · {H.escape(rest)}" if rest else ""
    return f'<p class="byline">By {name}{tail}</p>\n'


def primary_html(meta):
    url = meta.get("primary_url")
    if not url:
        return ""
    label = meta.get("primary_label", "Primary source")
    text = meta.get("primary_text") or url
    return (f'<aside class="primary"><span class="label">{H.escape(label)}</span>'
            f'<a href="{H.escape(url)}">{H.escape(text)}</a></aside>\n')


for p in pages:
    slug = p["slug"]
    prefix = "" if slug == "" else "../"
    body_html, toc = render(p["body"])
    if not slug:
        toc = ""
    toc_html = (f'<nav class="toc"><span class="label">Contents</span>{toc}</nav>\n' if toc else "")
    out_dir = ROOT if slug == "" else ROOT / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = TEMPLATE.format(
        title=H.escape(p["title"]),
        site=SITE_NAME,
        prefix=prefix,
        crumbs=crumbs_html(prefix, slug),
        byline=byline_html(p["meta"]),
        primary=primary_html(p["meta"]),
        toc=toc_html,
        body=body_html,
        footer=FOOTER,
        built=BUILT,
    )
    out_file = out_dir / "index.html"
    out_file.write_text(doc, encoding="utf-8")
    print("wrote", out_file.relative_to(ROOT))

(ROOT / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
(ROOT / ".nojekyll").write_text("\n", encoding="utf-8")
print("wrote robots.txt and .nojekyll")
