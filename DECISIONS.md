# FontCore decisions walkthrough

Working draft, 2026-11-20. Each area lists what the code decides today (with real outputs), then the questions that need
your call. Answer by number ("Q1 yes, Q2 b, Q4 a"). Your answers become the "How it decides" page on the docsite, so
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
