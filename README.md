# santoshkumaradhikari.github.io

Personal professional website for Santosh Kumar Adhikari — healthcare professional,
finance researcher, and technology enthusiast.

Plain HTML/CSS/JS, no build step. Published with GitHub Pages at
[santoshkumaradhikari.com.np](https://santoshkumaradhikari.com.np/) (see `CNAME`).

## Local preview

Open `index.html` directly in a browser, or serve it locally:

```
python3 -m http.server 8000
```

Then visit http://localhost:8000

## Structure

### Personal site (root)

- `index.html` — single-page personal site
- `style.css` — styling for the personal site
- `script.js` — theme toggle, mobile nav, scrollspy, footer year
- `sitemap.xml` — all published URLs
- `CNAME` — custom domain

### The Investor's Canon (`investors-canon/`)

A complete 118-chapter guide to NEPSE investing, organised as 4 volumes and
Part 0 plus 18 parts.

- `index.html` — table of contents
- `framework.html` — 3-diagram overview of the system
- `study-guide.html` — suggested reading paths
- `glossary.html` — 39 key terms
- `chapters/` — 121 chapter pages (`ch-0-1` … `ch-118`)
- `css/style.css` — shared Canon stylesheet
- `js/audio-reader.js` — read-aloud player, loaded by every Canon page

## Conventions

- Chapter pages are numbered `ch-NN-slug.html` and listed in
  `investors-canon/index.html`, which is the single source of truth for
  chapter order, titles, and part grouping.
- Within a chapter, section headings are `<h2>Lesson N.M — Title</h2>`, where
  `N` matches the chapter number.
- Each chapter links to its previous and next chapter via `.chapter-nav`.
- Add new URLs to `sitemap.xml` when publishing a page.
