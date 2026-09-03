"""Install a self-contained HTML page as a post, then rebuild the index.

    python publish.py <path-to-html> --slug allen-vs-jackson \
        --title "Josh vs Lamar." --description "..." --tag NFL

If the slug already exists in posts.json the entry is updated in place and the
file replaced, so re-publishing an edited article keeps its URL and its date.
"""
import argparse, json, os, shutil, subprocess, sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
POSTS = os.path.join(HERE, "posts.json")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="standalone .html file to publish")
    ap.add_argument("--slug", required=True, help="url segment, e.g. allen-vs-jackson")
    ap.add_argument("--title")
    ap.add_argument("--description")
    ap.add_argument("--tag", default="Post")
    ap.add_argument("--date", default=date.today().isoformat())
    ap.add_argument("--assets", help="optional folder copied in alongside the page")
    ap.add_argument("--commit", action="store_true", help="git add/commit after building")
    a = ap.parse_args()

    if not os.path.exists(a.source):
        sys.exit(f"no such file: {a.source}")

    dest_dir = os.path.join(HERE, "posts", a.slug)
    os.makedirs(dest_dir, exist_ok=True)
    shutil.copy(a.source, os.path.join(dest_dir, "index.html"))
    if a.assets and os.path.isdir(a.assets):
        target = os.path.join(dest_dir, os.path.basename(a.assets.rstrip("/")))
        shutil.rmtree(target, ignore_errors=True)
        shutil.copytree(a.assets, target)

    cfg = json.load(open(POSTS, encoding="utf-8"))
    existing = next((p for p in cfg["posts"] if p["slug"] == a.slug), None)
    if existing:
        for k, v in [("title", a.title), ("description", a.description), ("tag", a.tag)]:
            if v:
                existing[k] = v
        print(f"updated existing post: {a.slug}")
    else:
        if not (a.title and a.description):
            sys.exit("--title and --description are required for a new post")
        cfg["posts"].append(dict(slug=a.slug, title=a.title, description=a.description,
                                 date=a.date, tag=a.tag))
        print(f"added new post: {a.slug}")
    json.dump(cfg, open(POSTS, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    subprocess.run([sys.executable, os.path.join(HERE, "build_index.py")], check=True)

    if a.commit:
        subprocess.run(["git", "-C", HERE, "add", "-A"], check=True)
        msg = f"{'Update' if existing else 'Add'} post: {a.slug}"
        subprocess.run(["git", "-C", HERE, "commit", "-m", msg], check=True)
        print("committed — run `git push` when you are ready")

if __name__ == "__main__":
    main()
