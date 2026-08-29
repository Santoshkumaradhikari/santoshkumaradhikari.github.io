#!/usr/bin/env python3
"""Regenerate sitemap.xml from the pages actually present in the repository.

Run from the repository root:

    python3 tools/build-sitemap.py

Why this exists: the sitemap was hand-maintained, so every time a page was
added or removed it drifted out of step with the site. This rebuilds it from
what is really on disk, so it cannot go stale.

Rules applied:
  * Only .html files are included.
  * Pages marked <meta name="robots" content="noindex"> are skipped (404.html).
  * Google Search Console verification files are skipped.
  * index.html becomes a directory URL ("/" and "/investors-canon/") because
    that is the form the site links to and declares as canonical.
  * <lastmod> comes from the file's last git commit date, not today's date, so
    it stays honest about when the content actually changed.
  * Priority: homepage 1.0, book landing page 0.9, everything else 0.7.
"""

import os
import re
import subprocess
import sys

DOMAIN = "https://santoshkumaradhikari.com.np"


def git_last_modified(path):
    """Return the file's last commit date as YYYY-MM-DD, or None if untracked."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", path],
            capture_output=True, text=True, check=False,
        ).stdout.strip()
        return out or None
    except OSError:
        return None


def url_for(path):
    """Map a file path to its canonical public URL."""
    rel = path.replace(os.sep, "/")
    if rel == "index.html":
        return DOMAIN + "/"
    if rel.endswith("/index.html"):
        return DOMAIN + "/" + rel[: -len("index.html")]
    return DOMAIN + "/" + rel


def priority_for(url):
    if url == DOMAIN + "/":
        return "1.0"
    if url == DOMAIN + "/investors-canon/":
        return "0.9"
    return "0.7"


def collect():
    pages = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".git", "node_modules", "tools"}]
        for name in files:
            if not name.endswith(".html"):
                continue
            if name.startswith("google") and "verif" not in name:
                # Search Console verification stub - not a real page.
                if re.fullmatch(r"google[0-9a-f]+\.html", name):
                    continue
            path = os.path.normpath(os.path.join(root, name))
            try:
                html = open(path, encoding="utf-8").read()
            except OSError:
                continue
            if re.search(r'<meta\s+name="robots"\s+content="[^"]*noindex', html):
                continue
            pages.append(path)
    return sorted(pages)


def main():
    if not os.path.isdir(".git"):
        sys.exit("Run this from the repository root.")

    pages = collect()
    entries = []
    for path in pages:
        url = url_for(path)
        entries.append((url, git_last_modified(path), priority_for(url)))

    # Homepage first, then the book landing page, then everything else A-Z.
    def sort_key(e):
        url = e[0]
        if url == DOMAIN + "/":
            return (0, url)
        if url == DOMAIN + "/investors-canon/":
            return (1, url)
        return (2, url)

    entries.sort(key=sort_key)

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for url, lastmod, priority in entries:
        lines.append("  <url>")
        lines.append(f"    <loc>{url}</loc>")
        if lastmod:
            lines.append(f"    <lastmod>{lastmod}</lastmod>")
        lines.append(f"    <priority>{priority}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")

    with open("sitemap.xml", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    print(f"sitemap.xml written with {len(entries)} URLs")


if __name__ == "__main__":
    main()
