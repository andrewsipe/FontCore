---
name: cli-writing
description: Write and edit the words people read in the font command-line tools and their docs (--help text, status and error messages, prompts, preflight checklists, README, docsite pages). Use whenever a change adds or rewords a string a person will read, even when the text is a small part of a feature, and for wording audits. Applies to FontCore, FontFixer, Ebrium, FontCatalyst, FontNameID, FileRenamer and Filename_Tools.
---

# Writing for the font tools

Adapted from FontVault's `ui-writing` skill, for a command line instead of a Mac app. The goal is the same: text that
sounds like a capable, considerate person who knows fonts. Clear first, short second, warm through plain words and
rhythm, never through extra words. The problem this fixes: help and messages written like source code ("Override
nameID=8 content with exact string (supersedes all other options)") instead of for the person at the keyboard.

## Who is reading

Someone who manages or designs fonts. They know family, weight, width, italic, PostScript name, WOFF2, "install a
font". They do not know OpenType table internals, platform IDs, Python, or how the tools share code. Technical terms
are right when the information itself is technical, but lead with the plain name and add the technical one only when
the reader must match it to something else.

## Before writing

- Read the strings around yours: the same tool's `--help`, its other messages, and the same flag in the other tools.
  A flag that means the same thing in two tools gets the same words (see "Standard flag wording").
- Check what the code really does before describing it. Preview, change, move, delete and quarantine are different
  things; never blur them to sound friendlier. Say whether originals are overwritten.
- Read the finished tools (FontFixer, Ebrium, FontCatalyst) for the house style before touching an older tool.

## Voice

- Natural and direct, without changing the meaning or scope.
- Prefer a precise familiar word over a vague casual one.
- Contractions are welcome ("can't", "you'll", "isn't").
- Second person when it reads naturally ("your fonts", "your originals"); leave it out when the sentence works without.
- Warmth is plain words and a natural rhythm. No hype, no jokes, no exclamation marks, no "simply", "just", "easily",
  "please". No emoji.
- Errors, warnings and anything that overwrites or deletes: calm and exact. Say what happened or will happen, to what.

## Short, not cryptic

- Describe the person's task, not the implementation. Never show internal names: module or function names
  (`sanitize_postscript`, `FontCore`), framework names (`BatchRunner`), or old script names (`NameID8Replacer.py`).
  Use the command a person types: `fontnameid batch`.
- Name a table or ID only when it helps: "manufacturer name (nameID 8)" in a flag that edits that record; just
  "manufacturer name" in a status line. Drop platform and encoding numbers (`platformID=1`); say "Mac name records".
- Cut anything the flag name or neighbor already says. Add a clause only for a consequence, a scope or a trade-off.
- One idea per sentence. Two short sentences beat one with a semicolon.
- Keep useful domain words: family, style, weight, width, slope, italic, PostScript name, WOFF2, variable font.

## Plain, but exact

Plain words replace jargon. They never replace a condition, a scope or an exception.

- Keep every qualifier that changes what happens: which records (Windows English only, or every platform), which
  fonts, what is overwritten, what is skipped, what happens when two options are combined.
- When a precise term carries the scope, keep it and say what it means in a few words ("the Windows English name
  record"), rather than dropping it for a vaguer one.
- Test: if the person read only this line, could they do something different from what the tool will do? If yes,
  the short version has lost something. Keep the longer text, or move the detail to the long help or the docs and
  keep the one-liner accurate.
- Don't add editorial words the code doesn't know ("old", "stale", "cleaner", "best") unless the code makes that
  judgment and the text says how.
- Don't pull a technical identifier out of help text if it is how the person finds the record elsewhere
  (nameID 8 appears in other font tools). Put it in parentheses after the plain name.

## When not to rewrite

- Leave clear, accurate wording alone. A change has to improve accuracy, understanding, consistency, brevity, or a tone
  that is wrong for the moment. "Sounds friendlier" is not enough.
- Never strengthen a claim, drop a condition or change a scope just to shorten it. When unsure whether a shorter
  line is still exact, keep the original and flag it in the audit as **clear (verify)** for the owner.
- Don't change strings the task didn't touch.

## By element

- **Description line (top of `--help`):** one sentence: what it does, to what. Name the safe path in the same screen
  (a "Heads up" panel when the default overwrites originals), the way FontFixer, Ebrium and FontCatalyst do.
- **Option help:** a lowercase fragment, no final period (finished tools' style), starting with a verb or a noun
  phrase that completes "this option will…" or names the thing: `write fixed fonts to DIR instead of the originals`.
  Mention a default in parentheses: `(default: 1)`. Group related options under plain headings ("input", "output and
  safety").
- **Placeholders and metavars:** a plain word (`DIR`, `FILE`, `TEXT`), not a Python name.
- **Examples:** real commands a person would run, with a short comment. Show the dry run first when a command changes files.
- **Status lines and summaries:** `what happened`, then the file or count. Counts through the shared count helper,
  never hand-formatted. A summary line reads like a sentence: "Renamed 12, skipped 3, 1 problem."
- **Warnings:** the situation, then what the person can do about it, only if something can be done.
- **Errors:** what failed, the cause only if known, a fix only if one exists. Never invent either. Don't print a
  Python traceback where a sentence will do.
- **Prompts:** name the action and the amount: "Rename 12 fonts? (y/n/q)". Don't ask "Proceed?" with nothing to proceed with.
- **Docs and README:** lead with what it does and the safe first command. Define a term the first time. Put warnings
  where the person will act, not at the bottom. Reference pages can be technical; the first screen must not be.

## Standard flag wording

Same flag, same words, in every tool (proposed; the owner confirms):

| Flag | Help text |
|---|---|
| `-r`, `--recursive` | include subfolders |
| `-n`, `--dry-run` | preview only; change nothing |
| `-y`, `--yes` | skip the confirmation |
| `-v`, `--verbose` | show more detail |
| `-o`, `--output-dir DIR` | write results to DIR instead of changing the originals |
| `--no-preview` | skip the preview and start right away |

## Terms

Seed list. Add to it when a term comes up twice. The left column is what readers see.

| Say | Not | Note |
|---|---|---|
| name record | name table entry, namerecord | Say "name table" only when the person needs the table itself. |
| family name, style name, full name, PostScript name | nameID 1, 2, 4, 6 | Add the ID in parentheses only where it must be matched. |
| manufacturer, designer, description, license | nameID 8, 9, 10, 13 | Same. |
| typographic family / style | nameID 16 / 17 | Same. |
| Mac name records | platformID=1 records | |
| preview | dry run | "Dry run" is fine inside a flag name (`-n, --dry-run`). |
| subfolders | directories, recurse | |
| overwrites your fonts | modifies in place | Say plainly whether there is a backup. |
| the file didn't change | no-op | |

## Mechanics

- American spelling (color, gray, canceled).
- Flag names, commands and filenames in backticks in docs; plain in terminal output.
- Command names are what a person types today: `fontnameid 8`, `filenametools normalize`, `fontrenamer`.
- For an audit, list location, current text, proposed text, kind and a one-line reason, and edit nothing until the
  owner picks. Kinds: **fix** (says something the tool doesn't do), **cut** (shorter, same meaning), **clear** (easier
  to understand), **term** (drifts from the Terms table or its neighbors), **jargon** (internal or table-level detail).

## Last pass

1. Does it match what the code does, including what happens to the originals?
2. Read full sentences aloud. Judge flag help and reference text by clarity, not by whether it sounds chatty.
3. Remove repetition and filler. Keep words that make it easier to understand.
4. Too cold, too cute, too vague, or too technical? Fix the one that applies.
5. Do the strings around it, and the same flag in the other tools, still match?
