# Annotation Policy

Version: `1.0`

Status: finalized for Stage 1 after manual QA of all 100 raw records and all 90
retained records.

## Labels

- `PERSON`: a named person, including given names and surnames.
- `ORGANIZATION`: a named company or institution.
- `LOCATION`: a named place such as a city, country, region, street, landmark,
  building, or geographic area.
- `TIMEDATE`: an expression that places something on a timeline, including
  dates, clock times, ages, frequencies, and durations used as time.
- `PRODUCT`: a named commercial product, device, software item, or branded good.
- `WORKOFART`: a named creative or published work such as a book, film, song,
  article, report, or titled publication.
- `JOB`: an occupational title or formal work role when it functions as such in
  the sentence.
- `AMOUNT`: a measurable or countable quantity that is not a time or date
  expression.

## Fixed Baseline Labeling Rules

These rules are fixed. Corrections follow these rules together with the extra
policy rules below.

1. A labeled mention should cover the entity itself, not the surrounding
   grammar.
   - Correct: `She visited <LOCATION>Paris</LOCATION> yesterday.`
   - Incorrect: labeling `visited Paris yesterday` as one span.
2. Articles, prepositions, conjunctions, and other function words should stay
   outside the span unless they are truly part of the proper name.
   - Correct: `He works at <ORGANIZATION>Google</ORGANIZATION>.`
   - `<ORGANIZATION>The New York Times</ORGANIZATION>` keeps `The` because it
     belongs to the established name.
3. Bare type words and category descriptors should not be labeled on their own.
   Examples include `person`, `company`, `organization`, `team`, `hospital`,
   `city`, `product`, `book`, and `quantity`.
   - `The company hired 200 people.` leaves `company` unlabeled.
   - `She joined <ORGANIZATION>Acme Corp</ORGANIZATION>.` labels the named
     organization.
4. A multi-word name should be one span when it forms one real named entity;
   separate entities should be labeled separately.
   - `<PERSON>Barack Obama</PERSON>` is one span.
   - `<PERSON>Barack</PERSON> and <PERSON>Michelle</PERSON>` are two spans.
5. Coordinated names should be separate spans unless the conjunction is part of
   one established name.
   - `<ORGANIZATION>Google</ORGANIZATION> and
     <ORGANIZATION>Microsoft</ORGANIZATION>` are separate.
   - `<ORGANIZATION>Johnson & Johnson</ORGANIZATION>` stays together.
6. Ordinary punctuation and stray whitespace should stay outside spans unless
   the punctuation belongs to the name or abbreviation.
   - `He moved to <LOCATION>Berlin</LOCATION>.`
   - `<ORGANIZATION>AT&T</ORGANIZATION>` keeps `&`.
7. Possessive markers should stay outside the span unless the full possessive
   form is the name.
   - `<PERSON>Maria</PERSON>'s laptop`.
8. Labels should follow context, not surface form alone.
   - `She works at <ORGANIZATION>Cambridge University</ORGANIZATION>.`
   - `The conference was held in <LOCATION>Cambridge</LOCATION>.`
9. Quantities used as time should be labeled `TIMEDATE`, not `AMOUNT`.
   - `She bought <AMOUNT>50</AMOUNT> tickets.`
   - `The train arrives in <TIMEDATE>50 minutes</TIMEDATE>.`

## Additional Policy Rules

### A1. Temporal specificity, ages, and vague temporal adverbs

Calendar dates, clock times, seasons, durations, frequencies, ages, and
relative/deictic expressions with a concrete temporal reference are labeled
`TIMEDATE`. General adverbs that do not identify a time point or interval, such
as `ever`, `never`, `always`, `again`, `yet`, `just`, `initially`, and
`already`, are not labeled. Interrogative placeholders such as `when` and
`how long` ask for a temporal value but do not provide one, so they are not
labeled.

- Record 45: `19-year-old` is an age and is labeled `TIMEDATE`.
- Record 72: `Now` and `three years later` place events on the timeline.
- Record 10: standalone `ever`, `never`, and `before` are not labeled.
- Record 58: `How long` asks for a duration but does not express one.

Reason: this prevents general discourse adverbs and question placeholders from
inflating the time class while retaining real temporal references.

### A2. Core quantity spans and unit boundaries

An `AMOUNT` span includes the numeric/count component, ranges, and scale words:
`3.5`, `3-4`, `1.2 million`, `half`, `both`, and `thousands`. Currency symbols
and codes, measurement units, counted nouns, and approximation modifiers such
as `about`, `over`, and `at least` stay outside.

Digits alone are not sufficient for `AMOUNT`. A numeric string used as a code,
identifier, model name, or shared value is not labeled unless it expresses a
measurable or countable quantity.

For `TIMEDATE` durations and ages, the time unit determines the class and stays
inside the span (`15 minutes`, `19-year-old`), while external modifiers such as
`about` and `up to` stay outside.

- Record 33: `about $ <AMOUNT>784,700.78</AMOUNT>`.
- Record 85: `<AMOUNT>6</AMOUNT>ft` and
  `<TIMEDATE>two months ago</TIMEDATE>`.
- Record 9: `less than <TIMEDATE>six hours</TIMEDATE> a night`.
- Record 29: `3339` and `483` are numeric identifiers, not quantities.

Reason: this applies the baseline minimal-span principle consistently and
prevents identifiers from being learned as quantities.

### A3. Person names, nicknames, and usernames

Adjacent given and family names referring to one person form one `PERSON` span.
Titles and possessive markers stay outside. A nickname inside a full name may
remain inside the same span, including its quotation marks. A username or
explicitly introduced nickname is labeled only when the context presents it as
a real person reference. Structural dialogue placeholders are not labeled.

- Record 1: `<PERSON>Manny Pacquiao</PERSON>`, not two separate spans.
- Record 73: `<PERSON>Norville "Shaggy" Rogers</PERSON>`.
- Record 91: `Person1` and `Person2` are structural placeholders.

Reason: this extends the baseline multi-word name rule consistently to
nicknames and usernames.

### A4. Product, organization, and published work

A named application, game, platform, medicine, font, device, or branded good is
`PRODUCT` when the context refers to the artifact or service. The company that
operates or manufactures it is `ORGANIZATION`. A film, song, book, article,
report, or other publication title is `WORKOFART`.

- Record 13: Discord is `PRODUCT` in the context `on Discord`.
- Record 26: Garamond is a font and is `PRODUCT`.
- Record 99: `Project Performance Audit Report` is `WORKOFART`.

Reason: this resolves recurring semantic confusion while following the
baseline context rule.

### A5. Occupations versus departments and activities

`JOB` is used only for an occupational title or formal work role in the
sentence. A department, team, sector, field, activity, or generic
organizational function is not `JOB`. A specifically named department may be
`ORGANIZATION`.

- Record 66: `Business Intelligence Director` is `JOB`; `market analysis
  division` and `analytics team` are unlabeled.
- Record 77: `Geriatric Medicine Department` is `ORGANIZATION`, not `JOB`.
- Record 80: `psychology` and `military` are not occupations.

Reason: this prevents topics and organizational units from being learned as
occupations.

### A6. Locations, establishments, and companies

Named companies, sports teams, restaurants, casinos, and establishments remain
`ORGANIZATION` even when someone visits them. Geographic areas, streets,
addresses, landmarks, and physical facilities are `LOCATION` when the context
emphasizes the place. The same surface form may therefore receive different
labels in different contexts.

- Record 65: Joyride Taco House is a restaurant and is `ORGANIZATION`.
- Record 69: McDonald's is `ORGANIZATION` when referring to the company, but
  may be `LOCATION` when the text explicitly refers to being inside a physical
  restaurant.
- Record 56: West Wing Studio is `LOCATION` when described as a physical
  facility.

Reason: this makes the baseline context rule explicit for establishment/place
confusion.

### A7. No nested labels inside work titles

The dataset uses flat, non-overlapping spans. If another entity name appears
inside a complete work title, the whole title is labeled `WORKOFART` and no
nested span is created.

- Record 87:
  `<WORKOFART>Diversity Rates in Mercer County, West Virginia Evaluation
  Essay</WORKOFART>` is one span.

Reason: this keeps annotations compatible with flat BIO token classification
and removes conflicting overlaps.

### A8. Proposed names

An expression explicitly proposed as a name is labeled according to the
intended entity type even if the object has not yet been released.

- Record 2: proposed publication titles are `WORKOFART`.
- Record 96: proposed pet-collar product names are `PRODUCT`.

Reason: the text explicitly presents these expressions as names; release status
does not change the naming context.

### A9. Record-removal quality threshold

A record is removed only when severe OCR/encoding corruption, an unrelated
nonsensical word list, or truncation makes reliable annotation impossible.
Ordinary spelling and grammar errors are retained as real language variation.

- Record 61: severe OCR corruption prevents reliable span selection.
- Record 80: keyword spam and nonsensical lists dominate the text.
- Record 92: generated nonsense and mixed-language fragments dominate the
  record.

Reason: removal is reserved for objective quality failures likely to harm the
model, not used to avoid difficult annotation decisions.
