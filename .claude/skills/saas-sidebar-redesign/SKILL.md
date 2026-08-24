---
name: saas-sidebar-redesign
description: Design system and migration reference for converting the Vue 3 client's top-nav layout into a modern SaaS-style left sidebar with CSS custom-property design tokens. Use this skill when redesigning App.vue's navigation shell, introducing design tokens/CSS variables, or restyling any client/src view or component to match the sidebar-based SaaS look.
---

# SaaS Sidebar Redesign

This skill defines the **target design system** for converting the Factory Inventory Management client from its current horizontal top-nav layout into a modern SaaS-style interface with a left vertical sidebar, a CSS custom-property token system, and consistent spacing across every view. It is a reference document, not a to-do list — read it fully before touching any file, and re-read it before starting each new file in the migration.

## Mandatory Delegation Notice

> Per root `CLAUDE.md`: **ANY time you need to create or significantly modify a `.vue` file, you MUST delegate to the `vue-expert` subagent.**

This skill only documents *what* the target design looks like. It does not authorize direct `.vue` edits. Whoever invokes this skill must:
1. Delegate all `.vue` file changes to `vue-expert`.
2. Instruct `vue-expert` to read this `SKILL.md` in full before editing each file — not just once at the start of the task, but again before each file in the Migration Order below, since the token names and markup structure defined here must stay consistent across the whole migration.
3. Leave `server/` and API contracts (`client/src/api.js` request/response shapes) untouched — this is a presentation-layer-only redesign.

## Design Tokens: CSS Custom Properties

Add a single `:root` block at the top of `App.vue`'s existing global (unscoped) `<style>` block — no new file, no new import wiring in `main.js`. Every value below is taken directly from the current hardcoded literals in `App.vue`; nothing is invented, only centralized and named.

```css
:root {
  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;

  /* Surface & text */
  --color-bg-page: #f8fafc;
  --color-bg-surface: #ffffff;
  --color-text-heading: #0f172a;
  --color-text-body: #1e293b;
  --color-text-secondary: #475569;
  --color-text-tertiary: #334155;
  --color-text-muted: #64748b;

  /* Borders */
  --color-border: #e2e8f0;
  --color-border-subtle: #f1f5f9;
  --color-border-hover: #cbd5e1;

  /* Brand / primary */
  --color-primary: #2563eb;
  --color-primary-accent: #3b82f6;
  --color-primary-bg: #eff6ff;

  /* Semantic status */
  --color-success: #059669;
  --color-success-bg: #d1fae5;
  --color-success-text: #065f46;
  --color-warning: #ea580c;
  --color-warning-bg: #fed7aa;
  --color-warning-text: #92400e;
  --color-danger: #dc2626;
  --color-danger-bg: #fecaca;
  --color-danger-text: #991b1b;
  --color-info-bg: #dbeafe;
  --color-info-text: #1e40af;
  --color-neutral-bg: #e0e7ff;
  --color-neutral-text: #3730a3;

  /* Spacing scale (4px base) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.25rem;
  --space-6: 1.5rem;
  --space-8: 2rem;

  /* Radii */
  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 10px;

  /* Layout */
  --sidebar-width: 260px;
  --content-max-width: 1600px;
  --shadow-card: 0 4px 12px rgba(0, 0, 0, 0.06);
  --shadow-header: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
}
```

## Sidebar Layout Structure

Replace `App.vue`'s `.app` > `header.top-nav` + `main.main-content` structure with a flex row: `.app-shell` containing `aside.sidebar` and `.app-main`.

Key structural decision: `LanguageSwitcher` and `ProfileMenu` move into a `.sidebar-footer` at the bottom of the sidebar (not a separate top bar). This means nothing sits above `FilterBar` inside `.app-main` anymore, so `FilterBar.vue`'s sticky offset can go back to `top: 0` instead of the current hardcoded `top: 70px` (a magic number coupled to the old 70px-tall top nav — remove that coupling as part of this change).

```html
<div class="app-shell">
  <aside class="sidebar">
    <div class="sidebar-brand">
      <h1 class="sidebar-brand__title">{{ t('nav.companyName') }}</h1>
      <span class="sidebar-brand__subtitle">{{ t('nav.subtitle') }}</span>
    </div>

    <nav class="sidebar-nav">
      <router-link to="/" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/' }">
        <span class="sidebar-nav__icon" v-html="icons.overview"></span>
        <span class="sidebar-nav__label">{{ t('nav.overview') }}</span>
      </router-link>
      <router-link to="/inventory" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/inventory' }">
        <span class="sidebar-nav__icon" v-html="icons.inventory"></span>
        <span class="sidebar-nav__label">{{ t('nav.inventory') }}</span>
      </router-link>
      <router-link to="/orders" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/orders' }">
        <span class="sidebar-nav__icon" v-html="icons.orders"></span>
        <span class="sidebar-nav__label">{{ t('nav.orders') }}</span>
      </router-link>
      <router-link to="/spending" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/spending' }">
        <span class="sidebar-nav__icon" v-html="icons.spending"></span>
        <span class="sidebar-nav__label">{{ t('nav.finance') }}</span>
      </router-link>
      <router-link to="/demand" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/demand' }">
        <span class="sidebar-nav__icon" v-html="icons.demand"></span>
        <span class="sidebar-nav__label">{{ t('nav.demandForecast') }}</span>
      </router-link>
      <router-link to="/reports" class="sidebar-nav__item" :class="{ 'is-active': $route.path === '/reports' }">
        <span class="sidebar-nav__icon" v-html="icons.reports"></span>
        <span class="sidebar-nav__label">{{ t('nav.reports') }}</span>
      </router-link>
    </nav>

    <div class="sidebar-footer">
      <LanguageSwitcher />
      <ProfileMenu @show-profile-details="showProfileDetails = true" @show-tasks="showTasks = true" />
    </div>
  </aside>

  <div class="app-main">
    <FilterBar />
    <main class="main-content">
      <router-view />
    </main>
  </div>

  <ProfileDetailsModal :is-open="showProfileDetails" @close="showProfileDetails = false" />
  <TasksModal
    :is-open="showTasks"
    :tasks="tasks"
    @close="showTasks = false"
    @add-task="addTask"
    @delete-task="deleteTask"
    @toggle-task="toggleTask"
  />
</div>
```

Note: the global modals (`ProfileDetailsModal`, `TasksModal`) stay exactly where they are — siblings at the `.app-shell` root, outside both `.sidebar` and `.app-main`. No change needed there.

Companion CSS:

```css
.app-shell {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--color-bg-surface);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  height: 100vh;
  position: sticky;
  top: 0;
  overflow-y: auto;
}

.sidebar-brand {
  padding: var(--space-6) var(--space-5);
  border-bottom: 1px solid var(--color-border);
}

.sidebar-brand__title {
  font-size: 1.375rem;
  font-weight: 700;
  color: var(--color-text-heading);
  letter-spacing: -0.025em;
}

.sidebar-brand__subtitle {
  display: block;
  font-size: 0.813rem;
  color: var(--color-text-muted);
  font-weight: 400;
  margin-top: var(--space-1);
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
  padding: var(--space-4);
  flex: 1;
}

.sidebar-nav__item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  text-decoration: none;
  font-weight: 500;
  font-size: 0.938rem;
  transition: all 0.2s ease;
}

.sidebar-nav__item:hover {
  background: var(--color-border-subtle);
  color: var(--color-text-heading);
}

.sidebar-nav__item.is-active {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.sidebar-nav__icon svg {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

.sidebar-footer {
  border-top: 1px solid var(--color-border);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}

.app-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  max-width: var(--content-max-width);
  width: 100%;
  padding: var(--space-6) var(--space-8);
}
```

**`FilterBar.vue` fix required alongside this**: change `position: sticky; top: 70px;` to `position: sticky; top: 0;` — this is the one line coupling `FilterBar` to the old top-nav height.

## Icon Snippet Library

Keep the existing hand-inline-SVG convention — do **not** add an icon library dependency. Use a consistent 24×24 outline shell (`stroke="currentColor"`) for every sidebar item:

```html
<!-- overview -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12l8.954-8.955c.44-.439 1.152-.439 1.591 0L21.75 12M4.5 9.75v10.125c0 .621.504 1.125 1.125 1.125H9.75v-4.875c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21h4.125c.621 0 1.125-.504 1.125-1.125V9.75M8.25 21h8.25" /></svg>

<!-- inventory -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" /></svg>

<!-- orders -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 3h1.386c.51 0 .955.343 1.087.835l.383 1.437M7.5 14.25a3 3 0 00-3 3h15.75m-12.75-3h11.218c1.121-2.3 1.749-4.766 1.749-7.353 0-.322-.026-.638-.076-.947H5.106M7.5 14.25L5.106 5.997M7.5 14.25L5.106 5.997m5.394 12.253a.75.75 0 11-1.5 0 .75.75 0 011.5 0zm7.5 0a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" /></svg>

<!-- spending -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3M4.5 19.5h15a2.25 2.25 0 002.25-2.25V6.75A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25v10.5A2.25 2.25 0 004.5 19.5z" /></svg>

<!-- demand -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18l6.16-6.16a1.5 1.5 0 012.12 0l2.84 2.84a1.5 1.5 0 002.12 0L21.75 8.25M17.25 6h4.5v4.5" /></svg>

<!-- reports -->
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M9 4.5v15M15 4.5v15M4.5 9h15M4.5 15h15M3.75 4.5h16.5a1.125 1.125 0 011.125 1.125v13.75a1.125 1.125 0 01-1.125 1.125H3.75a1.125 1.125 0 01-1.125-1.125V5.625A1.125 1.125 0 013.75 4.5z" /></svg>
```

Treat this path data as a starting point, not pixel-gospel — verify visually via Playwright once implemented and adjust if any icon reads oddly at 20px. `backlog` is intentionally excluded from this set (see Key Reminders).

## Reusing Existing Global CSS Classes

`.page-header`, `.stats-grid` / `.stat-card` (+ `.warning`/`.success`/`.danger`/`.info` variants), `.card` / `.card-header` / `.card-title`, `table`/`thead`/`th`/`td`, `.badge` (+ all status variants), `.loading`, `.error` **must keep their exact class names and selectors** — every view (`Dashboard`, `Inventory`, `Orders`, `Spending`, `Demand`, `Reports`) depends on them today. This redesign only re-expresses their property *values* in terms of the tokens above — a substitution pass over the same selectors in `App.vue`'s global style block, not a rename or restructure. For example:

```css
/* before */
.card { background: white; border-radius: 10px; padding: 1.25rem; border: 1px solid #e2e8f0; margin-bottom: 1.25rem; }

/* after */
.card { background: var(--color-bg-surface); border-radius: var(--radius-lg); padding: var(--space-5); border: 1px solid var(--color-border); margin-bottom: var(--space-5); }
```

## Migration Order

Apply changes in this order — each step should be verified (start the app, click through) before moving to the next:

1. **`App.vue`** — token block + sidebar shell + i18n `Reports` fix (see Key Reminders). Establishes the shell everything else lives inside.
2. **`FilterBar.vue`** — sticky offset fix (`top: 70px` → `top: 0`).
3. **`Backlog.vue`** — smallest view, currently orphaned; forces the sidebar-inclusion decision (see Key Reminders) to be made concretely before moving on.
4. **`Orders.vue`**, then **`Inventory.vue`** — both already mostly reuse the global classes; for `Inventory.vue` also resolve its scoped-style duplication so it fully defers to the global primitives instead of re-declaring them.
5. **`Demand.vue`**, then **`Reports.vue`** — moderate custom styling.
6. **`Spending.vue`** — heavier bespoke layout.
7. **`Dashboard.vue`** — last. It has the hand-drawn SVG donut chart and bespoke KPI/progress-bar CSS, making it the highest-risk, most bespoke file. Tackle it once the token vocabulary and sidebar shell are already proven stable everywhere else.

## Key Reminders

- Fix the untranslated `"Reports"` nav label: `App.vue`'s top-nav template hardcodes the literal string `Reports` instead of using `t('nav.reports')`. Add a `reports` key to the `nav` block in both `client/src/locales/en.js` and `client/src/locales/ja.js` (confirmed missing from both today), then use `{{ t('nav.reports') }}` in the sidebar item. Do this while already touching `App.vue` — not as a separate pass.
- Decide on `Backlog.vue`: it exists in `client/src/views/` but is not registered in `main.js`'s router, so it's currently unreachable. Default recommendation is to **leave it out of the sidebar and the router** for this redesign — wiring up an orphan feature is a separate product decision. Flag the choice explicitly (in the PR/commit description) rather than silently deciding either way.
- Preserve the *behavior* of every global CSS class listed under "Reusing Existing Global CSS Classes" — tokenize their declared values, never rename or remove the selectors themselves.
- Do not touch `server/` or any API contract (`client/src/api.js` request/response shapes) — this is a pure presentation-layer change.
- Do not add `@media` queries, breakpoints, or a collapse/toggle affordance. The sidebar is fixed-width (`--sidebar-width`) and desktop-only, matching the app's current fully-desktop scope — there are zero `@media` queries anywhere in the codebase today, and this redesign does not change that.
- Have `vue-expert` re-read this `SKILL.md` before starting each file in the Migration Order above, not just once at the start of the whole task.
