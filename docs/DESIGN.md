# Connected Earth: design rules

One place for the UX rules, so the app feels like one app. Read this before any UI work and update it when a rule changes. If a screen needs to break a rule, change the rule here first.

## Principles
1. **Consistency over novelty.** New designs are welcome, but the same thing looks and behaves the same everywhere.
2. **Mobile and desktop stay in sync.** Only layout-dependent parts differ; every improvement applies to both.
3. **Self-explanatory.** No "tap this" hints, no jargon. If it needs a hint, redesign it.
4. **Mobile screen space is premium.** Prefer one line over a card, and nothing permanent that covers content.
5. **Avoid buttons.** Prefer plain links, and tappable cards or rows with a chevron.
6. **Photos, not icons,** wherever a photo exists. Icons only as the fallback while a photo loads or is missing.

## Patterns (one definition each)
- **Back.** One link: accent colour, 16px / 600, "‹ " plus the name of where it goes ("‹ Map", "‹ Journey", "‹ Place"). 44px tall, top-left of the content on every screen: 24px from the edge on a phone; on desktop the edge of the page column (journeys, places) or of the full-width graph (explore). Over the graph it gets a faint backdrop. Never an arrow-only icon, never a ✕. Code: `.jback` (pages) and `#pbk` (explore); both must look identical (a test checks it).
- **Close (✕).** Only for dismissing something that sits on top of a screen (the species sheet). It never navigates.
- **Section headings.** Small mono caps label (`.jp h3`). Same on every page.
- **Story blocks.** "The story" is plain text with a bold lead-in; "Why it matters" has the accent bar (`.jwhy`). Journeys and places use the same blocks.
- **Photo rows.** Horizontal rows of small photo cards: photo, name, at most one small line below. Badges go under the name, never on the photo.
- **Tappable rows.** Photo, title, one muted line, chevron on the right (`.jend`, `.pj`).
- **Fonts.** Display font for names and titles, body font for text, mono for small labels. Sizes: page title 24, row title 16, body 16, card name 12–13, label 11, fine print 12.
- **Credits.** Every photo has its author and licence reachable on the screen that shows it.

## Navigation shape
Map → Place page → Explore (graph) → species sheet. Back always goes one step up and says where. Journeys sit beside places and link both ways.
- Explore with nothing selected is just the graph. The sheet or side panel appears only for a selected species.

## How this is enforced
- `tests/consistency.test.mjs` checks that every screen has exactly one back link with the same look and position.
- When adding a screen, reuse the pattern's existing class rather than writing new CSS.
