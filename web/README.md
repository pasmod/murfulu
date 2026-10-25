# web

The Murfulu interface. Persian, right to left, mobile first.

The screens and the rules they follow are in
[docs/FRONTEND.md](../docs/FRONTEND.md). What is built and what is not is in
[docs/PLAN.md](../docs/PLAN.md), Phase 7.

```
src/styles/   the design system as tokens; nothing hard-codes a value
src/shell/    the frame: navigation, routing, the list of screens
src/text/     Persian and Latin together — the LTR island, numerals, terms
src/screens/  one module per screen
```

## Working on it

```
make web-install     # npm ci
npm --prefix web run dev
make web-check       # lint, types, tests
```

The dev server proxies `/api` to `MURFULU_API_URL`, default
`http://localhost:8000`. In the container nginx does the same. The app never
names a host.

## Three rules that are enforced by tests

- **Every value comes from a token.** A stylesheet may not write a colour, and
  may not name a token that `styles/tokens.css` does not define.
- **Logical properties only.** No `left` or `right`: a right-to-left layout
  built by mirroring breaks the first time a component is nested.
- **A Latin form is an island.** `dir="ltr"` *and* `unicode-bidi: isolate`, and
  never lower-cased — capitalisation carries grammar in Behnevis.
