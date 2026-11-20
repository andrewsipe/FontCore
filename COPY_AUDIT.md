# Wording audit: FontCore's shared messages

2026-11-20, with the `cli-writing` skill. **Sections A (0.2.2) and B (0.2.3) applied 2026-11-20.** C is still a proposal. Pick by number
("all of A", "B2, B4", "skip C3"), or rewrite any line yourself and I'll use yours.

Scope: the messages every replacer prints through `core_nameid_replacer_base.py` and `core_console_styles.py`,
plus the status labels. Not covered yet: each tool's own `--help` (a later pass, one tool at a time), and
`core_logging_config.py`'s extraction messages (they belong to FontExtractor2).

Kinds: **fix** = says something the tool doesn't do; **jargon** = internal or table-level detail the reader doesn't
need; **term** = drifts from the skill's Terms table or from its neighbors; **clear** = easier to understand;
**cut** = shorter with the same meaning and scope. *(verify)* = I'm not sure the shorter text keeps the exact scope;
the original stays unless you say otherwise.

## A. Fixes (the text is wrong, or points at something that doesn't exist)

| # | Where | Now | Proposed | Why |
|---|---|---|---|---|
| A1 ✓ | Active flags list (`core_nameid_replacer_base.py:573`) | `-dry, --dry-run : Preview mode - no changes will be saved` | `-n, --dry-run : preview only; no changes are saved` | There is no `-dry` flag; it's `-n`. |
| A2 ✓ | Active flags list (`:576`) | `-yes, --confirm : Auto-confirm all prompts` | `-y, --yes : skip the confirmation` | The flag is `-y/--yes`. The code also checks an option called `confirm`, which doesn't exist, so this line **never prints** even when `-y` is used. Fixing it needs a one-word code change. |
| A3 ✓ | Active flags list (`:579`) | `-R, --recursive : Process directories recursively` | `-r, --recursive : include subfolders` | The flag is lowercase `-r`. |
| A4 ✓ | Compound-modifier warning (`:466`) | `To fix: run Find-N-Replace with the RemoveModifierSpaces preset.` | `To fix: run fontnameid replace with the RemoveModifierSpaces preset.` | `Find-N-Replace` is no longer the command name. *(verify the preset name still exists)* |
| A5 ✓ | Plain-text prompt (`core_console_styles.py:1056`, used only when Rich is missing) | prints the literal text `[input][bold](y/N): [/bold][/input]` | no wording change; the markup shouldn't be printed | Code fix. Rich is now a required dependency, so this path is rare. |

## B. Jargon and terms

| # | Where | Now | Proposed | Kind |
|---|---|---|---|---|
| B1 ✓ | Checklist line (`:596`) | `Mac name records will be removed (platformID=1)` | `Mac name records will be removed` | jargon: platform numbers stay in the flag's help, where someone might match them to another tool |
| B2 ✓ | Flag list, `-dmr` (`:586`) | `-dmr, --delete-mac-records : Remove all Mac name records (platformID=1) before processing` | `-dmr, --delete-mac-records : remove all Mac name records (platform 1) before processing` | jargon: lowercase fragment like the finished tools; `platformID=1` becomes `platform 1`; scope kept |
| B3 ✓ | Flag list, `--empty-fields-only` (`:591`) | `Only fill blank Windows English name entries; do not overwrite existing text` | `fill only the blank Windows English name records; leave existing text alone` | term: "name entries" → "name records"; scope kept |
| B4 ✓ | Deletion summary (`core_console_styles.py:954`) | `Macintosh records (platformID=1)` | `Mac name records (platform 1)` | term: "Macintosh records" and "Mac name records" both appear |
| B5 ✓ | Deletion summary (`:959`) | `non-Windows/English/Latin records (keep only platformID=3, platEncID=1, langID=0x409)` | `every name record except Windows English (platform 3, encoding 1, language 0x409)` *(verify)* | jargon, but the exact IDs stay; says what is kept instead of "non-… records" |
| B6 ✓ (changed) | Header (`:156`) | `Name ID 8 Replacer - Processing nameID=8 records` | `Manufacturer name (nameID 8)` | clear: the old header repeats itself and names an internal "replacer" |
| B7 ✓ (changed) | Checklist (`core_console_styles.py:869`) | `Script: NameID 8 Replacer` | `Command: fontnameid 8` | jargon: "Script" and the old script name |
| B8 ✓ | Checklist (`core_console_styles.py:867`) | `Pre-flight checklist:` and `Operations to perform:` | `Before it starts:` and `What will happen:` | jargon: "pre-flight" and "operations" are developer words |
| B9 (deferred) | Checklist, replace line (`core_console_styles.py:983`) | `Replace nameID 8 (Manufacturer) with: Acme` | `Set the manufacturer name (nameID 8) to: Acme` *(verify)* | clear: with `--empty-fields-only` or a missing record nothing is replaced, so "set" is exact; plain name first, ID in parentheses |

## C. Clear / cut

| # | Where | Now | Proposed | Kind |
|---|---|---|---|---|
| C1 | Prompt (`:300`) | `About to modify 3 file(s). Proceed?` followed by a second `Proceed? (y/N/q)` | `About to modify 3 files.` then `Proceed? (y/N/q)` | cut: "Proceed?" is asked twice; needs a plural helper so "1 file / 3 files" reads right |
| C2 | Summary label (`core_console_styles.py:901`) | `Processing Completed!` | `Finished` | term: the skill avoids exclamation marks; the counts follow on the next lines |
| C3 | File list (`:163`) | `Found 1 font file(s) to process:` | `Found 1 font file:` / `Found 3 font files:` | clear: needs the same plural helper |
| C4 | Nothing to do (`:552`) | `No font files found to process.` | `No font files found.` | cut |
| C5 | Mac warning (`:222`) | `Use -dmr to remove them before processing for cleaner results` | `Use -dmr to remove them before processing.` | cut: "cleaner results" is a judgment the code doesn't make |
| C6 | Mac warning (`:220`) | `Macintosh name records detected in 2 file(s)` / `4 total records` | `Found 4 Mac name records in 2 files.` | term: matches the line shown when `-dmr` is on (`Found 3 Mac name record(s) in 1 file(s)…`) |
| C7 | Active flags header (`:176`) | `Active Flags:` | `Options in use:` | clear |
| C8 | Error summary (`core_error_handling.py:274`) | `Recoverable: NO` | `Recoverable: no` | term: only this line shouts |

## D. Leave alone

- Status labels: `UPDATED`, `NO CHANGE`, `SAVED TO`, `REMOVED`, `SKIPPED`, `DUPLICATE`, `WARNING`, `ERROR`. Short,
  consistent and the same across every tool.
- `Variable font detected`, `Cancelled`, and the file-collector progress line (`12 fonts found (340 files scanned)`).
- `Unknown status: 'x'. Available: …` is a developer-facing error and stays technical.

## Needs a code change, not only new text

- **A2** (the `confirm` / `yes` option name) and **A5** (printing markup in the plain-text fallback).
- **C1, C3** need a small helper that picks "file" or "files" from the count. Without it, "file(s)" stays.
- **A1, A2, A3, B2, B3** appear only in the replacers' preflight; each tool's own `--help` has separate wording and
  gets its own pass.

## Not changed because they aren't FontCore's

`core_logging_config.py` prints FontExtractor2-specific lines ("Font extraction finished", "Where fonts were detected
(by site)"). Left alone.

## Notes on B as applied

- **B6** became `{description} (nameID {n})`, e.g. `Manufacturer (nameID 8)`, `Unique ID (nameID 3)`. NameID 0, 2 and 4 were passing
  `Processing nameID=N records` as their description, so those three now pass `Copyright`, `Font Subfamily` and
  `Full Font Name` (FontNameID).
- **B7** dropped the `Script:` line for replacers instead of writing `Command: fontnameid 8`: the header right above already names
  the ID, and FontCore shouldn't hard-code a command name. The Catalog Apply plan keeps a line, now `Task: Catalog Metadata Apply`.
- **B8** became `Before starting:` and `This will:`.
- **B9** belongs to FontNameID (`Replace nameID 8 (Manufacturer) with: …` is built in each replacer, and in
  `fmt_replacement_operation` for IDs 0, 2 and 4). It goes into FontNameID's own wording pass.
- Also seen, FontNameID's: the Deleter prints `Non-Windows/English records: N`, which should match B5.
