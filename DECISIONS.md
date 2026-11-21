# FontCore decisions walkthrough

Working draft, 2026-11-20. Each area lists what the code decides today (with real outputs), then the questions that need
your call. **Answers to Q1–Q10 are recorded in "Decided" below.** Answer by number ("Q1 yes, Q2 b, Q4 a"). Your answers become the "How it decides" page on the docsite, so
anything marked **keep** is written down as intended, and anything you change gets a test first.

Areas: **1. Style vocabulary** and **2. How names are built** (this pass). Still to come: 3. File collection,
4. Extension checks, 5. Variable-font filenames, 6. The console contract.

---

## Area 1: Style vocabulary (`core_font_style_dictionaries.py`)

One module holds the words the tools recognize: weights, widths, slopes, optical sizes, a few decorative terms, hyphen
placement, and how compounds are spelled. `SLOPE_BASES`, `WIDTH_BASES` and `OPTICAL_BASES` are meant to be the single
source for the other modules and the tools.

### What it decides today

| Group | Terms |
|---|---|
| Widths (8 bases) | Condensed, Compressed, Compact, Narrow, Tight, Extended, Expanded, Wide; plus Semi/Demi/Extra/Ultra/Super and 1–7 X prefixes, generated |
| Slopes (11) | Italic, Oblique, Slanted, Slant, Inclined, Backslanted, Backslant, Reverse, Retalic, Cursive, Kursiv; compounds `Reverse Italic`, `Reverse Slanted` |
| Optical sizes (10) | Caption, Display, Text, Poster, Headline, Subhead, Title, Deck, Micro, Banner |
| Weights | listed in `STYLE_WORDS` only (Hairline … Ultrablack, plus 100–1000) |
| Compound spelling | `SemiBold → Semibold`, `ExtraLight → Extralight`, `SmallCaps → Smallcaps` (weights are one lowercase word) |
| Hyphen left (`Foo-Condensed`) | width terms. Hyphen right: optical sizes and Round/Rounded/Mono/Sans/Slab/Serif |

### Where it disagrees with itself or with the tools

1. **Slopes are defined four times inside FontCore**: the dictionary (`SLOPE_BASES`), a regex list in `core_name_policies`
   (`_STYLE_SLOPE_EXTRACTORS`), a hard-coded regex in `_strip_trailing_slope_tokens`, and an alias map in the variable
   filename parser. Add a term to one and the others don't know.
2. **The tools drifted from the dictionary.** `reorder-slopes` doesn't know `Cursive` or `Kursiv`. `regular` knows 5 slope
   terms and has `Expand` where the dictionary has `Compact` and `Tight`. `reorder-optical` has 17 optical terms (adds
   Big, Fine, Head, Large, Small, Tall) against the dictionary's 10.
3. **Optical sizes are inconsistent in the dictionary itself.** `STYLE_WORDS` lists Titling, Fine, Large, Small, Big and
   Tall as style words, but `OPTICAL_BASES` doesn't include them.
4. **Weight compounds are spelled two ways.** The dictionary and `filenametools compound` turn `SemiBold` into `Semibold`.
   The name builders turn a `Probe-SemiBold` filename into `Semi Bold` and leave `Probe-Semibold` as `Semibold`.
   Widths keep their CamelCase (`SemiCondensed`).
5. **`Book` and `Normal` are kept by default** ("Probe Book"), while the STAT lists `ELIDABLE_WEIGHT_NAMES` and
   `ELIDABLE_WIDTH_NAMES` (Regular, Normal, Roman, Plain, Standard, Book, Text) treat them as the default name. Those two
   lists aren't used by anything today.

### Questions

**Q1. One source of truth for slope, width and optical terms?** Derive the regexes from the dictionary, make the tools
import the lists, and add tests so they can't drift. (a) yes, (b) keep separate copies. *Recommend (a).*

**Q2. Which words are optical sizes?** (a) all of: Caption, Display, Text, Poster, Headline, Subhead, Title, Titling, Deck, Micro,
Banner, plus Fine, Large, Small, Big, Tall, Head (what `reorder-optical` uses today); (b) keep the dictionary's 10 and
treat the rest as ordinary style words; (c) your list. *Note: Small, Large, Big and Tall are also plain adjectives; if a
family is named "Big Shoulders", a match on Big could misfire. I'd lean (b) unless you rely on those in filenames.*

**Q3. `Cursive` / `Kursiv` as slopes everywhere**, including `reorder-slopes` and the `STYLE_WORDS` list. Your rule: after the
hyphen it's a slope; inside a family name it's part of the name. (a) yes, (b) no. *Recommend (a).*

**Q4. Canonical spelling of weight compounds** (SemiBold, ExtraLight, DemiBold, UltraBlack…): (a) `Semibold` one word (the
dictionary today), (b) `Semi Bold` two words (what a `SemiBold` filename becomes in names today), (c) keep whatever the file
says and never rewrite it. And the same question for widths (`SemiCondensed` vs `Semi Condensed`).

**Q5. Which "regular" words does ID1/ID4 drop?** Today only `Regular` and `Roman` ("Probe Book", "Probe Normal" stay).
(a) keep that, (b) also drop `Book`, (c) also drop `Normal`, (d) both. The replacers already have `--regular-synonyms`
(`regular_only`, `conservative`, `loose`); this is about the default.

**Q6. The unused STAT lists** (`ELIDABLE_WEIGHT_NAMES`, `ELIDABLE_WIDTH_NAMES`) put `Text` in the weights list although `Text` is
an optical size. Nothing reads them. (a) delete them, (b) keep and remove `Text`, (c) keep as is. *Recommend (a); they come
back when STAT building needs them.*

---

## Area 2: How names are built (`core_name_policies.py`)

Real outputs for `(family "Probe", modifier, style, slope)`:

| Input | ID1 family | ID4 full name | ID17 subfamily |
|---|---|---|---|
| Bold | Probe Bold | Probe Bold | Bold |
| Bold Italic | Probe Bold | Probe Bold Italic | Bold Italic |
| Regular Italic | Probe | Probe Italic | Regular Italic |
| Italic only | Probe | Probe Italic | Italic |
| Roman | Probe | Probe | Roman |
| Book | Probe Book | Probe Book | Book |
| Normal | Probe Normal | Probe Normal | Normal |
| Condensed Bold Oblique | Probe Condensed Bold Oblique | same | Condensed Bold Oblique |
| Light Cursive | Probe Light Cursive | same | Light Cursive |
| Regular Cursive | Probe Cursive | Probe Cursive | Regular Cursive |
| Wide Regular Backslanted | Probe Wide Backslanted | same | Wide Regular Backslanted |

Filenames to family and subfamily: `Probe-SemiBold → (Probe, Semi Bold)`, `Probe-Semibold → (Probe, Semibold)`,
`Probe-BoldCondensed → (Probe, Bold Condensed)`, `Probe-CondensedBold → (Probe, Condensed Bold)`,
`ProbeCondensed-Bold → (Probe Condensed, Bold)`.

### What it decides today

- **ID1** drops `Italic` (so Bold and Bold Italic share a family, the RIBBI link), but keeps `Oblique`, `Cursive`,
  `Backslanted` and the other slopes in the family name. So "Probe Cursive" becomes its own family.
- **ID1 and ID4 drop `Regular` and `Roman`**; ID17 keeps `Regular` and `Roman`.
- **ID17 falls back to `Regular`** when empty.
- **Word order is whatever the filename says** (`Bold Condensed` stays `Bold Condensed`); reordering is the filename tools' job.

### Questions

**Q7. Only Italic is dropped from the family name.** Oblique, Cursive and the others stay and form their own family. (a) keep,
(b) also drop Oblique, (c) your rule. *This matches your Cursive rule (a slope after the hyphen, but a separate family
once it reaches ID1).*

**Q8. ID17 for a regular italic.** Today `Regular` + `Italic` gives "Regular Italic" but an Italic-only file gives "Italic".
(a) always "Italic", (b) keep as is, (c) always "Regular Italic". *Most families name it "Italic"; (a) would make the two
cases agree.*

**Q9. ID17 keeps "Regular" in the middle** ("Wide Regular Backslanted"). (a) drop it when other words are present
("Wide Backslanted"), (b) keep.

**Q10. Word order.** Names keep the filename's order. (a) keep, and leave ordering to the filename tools, (b) also order words in
names (width, weight, slope).

---

## Decided (2026-11-20)

These are the author's house conventions, not rules of OpenType: there is no hard rule for font naming, and these choices exist to
add consistency where there is little. The docsite should say so.

| # | Decision |
|---|---|
| Q1 | **One source of truth** for slope, width and weight terms. Regexes derive from the dictionary; tools import it; tests stop drift. |
| Q2 | **No closed list of optical-size words.** There are too many possible names to maintain. Optical size is recognized by position in the name (`Family {Optical Size} - {Width} {Weight} {Slope}`), not by vocabulary. |
| Q3 | **`Cursive` is a slope** after the hyphen, in every tool. `Kursiv` stays; other non-English terms are added as they occur. |
| Q4 | **Weight compounds are one word**: `SemiBold → Semibold`, `ExtraLight → Extralight`. **Width and other compounds are joined with no space and keep their capitals**: `Semi Condensed → SemiCondensed`. Example: `Ultra Condensed SemiBold → UltraCondensed Semibold`. |
| Q5 | *(superseded, see Revised decisions)* **ID1/ID4 drop only `Regular` and `Roman`.** The family-relative "regular equivalent" (Plain, Normal, Book, Light, Medium, Text when there is no Regular) is a long-standing convention that is hard to maintain; to be reconsidered (see follow-ups). |
| Q6 | **`Text` is context-sensitive**: an optical size when it appears with a weight word (or beside an `opsz` axis plus a weight axis); a weight name only when it is the only style word. The unused STAT "elidable" lists go away. |
| Q7 | **The RIBBI model**: ID2 is only Regular, Italic, Bold or Bold Italic. Bold and Bold Italic are the stand-alone pair, used only for the family's bold weight. ID1 may be more explicit; ID4 is the full name. Every other weight is named in ID1, and ID2 says only whether it is the Regular or the Italic of that pair. Non-Italic slopes (Oblique, Cursive…) stay in ID1 as naming. |
| Q8 | **ID17 keeps `Regular`**: a regular italic is `Regular Italic`, never plain `Italic`, so it can't be mistaken for another style (for example in a variable font). |
| Q9 | **ID17 keeps `Regular` in the middle** ("Wide Regular Backslanted"), and adds it when there is no weight word ("Wide Regular Italic"). |
| Q10 | **Order is `Family {Optical Size} - {Width} {Weight} {Slope}`.** The filename tools put names in that order; the name builders keep the order they are given. |

## What the real replacers do today (`fontnameid 1/2/4/16/17 -fp`, synthetic family "Probe")

| File | ID1 | ID2 | ID4 | ID17 |
|---|---|---|---|---|
| Probe-Regular | Probe | Regular | Probe | Regular |
| Probe-Italic | Probe | Italic | Probe Italic | **Italic** (Q8 wants `Regular Italic`) |
| Probe-Bold | Probe | Bold | Probe Bold | Bold |
| Probe-BoldItalic | Probe | Bold Italic | Probe Bold Italic | Bold Italic |
| Probe-Light | Probe Light | Regular | Probe Light | Light |
| Probe-LightItalic | Probe Light | Italic | Probe Light Italic | Light Italic |
| Probe-Black | Probe Black | Regular | Probe Black | Black |
| Probe-Book | Probe Book | Regular | Probe Book | Book |

The RIBBI model in Q7 is what happens for these. The filenames below are where the compound rule (Q4) is missing:

| File | ID1 | ID4 | ID17 | Problem |
|---|---|---|---|---|
| Probe-SemiBold | **Probe Semi** | Probe Semi Bold | Semi Bold | `Semi` and `Bold` are split, then `Bold` is treated as the RIBBI bold and dropped from ID1 |
| Probe-ExtraBold | **Probe Extra** | Probe Extra Bold | Extra Bold | same |
| Probe-DemiBold | **Probe Demi** | Probe Demi Bold | Demi Bold | same |
| Probe-ExtraLight | **Probe Extra** | **Probe Extra** | Extra Light | `Light` is taken as the family's "regular equivalent" and dropped, leaving `Extra` |
| Probe-CondensedSemiBold | **Probe Condensed Semi** | Probe Condensed Semi Bold | Condensed Semi Bold | same as SemiBold |
| Probe-UltraCondensedSemiBold | **Probe Ultra Condensed Semi** | … | Ultra Condensed Semi Bold | same |
| Probe-Semibold (one word) | Probe Semibold | Probe Semibold | Semibold | correct, and what Q4 asks for |

The cause is one step: the filename parser splits PascalCase into separate words (`SemiBold → Semi Bold`) before the weight is
identified. Treating `modifier + weight` as one token (Q4) fixes the truncated ID1, the lost `Light` and the spelling together.

## Implementation list (derived from the answers)

Each item gets a test first. Items are ordered by how much they fix.

1. **Weight compounds as one token** (Q4) in `core_filename_parts_parser` and the name builders. Width and other compounds
   join with no space and keep capitals. Fixes the truncated ID1/ID4 above.
2. **ID17 always carries a weight** (Q8, Q9): `Italic → Regular Italic`, `Wide Italic → Wide Regular Italic`.
3. **One vocabulary** (Q1, Q3): regexes derived from `SLOPE_BASES`; `reorder-slopes`, `regular` and the rest import it;
   `Cursive`/`Kursiv` in `STYLE_WORDS`.
4. **Optical sizes by position** (Q2): remove the closed list from the shared vocabulary; decide how `reorder-optical` finds them.
5. **`Text` by context** (Q6); delete the unused STAT lists.
6. **Regular equivalent** (Q5): redesign, see follow-ups.
7. **Docs**: the RIBBI model, the house order, the compound rules, written as the author's conventions.

## Revised decisions (2026-11-20, after F3): the "regular equivalent" convention is retired

This supersedes Q5 and the F3 reading. The author's reasons: the convention was built for FontExplorerX (a font with no weight
word is listed first and used as the default preview). It is not honest naming, and it matters less every year.

1. **Weight names always appear in filenames.** A single-weight file with no hyphen gets `-Regular`; `Font-Italic` gets the
   weight too (`Font-RegularItalic`). The tools keep doing this.
2. **ID1 drops only `Regular`, `Italic`, `Bold` and `Bold Italic`** (the RIBBI words). Regular equivalents (Book, Normal, Plain,
   Medium, Light, Text…) **stay in ID1, whether or not a Regular exists in the family.**
3. **ID4 gets `Regular` and its equivalents back.** The aggressive removal of `Regular` from ID4 ends.
4. **ID17 is unchanged** (it always kept `Regular`).
5. **`Variable` stays in ID1.** It is currently stripped.
6. **The family-relative "regular equivalent" detection goes away**: no nearest-neighbor pick, no `--regular-synonyms` modes
   (`regular_only`, `conservative`, `loose`).

### What changes (spec, not yet built) for family "Probe"

| File | ID1 today → new | ID4 today → new |
|---|---|---|
| Probe-Regular | Probe → Probe | Probe → **Probe Regular** |
| Probe-RegularItalic | Probe → Probe | Probe Italic → **Probe Regular Italic** |
| Probe-Bold / Probe-BoldItalic | Probe → Probe | Probe Bold / Probe Bold Italic → unchanged |
| Probe-Light (family has a Regular) | Probe Light → Probe Light | Probe Light → Probe Light |
| Probe-Light (family has **no** Regular) | Probe → **Probe Light** | Probe → **Probe Light** |
| Probe-Book | Probe Book → Probe Book | Probe Book → Probe Book |
| Probe-Roman (standalone) | Probe → **Probe Roman** | Probe → **Probe Roman** |
| Probe-Roman + Probe-Italic (a pair) | rename to Probe-Regular / Probe-RegularItalic first | then as the Regular rows |
| Variable file (upright or italic) | Probe → **Probe Variable** | unchanged |

**What a re-run does to a collection already processed.** IDs 1 and 4 change for: every Regular font (ID4 gains `Regular`),
families that relied on the nearest-neighbor rule (the "regular" font gets its weight word back), Roman files, and variable
fonts (ID1 gains `Variable`). ID2, ID3, ID6 and ID17 don't change. `fontrenamer -N full` (which uses ID4) will start producing
`ProbeRegular` instead of `Probe` until you pick another stem, and `-N legacy` (ID1+ID2) is unaffected.

### Answers

| # | Answer |
|---|---|
| C1 | **Yes: ID4 is `Probe Regular Italic`** (Regular goes back in). This departs from the original "Family + Style" idea, where ID2 is just `Italic`, but it matches ID17 and the `-RegularItalic` filename. |
| C2 | **`Roman` is a style (upright), not a weight.** If the font is standalone, or the family has no Italic files, `Roman` stays (`Probe Roman`). If it is half of a pair with an Italic, `Roman` becomes `Regular` and the italic is `Regular Italic` (never `Roman Italic`). A `Roman` inside a family name (a very upright or serif style) is part of the name and untouched. |
| C3 | **Purge `--regular-synonyms`** and the machinery behind it. Anyone else using the scripts will see bigger changes than a synonym difference, so no deprecation period. |
| C4 | **`Variable` in ID1 is `Probe Variable`** for the upright and the italic variable file. The rest of the variable policy is area 5. |

### Where the Roman pairing rule lives (my recommendation)

The rule needs family context ("does this family have an Italic?"). Put it in **one place, the filename step**: `filenametools regular`
turns `Probe-Roman` into `Probe-Regular` (and `Probe-Italic` into `Probe-RegularItalic`) when the family has both, the same
way it already adds a missing `Regular`. The name builders then treat `Roman` as an ordinary style word. That matches how you
already work (filenames carry the weight, and the names follow the filenames) and keeps the builders free of family lookups.
The cost: names are only right once the filenames are.

## Follow-up answers (2026-11-20)

| # | Answer | What it means |
|---|---|---|
| F1 | **`Smallcaps`** (no strong preference; reads clearer than `SmallCaps`). | The dictionary keeps `Smallcaps` and `ItalicSmallCaps → SmallcapsItalic`. The Q4 "keep capitals" rule has this one exception, and the docs say so. |
| F2 | **A word list supplied at the time of use** (`-F "Display,Text,Sans"`), moving those words before or after the family name depending on the options. A saved preference list is an advanced extra: an empty list that ships with the tool and that you can fill in. | No built-in optical words. See "F2 finding" below. |
| F3 | The convention comes from **FontExplorerX**, which lists a font with no weight word first in its family and uses it as the default preview weight. The tools were built around that. Newer apps and variable fonts are making it matter less. | It is a listing and preview convention, not a naming standard. See "F3 reading" below. |

**F2 finding.** `filenametools reorder-replace` already works this way: `--prehyphen TERM` moves a term before the hyphen and
`--posthyphen TERM` moves it after, repeatable and case-sensitive. It has no comma list and no saved list.
`reorder-optical` still carries its own 17 built-in words (plus `--add-optical`). Proposed shape:

- Both commands take the words the same way: repeatable `--prehyphen` / `--posthyphen`, plus a comma list (`-F "Display,Text,Sans"`).
- `reorder-optical` ships with **no** built-in words. It reads an optional preference list (an empty file you can fill in, for
  example `optical-terms.txt` in the tool's config folder) and anything you pass with `-F`. Same engine as `reorder-replace`, so
  there is one implementation, not two.

**F3 reading (superseded: the convention is retired, see above).** Keep the convention, but make it explicit and stable instead of name-guessing:

- Only when a family has no `Regular` or `Roman`, and for **exactly one font**: the one whose weight class is nearest 400. Its
  weight word is left out of ID1/ID4, so apps like FontExplorerX list it first.
- The name list (Plain, Normal, Book, Light, Medium, Text) breaks ties; it is no longer matched against pieces of a compound, so
  `ExtraLight` can't lose `Light`.
- A switch to turn it off for apps that don't need it, and a note in the docs saying why it exists. Default stays on until you
  say otherwise.

## Still open

**F4. Variable fonts.** You called the variable-font policies "not great". That is its own area (5) in the walkthrough.

## Build order

Each stage: tests first (showing the current behavior fail), then the change, then the old-versus-new comparison so only
the intended names move. FontCore and FontNameID get a minor version bump (0.3.0) and a changelog entry that says plainly
that names change.

1. **Weight compounds as one token** (Q4) and `Smallcaps`: fixes `Probe Semi`, `Probe Extra`, and the `Light` lost from `ExtraLight`.
2. **Retire the regular-equivalent machinery** (Q5 and F3 revised, C3). ID1 keeps equivalents and `Variable`; ID4 gets `Regular` and
   `Regular Italic`; ID17 always carries a weight. Removes `--regular-synonyms`.
3. **One vocabulary** (Q1, Q3): derived regexes, shared lists, `Cursive` everywhere; no optical list (Q2); `Text` by context (Q6).
4. **Filename tools**: `regular` adds `-Regular` / `-RegularItalic` and applies the Roman pairing rule; `reorder-optical` and
   `reorder-replace` take `-F "Display,Text,Sans"`, with an empty preference list.
5. **Docs**: the house conventions, the RIBBI model, and the compound rules.

## Q7 revisited: ID2 from the font, no slope vocabulary (2026-11-20)

Names (ID1, ID4, ID17) come from the filename and carry no slope vocabulary. ID2 is one of Regular, Italic, Bold, Bold Italic,
decided by three checks in this order: **name, flag, angle.**

- **ID1 drops only the exact words Regular, Italic and Bold.** Everything else (Oblique, Cursive, Backslanted, Reverse...) is an
  ordinary style word and stays. ID1 + ID2 stay unique without a slope list.
- **Bold:** the word `Bold` in the style (the same word ID1 drops). `usWeightClass` is not trusted (it is not always 700). The
  bold flag confirms it, and decides only when the style has no weight word at all.
- **Italic:** the word `Italic` in the style, then the italic flag, then the **italic angle**. The angle is the most accurate
  check *when FontFixer has run first*: a measured angle with `|angle| >= 2` degrees is slanted (forward or back), anything inside
  that zone is upright. FontFixer already measures the angle from the stem glyphs and uses the same 2 degree floor.
- **No Italic is appended** unless it is in the filename. Variable fonts may need their own approach (area 5).

### Settled (2026-11-20)

1. **Italic in either direction is Italic.** ID2 is Italic when the name says `Italic` **or** the measured angle is outside the zone
   (forward or back slant). Names never change; ID2 and the flags are what get corrected, so machines see a slanted face
   as Italic. A name that says Italic is never demoted by a near-zero angle (the tool warns instead); the angle only adds.
2. **Italic is the bit machines read; Oblique is not required.** CSS and browsers register Italic. Slanted faces get the ITALIC
   bit (`fsSelection` bit 0 and `macStyle` italic). The OBLIQUE bit is optional and no longer validated. Decisions about these
   fields are judged by how a web page would read the font.
3. **FontFixer measures the angle for every font, but its flags only follow labels.** Tested on synthetic fonts (all named
   `Regular` unless noted):

   | Font | angle before -> after FontFixer | fsSelection ITALIC | macStyle italic |
   |---|---|---|---|
   | upright | 0 -> 0 | 0 | 0 |
   | slanted 12 degrees, named Regular | 0 -> -12.02 | **0** | **0** |
   | back slant -12 degrees, named Regular | 0 -> +12.02 | **0** | **0** |
   | slanted 12 degrees, named Oblique | 0 -> -12.02 | **0** (OBLIQUE set) | 1 |
   | upright geometry, named Italic | 0 -> 0 | 1 | 1 |

   So the angle is measured from the glyphs everywhere, as you expected. The gap is the flags: a slanted face named Regular
   gets a correct `italicAngle` but no ITALIC bit, and an Oblique face gets `macStyle` italic but not `fsSelection` ITALIC, which
   disagree with each other. FontFixer's style flags should follow label **or** angle: ITALIC set when the name says Italic or
   `|angle| >= 2`.
4. **Bold:** the word `Bold` (the same word ID1 drops); the bold flag confirms it, and decides only when the style has no weight
   word. `usWeightClass` is not trusted.

### Follow-ups this creates

- **FontCore:** one shared angle measurement and the 2 degree floor (moved out of FontFixer), used by both tools.
- **FontFixer:** ITALIC and `macStyle` italic follow the **label** (superseded 2026-11-21: the angle no longer sets Italic for an upright-named font, see below). A FontFixer release.
- **Order of tools:** FontFixer (angle and flags) -> fontnameid (names, ID2) -> FontFixer again to verify -> ebrium.

## Reverse Italic and missing weights (2026-11-21)

- **Reverse Italic:** `Black Reverse Italic` gives ID1 `Probe Black Reverse`. Reverse is a slope name in its own right and the
  designer may intend it without Italic, so ID1 drops only the exact word `Italic`. ID4 and ID17 keep `Reverse Italic` whole. (Settled.)
- **A missing Regular is accounted for when possible; a missing Italic is not.** `Regular` is a weight, so it keeps the weight
  scheme continuous even when it is the only weight. `Italic` is never appended.

### Proposed (revised 2026-11-21): where a missing Regular goes

Evidence: the Bitcount Grid family names its fonts `Bitcount Grid Double Regular Circle Italic`, `... Regular Line Square Italic`,
`... Regular Plus Italic`. The weight sits right after the family and width, **before** the bespoke modifiers (Circle, Line,
Square, Plus) and the slope. A rule that puts Regular next to the slope would get all five wrong.

Decision tree (no slope list, no slanted signal needed):

1. The style already has a weight word: leave it.
2. The style is empty: `Regular`.
3. Otherwise insert `Regular` after any leading **width** words (a bounded list), or at the start: `Circle Italic` -> `Regular Circle Italic`,
   `Condensed Oblique` -> `Condensed Regular Oblique`, `Reverse Italic` -> `Regular Reverse Italic`, `Condensed` -> `Condensed Regular`.
4. With family context (the filename step), the weight position seen in the siblings wins over this default.
5. When Regular is added with no family pattern to confirm it, warn and say how to override. A `usWeightClass` far from 400 is a
   second reason to warn (a hint only).

Single-font runs are safe: nothing is ever removed or rewritten on the strength of a pattern (the old "regular equivalent" rule dropped
Book and Light when a font was run alone). A pattern may only *place an addition*.

### Overrides (so a special case is never stuck)

Applies to the replacers that add a weight (4, 17, and `batch`):

- `--weight-word WORD`: add WORD instead of `Regular`; `--weight-word none` adds nothing.
- `--weight-position {after-width,start,end}`: where it goes (default `after-width`).
- Every warning names the flag that changes it. `-str` (exact text) remains the last resort.
- Standing choices can live in a preferences file later (same mechanism as the optical word list); a flag on the command line wins.

## Name wins over the angle (2026-11-21)

Tested on 1,539 FontVault fonts: 223 had a slant of 2 degrees or more with a plain upright name (`RoleSerifBanner-Regular` at 6.2).
Comparing the angle across each family showed no reliable pattern (only 5 of 59 families had slope-named files that were clearly
steeper), and most were scripts or slanted-by-design families.

- **Italic is a linked alternative to a Regular.** A slanted font with nothing to link to is not an Italic; marking it Italic is an
  assumption, so a script keeps Regular. Where an old tool had set Italic from the angle alone, the Italic setting is treated as wrong
  and goes back to Regular (59 of 1,539 in the vault sample).
- **ID2 rule now:** the word `Italic` in the style makes Italic. The angle (>= 2 degrees) adds Italic only when the style is empty
  or names a slope (Oblique, Slanted, Backslant, Cursive, Inclined). A style of weight, width, `Regular` or a bespoke word stays upright
  and the tool prints a note. The flags decide only when the style says nothing.
- **Flags** (fsSelection, macStyle) follow ID2, so they stay in step with it.
- **SemiMono:** modifier + Mono joins like the width compounds, in the family and the style (`Semi Mono` -> `SemiMono`).
- Known splits such as `S Sm` (ScreenSmart) and `3 D` are caught by the NameID find-and-replace script, not by the naming rules.
