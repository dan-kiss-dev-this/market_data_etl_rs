# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some Oxlint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the Oxlint configuration

If you are developing a production application, we recommend enabling type-aware lint rules by installing `oxlint-tsgolint` and editing `.oxlintrc.json`:

```json
{
  "$schema": "./node_modules/oxlint/configuration_schema.json",
  "plugins": ["react", "typescript", "oxc"],
  "options": {
    "typeAware": true
  },
  "rules": {
    "react/rules-of-hooks": "error",
    "react/only-export-components": ["warn", { "allowConstantExport": true }]
  }
}
```

See the [Oxlint rules documentation](https://oxc.rs/docs/guide/usage/linter/rules) for the full list of rules and categories.

## Responsive breakpoints

Width breakpoints live in `src/index.css`:

| Breakpoint | What changes |
|---|---|
| `max-width: 960px` | `.layout` collapses to one column, so the table stacks above the chart. `App.tsx` also moves the range picker above the chart at this width. |
| `max-width: 480px` | The `.name` column is capped at `10ch`, and percentages show as whole numbers (`.pct-whole`) instead of full precision (`.pct-full`). |

The 960px breakpoint is duplicated in JS as `STACKED` in `src/useMediaQuery.ts`. If you change it, update both places. `src/useMediaQuery.test.ts` fails if they drift apart.

`src/App.css` contains `max-width: 1024px` rules, but nothing imports that file, so they have no effect.
