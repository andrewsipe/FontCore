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
| Q5 | **ID1/ID4 drop only `Regular` and `Roman`.** The family-relative "regular equivalent" (Plain, Normal, Book, Light, Medium, Text when there is no Regular) is a long-standing convention that is hard to maintain; to be reconsidered (see follow-ups). |
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

## Follow-up questions raised by the answers

**F1. `SmallCaps`.** The dictionary spells it `Smallcaps` (and `ItalicSmallCaps → SmallcapsItalic`). Your Q4 rule says
non-weight compounds keep their capitals, which would give `SmallCaps`. Which do you want?

**F2. Optical sizes without a list.** `filenametools reorder-optical` works from a list of 17 words today. With position as the rule
(the term between the family and the hyphen), do you want (a) the tool to take the term by position and move it, (b) a list
you can extend in a file, or (c) retire the tool?

**F3. The regular-equivalent convention.** When a family has no Regular, the tools pick the nearest of Plain, Normal, Book, Light,
Medium, Text and drop its word from ID1/ID4. Today that is name-based and it misfires inside compounds (`ExtraLight` loses
`Light`). A steadier signal is the font's own weight class: the font nearest 400 is the family's regular. Do you want the
redesign to use (a) weight class first, with the name list only as a tie-break, (b) the name list as now, fixed to ignore
compound pieces, or (c) drop the convention and name every non-Regular/Roman style explicitly?

**F4. Variable fonts.** You called the variable-font policies "not great". That is its own area (5) in the walkthrough.
