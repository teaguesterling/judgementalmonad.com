# Site Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the site from a flat `blog/` directory into `blog/ma/` and `blog/fuel/` subdirectories, with a shared home page, preserving all existing links.

**Architecture:** Move all Ma content into `blog/ma/`. Create `blog/fuel/` for Ratchet Fuel. Leave redirect stubs at old paths for the two migrating essays. Update `conf.py` and toctrees. The root `index.md` becomes the site home page linking both series.

**Tech Stack:** Sphinx + MyST markdown, Furo theme, git

**Rollback:** All changes are in git. To roll back at any point: `git log --oneline` to find the commit before the restructure began, then `git reset --soft <sha>`. Every task commits, so you can also roll back to any intermediate state.

---

### Task 1: Create directory structure

**Files:**
- Create: `blog/ma/` (directory)
- Create: `blog/fuel/` (directory)

- [ ] **Step 1: Create the two subdirectories**

```bash
mkdir -p blog/ma blog/fuel
```

- [ ] **Step 2: Commit the empty structure**

```bash
touch blog/ma/.gitkeep blog/fuel/.gitkeep
git add blog/ma/.gitkeep blog/fuel/.gitkeep
git commit -m "Create blog/ma/ and blog/fuel/ directories"
```

---

### Task 2: Move Ma content into blog/ma/

**Files:**
- Move: all 18 `.md` files from `blog/` to `blog/ma/`

- [ ] **Step 1: Move all Ma markdown files**

```bash
cd /mnt/aux-data/teague/Projects/judgementalmonad.com
git mv blog/00-intro.md blog/ma/
git mv blog/01-the-four-actors.md blog/ma/
git mv blog/02-the-space-between.md blog/ma/
git mv blog/03-conversations-are-closures.md blog/ma/
git mv blog/04-raising-and-handling.md blog/ma/
git mv blog/05-predictability-as-embeddability.md blog/ma/
git mv blog/06-conversations-are-folds.md blog/ma/
git mv blog/07-computation-channels.md blog/ma/
git mv blog/08-the-specified-band.md blog/ma/
git mv blog/09-building-with-ma.md blog/ma/
git mv blog/formal-companion.md blog/ma/
git mv blog/the-residual-framework.md blog/ma/
git mv blog/coordination-is-not-control.md blog/ma/
git mv blog/case-studies.md blog/ma/
git mv blog/reference-tables.md blog/ma/
git mv blog/OUTLINE.md blog/ma/
git mv blog/the-configuration-ratchet.md blog/ma/
git mv blog/where-the-space-lives.md blog/ma/
```

- [ ] **Step 2: Verify all files moved**

```bash
ls blog/ma/*.md | wc -l
```

Expected: 18

- [ ] **Step 3: Verify blog/ is now empty of .md files**

```bash
ls blog/*.md 2>/dev/null | wc -l
```

Expected: 0

- [ ] **Step 4: Commit the move**

```bash
git add -A
git commit -m "Move all Ma content from blog/ to blog/ma/"
```

---

### Task 3: Verify internal links within Ma

All Ma posts use relative links like `[post 2](02-the-space-between.md)`. Since they all moved together, these still work. But links from posts to companions (e.g., `[formal companion](formal-companion.md)`) also need to be relative within `blog/ma/`. Verify this.

**Files:**
- Check: all files in `blog/ma/`

- [ ] **Step 1: Grep for any links that reference blog/ prefix**

```bash
grep -rn '\](blog/' blog/ma/*.md | head -20
```

Expected: 0 matches. All links within Ma should be relative (no `blog/` prefix).

- [ ] **Step 2: If any found, they're links from the old series.md toctree format. Note them for Task 5.**

---

### Task 4: Create Ma series index

**Files:**
- Create: `blog/ma/index.md`
- Remove reference: `series.md` (root level — content moves to `blog/ma/index.md`)

- [ ] **Step 1: Create blog/ma/index.md from the current series.md**

The current `series.md` uses `blog/` prefixed paths in its toctree. The new `blog/ma/index.md` uses paths relative to `blog/ma/`.

Write `blog/ma/index.md`:

```markdown
# The *Ma* of Multi-Agent Systems

*A design theory for the space between agents.*

```{toctree}
:maxdepth: 2
:caption: The Series

00-intro
01-the-four-actors
02-the-space-between
03-conversations-are-closures
04-raising-and-handling
05-predictability-as-embeddability
06-conversations-are-folds
07-computation-channels
08-the-specified-band
09-building-with-ma
```

## Supplementary Materials

```{toctree}
:maxdepth: 1
:caption: Supplementary Materials

formal-companion
the-residual-framework
coordination-is-not-control
the-configuration-ratchet
where-the-space-lives
case-studies
reference-tables
```

Note: `the-configuration-ratchet` and `where-the-space-lives` will migrate to `blog/fuel/` when the Fuel content plan executes. At that point, this toctree will be updated to point to the Fuel locations. For now they stay here so all links work.

`OUTLINE.md` is an internal planning document and is excluded from the toctree intentionally. It will generate an orphan warning, which is acceptable.
```

- [ ] **Step 2: Remove old series.md**

```bash
git rm series.md
```

- [ ] **Step 3: Commit**

```bash
git add blog/ma/index.md
git commit -m "Create Ma series index at blog/ma/index.md, remove old series.md"
```

---

### Task 5: Create redirect stubs for migrating essays

The configuration ratchet and placement essays will eventually live in `blog/fuel/`. Until Fuel posts are written, keep them in `blog/ma/` but create stubs that will redirect once Fuel exists.

For now, both files stay in `blog/ma/`. When Fuel is ready, they'll be moved to `blog/fuel/` and these stubs will be updated to point there. No action needed in this task beyond noting the plan.

- [ ] **Step 1: Verify both files exist in blog/ma/**

```bash
ls blog/ma/the-configuration-ratchet.md blog/ma/where-the-space-lives.md
```

Expected: both exist.

- [ ] **Step 2: Note: these will be moved to blog/fuel/ in the content plan. For now they stay in blog/ma/ and all existing links work.**

---

### Task 6: Create Fuel series directory with placeholder index

**Files:**
- Create: `blog/fuel/index.md`

- [ ] **Step 1: Write blog/fuel/index.md placeholder**

```markdown
# Ratchet Fuel

*A practitioner series on building systems that get smarter through friction.*

Coming soon. This series applies the [Ma of Multi-Agent Systems](../ma/index) framework to tool building, data platforms, and organizations.

Want the theory? Start with [The Ma of Multi-Agent Systems](../ma/00-intro).
```

- [ ] **Step 2: Commit**

```bash
git add blog/fuel/index.md
git commit -m "Add Fuel series placeholder index"
```

---

### Task 7: Create site home page

**Files:**
- Modify: `index.md` (root) — becomes the site home page
- Create: `blog/index.md` — or use root index.md directly (Sphinx uses root)

The user wants `blog/index.md` as the home page. But Sphinx's `conf.py` expects a root document. We'll make `blog/index.md` the toctree hub and update conf.py to point to it.

- [ ] **Step 1: Save the current landing page content before overwriting**

```bash
cp index.md drafts/landing-page-original.md
```

- [ ] **Step 2: Update root index.md to serve as the Sphinx root document**

Replace the entire current root `index.md` (the "Your Agent Is a Different System..." landing page) with a root document that contains the master toctree. Sphinx needs exactly one root doc; this is it.

```markdown
# The Judgemental Monad

*Design theory and practice for multi-agent systems.*

---

## Two series, one framework

**[The Ma of Multi-Agent Systems](blog/ma/index)** — Nine posts developing a formal theory of agent architecture. The grade lattice, the specified band, the fold model, computation channels. Why restriction works, why the orchestrator belongs at the hub, and why these are the same insight.

**[Ratchet Fuel](blog/fuel/index)** — A practitioner series on building systems that get smarter through friction. Tool design, failure streams, data platforms, organizational patterns. Code ships in every post.

---

*Ma* is the Japanese concept that the space between things is itself functional. These series explore what that means for systems where humans and AI agents work together — and for the design decisions that shape whether they work well.

```{toctree}
:hidden:
:maxdepth: 2

blog/ma/index
blog/fuel/index
```
```

Note: The "Your Agent Is a Different System..." content will be reworked into Fuel post 0 (The Ratchet Review) in the content plan. Save the current content to `drafts/landing-page-original.md` first.

This approach makes root `index.md` the actual home page (no dead "Redirecting" text) and the Sphinx root document (contains the master toctree). The `blog/index.md` from Step 1 becomes unnecessary — delete it.

- [ ] **Step 3: Commit**

```bash
git add index.md drafts/landing-page-original.md
git commit -m "Restructure root index.md as site home page, save original landing page"
```

---

### Task 8: Update conf.py

**Files:**
- Modify: `conf.py`

- [ ] **Step 1: Update exclude_patterns and temporarily show all warnings**

In `conf.py`, update exclude_patterns and temporarily comment out suppress_warnings:

```python
exclude_patterns = ["_build", ".git", ".venv", "README.md", "drafts", "experiments", "docs"]

# Temporarily show all warnings during restructure verification
# suppress_warnings = ["myst.xref_missing"]
```

- [ ] **Step 2: Verify the build**

```bash
cd /mnt/aux-data/teague/Projects/judgementalmonad.com
python -m sphinx -b html . _build/html 2>&1 | tail -20
```

Expected: Build succeeds. May have warnings about orphaned pages — that's acceptable.

- [ ] **Step 3: Check for broken toctree references**

```bash
python -m sphinx -b html . _build/html 2>&1 | grep -i "toctree contains reference to nonexisting document"
```

Expected: No matches. If any appear, note which documents are missing and fix paths.

- [ ] **Step 4: Commit**

```bash
git add conf.py
git commit -m "Update conf.py for restructured site"
```

- [ ] **Step 5: Re-enable suppress_warnings after verification passes**

In `conf.py`, uncomment:

```python
suppress_warnings = ["myst.xref_missing"]
```

```bash
git add conf.py
git commit -m "Re-enable myst.xref_missing suppression after restructure verification"
```

---

### Task 9: Update cross-references from root-level files

**Files:**
- Modify: `index.md` — already updated in Task 7
- Check: any other root-level files that reference `blog/` paths

- [ ] **Step 1: Verify series.md was removed and check root index references**

```bash
test ! -f series.md && echo "series.md removed: OK" || echo "WARNING: series.md still exists"
grep -n 'blog/' index.md
```

Expected: `series.md` does not exist. `index.md` references `blog/ma/index` and `blog/fuel/index`.

- [ ] **Step 2: Verify the Sphinx build completes without errors**

```bash
python -m sphinx -b html . _build/html 2>&1 | grep -c "ERROR"
```

Expected: 0

- [ ] **Step 3: Spot-check rendered HTML**

```bash
ls _build/html/blog/ma/00-intro.html _build/html/blog/index.html _build/html/blog/fuel/index.html 2>/dev/null
```

Expected: all three files exist.

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "Site restructure complete: blog/ma/ and blog/fuel/ with shared home"
```

- [ ] **Step 5: Push**

```bash
git push
```

---

### Task 10: Verify all links work

This is a manual verification pass after the restructure is complete.

- [ ] **Step 1: Check Ma internal links**

Pick 3 Ma posts and verify their relative links resolve:
- `blog/ma/01-the-four-actors.md` → links to `02-the-space-between.md` ✓
- `blog/ma/09-building-with-ma.md` → links to `the-configuration-ratchet.md` ✓
- `blog/ma/the-residual-framework.md` → links to `formal-companion.md` ✓

- [ ] **Step 2: Check cross-series links**

- `blog/ma/index.md` → links to `../fuel/index` ✓
- `blog/fuel/index.md` → links to `../ma/00-intro` ✓
- `blog/index.md` → links to `ma/index` and `fuel/index` ✓

- [ ] **Step 3: Check Sphinx build output for warnings**

```bash
python -m sphinx -b html . _build/html 2>&1 | grep -i warning | grep -v "myst.xref_missing" | head -10
```

Review any non-suppressed warnings.

- [ ] **Step 4: If any links are broken, fix and commit with specific paths**

```bash
git add <specific files that were fixed>
git commit -m "Fix broken links from site restructure"
```

---

## Notes

- This plan does NOT move content to Fuel or write new posts. That's the content plan (separate).
- The two migrating essays (`the-configuration-ratchet.md` and `where-the-space-lives.md`) stay in `blog/ma/` for now. They'll be moved and edited when the Fuel content plan executes.
- The original landing page ("Your Agent Is a Different System...") is saved to `drafts/landing-page-original.md` for reworking into Fuel post 0.
- All existing external links to `blog/*.html` paths will break because the files moved to `blog/ma/*.html`. If external link preservation is critical, add Sphinx redirect configuration or `.htaccess` rules. For now, we accept this — the site is not widely linked yet.
