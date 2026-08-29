# santoshkumaradhikari.github.io

Personal site and research library for Santosh Kumar Adhikari — independent
finance researcher on Nepal's capital markets, and author of *The Investor's
Canon*.

Plain HTML, CSS and JavaScript. No build step, no dependencies, no framework.
Published with GitHub Pages at
[santoshkumaradhikari.com.np](https://santoshkumaradhikari.com.np/) (see `CNAME`).

## Local preview

Open `index.html` directly in a browser, or serve the site so that root-relative
paths (`/style.css`, `/404.html`) resolve correctly:

```
python3 -m http.server 8000
```

Then visit http://localhost:8000

## Structure

### Root

| Path | Purpose |
| --- | --- |
| `index.html` | Single-page personal site |
| `404.html` | Not-found page, served automatically by GitHub Pages |
| `style.css` | Styling for the personal site |
| `script.js` | Theme toggle, mobile nav, skip link, scroll reveal, scrollspy, footer year |
| `robots.txt` | Crawler policy; points at the sitemap |
| `sitemap.xml` | All 126 indexable URLs — **generated**, see below |
| `CNAME` | Custom domain |
| `tools/build-sitemap.py` | Regenerates `sitemap.xml` from the files on disk |

### The Investor's Canon (`investors-canon/`)

A 118-chapter guide to investing in Nepal, organised as four volumes covering
Part 0 plus Parts I–XVIII. 121 chapter files in total, because Part 0 is
numbered `0.1`–`0.3`.

| Path | Purpose |
| --- | --- |
| `index.html` | Table of contents — the source of truth for chapter order |
| `framework.html` | Overview of the system: volume roadmap, Two Hemispheres, Canon Score |
| `study-guide.html` | Suggested reading paths |
| `glossary.html` | 53 terms, A–Z, each linking to the chapter that explains it |
| `chapters/` | 121 chapter pages (`ch-0-1` … `ch-118`), 732 lessons |
| `css/style.css` | Shared Canon stylesheet, including print rules |
| `js/audio-reader.js` | Read-aloud player and copyright line, loaded by every Canon page |

The framework diagrams are built with CSS and inline SVG rather than images, so
they stay sharp at any size, adapt to the light and dark themes, and add no
page weight.

## Conventions

- **`investors-canon/index.html` is the single source of truth** for chapter
  order, titles and part grouping. Chapter pages must agree with it: the `<h1>`
  matches the TOC title, and the `.chapter-kicker` matches the part.
- Chapter files are named `ch-NN-slug.html`.
- Section headings are `<h2>Lesson N.M — Title</h2>`, where `N` is the chapter
  number and `M` runs consecutively from 1.
- Each chapter links to its previous and next chapter through `.chapter-nav`.
- Statute years are given in Bikram Sambat with the Gregorian year in
  parentheses, e.g. *Securities Act, 2063 (2006)*.
- Money uses Nepali digit grouping (`Rs 11,50,000`) and the lakh/crore/arba
  scale, consistent within a page.
- Prose uses British spelling.

## Publishing a new page

1. Add the page, including a unique `<title>`, a unique
   `<meta name="description">`, `rel="canonical"`, Open Graph and Twitter tags,
   and JSON-LD. Copy the `<head>` of an existing page as the template.
2. Include a skip link and wrap the content in `<main id="main" tabindex="-1">`.
3. Regenerate the sitemap:

   ```
   python3 tools/build-sitemap.py
   ```

   The script walks the repository, skips anything marked
   `<meta name="robots" content="noindex">`, maps `index.html` files to their
   directory URL, and takes each `<lastmod>` from that file's last git commit
   date. Do not hand-edit `sitemap.xml`.

## Accessibility and SEO baseline

All 126 indexable pages carry a canonical URL, Open Graph and Twitter card
metadata, and Schema.org JSON-LD (`Article` for chapters, `Person` for the
homepage, `WebPage` elsewhere). Each has a skip link, a `<main>` landmark,
exactly one `<h1>`, no skipped heading levels, and honours
`prefers-reduced-motion`. Chapters print cleanly: interface controls are hidden
and an attribution line is appended.

The only file exempt from all of this is the Google Search Console
verification stub (`googleac56e58fd6b87728.html`), which must stay a bare
one-line response. `tools/build-sitemap.py` and the audit checks skip it.
