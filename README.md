# mpg000f.github.io

Static blog served by GitHub Pages at **https://mpg000f.github.io/**.

No site generator. Each post is a self-contained HTML file with its data, styles and
scripts inlined, dropped into `posts/<slug>/index.html`. That is deliberate — the posts
are interactive pages with embedded datasets, and Jekyll or Hugo would fight both the
markup and the JavaScript.

```
index.html          generated — do not edit by hand
style.css           shell styling for the index only
posts.json          the post list; source of truth for the index
build_index.py      regenerates index.html from posts.json
publish.py          installs a post and rebuilds the index
posts/<slug>/       one folder per post
```

## Publishing a post

From the project that produced the article:

```bash
python build_standalone.py                       # emits the self-contained page
python ~/mpg000f.github.io/publish.py \
    Allen_vs_Jackson_analysis.html \
    --slug allen-vs-jackson \
    --title "Josh vs Lamar. Let's settle the debate." \
    --description "One line for the index card." \
    --tag NFL --commit
git -C ~/mpg000f.github.io push
```

Re-run the same command with an edited file to update a post — the slug keeps its URL
and its original date. `--title` and `--description` are only required the first time.

## Editing the index

Change the site title, tagline or a post's copy in `posts.json`, then:

```bash
python build_index.py
```

## First-time setup

```bash
gh repo create mpg000f.github.io --public --source=. --remote=origin --push
```

Then in the repo's **Settings → Pages**, set the source to the `main` branch, root folder.
The site is live at https://mpg000f.github.io/ within a minute or two.

To use a custom domain later, add a `CNAME` file containing the bare domain and point a
DNS record at GitHub's Pages IPs.
