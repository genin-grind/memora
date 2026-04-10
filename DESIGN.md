# MEMORA — Design System Reference
> **Source of truth** compiled from four Stitch projects: Login, My Organization, Source Explorer, and Decision Engine.
> This file governs the visual layer only. No backend logic, auth flow, or data handling should change.

---

## 0. Creative Philosophy: "The Digital Curator"

Memora's interface is built on **Quiet Authority**. It should feel like a high-end editorial journal crossed with a precision surgical tool — not a cluttered enterprise dashboard.

Core principles:
- **No borders.** Define regions through surface color shifts, not 1px strokes.
- **Tonal Layering.** Depth is created by stacking background tokens, not shadows.
- **Intentional Asymmetry.** Offset hero headers against structured data grids.
- **Breathing Room.** Whitespace is structural. Add padding before adding dividers.
- **No pure black, no generic blue.** Every color choice uses curated tokens.

---

## 1. Color Palettes (Per Page)

Each page has its own Stitch project with a distinct palette. All share the same **Manrope + Inter** typographic system.

---

### 1.1 Login Page — "The Nocturnal Architect" (Dark Mode)

| Token | Hex | Usage |
|---|---|---|
| `surface` / `background` | `#0A0E17` | Base layer — infinite floor |
| `surface-container-low` | `#0D1320` | Sidebar / footer background |
| `surface-container` | `#11192A` | Grouped section panels |
| `surface-container-high` | `#151F34` | Primary interactive cards |
| `surface-container-highest` | `#19253F` | Modals, popovers, active cards |
| `surface-container-lowest` | `#000000` | Recessed inputs |
| `primary` | `#C4C7C9` | Primary text / CTA background |
| `on-primary` | `#3D4142` | Text on primary buttons |
| `secondary` | `#8F9FB7` | Secondary labels, slate tones |
| `secondary-container` | `#2D3C51` | Secondary button background |
| `on-surface` | `#DDE5FF` | Primary text (no pure white) |
| `on-surface-variant` | `#9EABCB` | Secondary labels / descriptions |
| `outline` | `#697593` | Ghost border / focus ring |
| `outline-variant` | `#3B4863` | Ghost border fallback (@ 15% opacity) |
| `error` | `#EE7D77` | Error states |
| `tertiary` | `#F0F3FF` | Accent / highlight |
| `surface-variant` | `#19253F` | Glassmorphism base (@ 70% opacity) |

**Login-specific rules:**
- Background: deep navy `#0A0E17` — never pure black.
- Input fields: `surface-container-lowest` background (recessed look).
- Input focus: 1px `outline` (#697593) glow — no glowing blue.
- CTA button: `primary` (#C4C7C9) background with `on-primary` text, `border-radius: 9999px` (full pill).
- Cards: `xl` radius (1.5rem / 24px); inner elements use `md` (0.75rem / 12px).
- Glassmorphism for floating elements: `surface-variant` at 70% opacity + `backdrop-filter: blur(12px–20px)`.
- Hero CTA gradient: 135° from `primary` (#C4C7C9) to `primary-dim` (#B6B9BB).

---

### 1.2 My Organization Page — "The Editorial Intelligence Framework" (Light Mode)

| Token | Hex | Usage |
|---|---|---|
| `surface` / `background` | `#FCF8F9` | Base layer |
| `surface-container-low` | `#F6F3F4` | Panel / sidebar background |
| `surface-container` | `#F0EDEF` | Structural sections |
| `surface-container-lowest` | `#FFFFFF` | Interactive cards (lifted) |
| `surface-container-high` | `#EBE7EA` | Hover states |
| `surface-container-highest` | `#E5E1E5` | Input background |
| `primary` | `#2B5BB5` | Navigation, CTAs, accents |
| `primary-container` | `#D9E2FF` | Hero gradient end |
| `on-primary` | `#F7F7FF` | Text on primary |
| `secondary` | `#49636F` | Secondary elements |
| `secondary-container` | `#CBE7F5` | Tag/chip backgrounds |
| `on-secondary-container` | `#3C5561` | Tag/chip text |
| `tertiary` | `#006B60` | Positive indicators / growth |
| `tertiary-container` | `#8DF5E4` | Highlight chip background |
| `on-tertiary-container` | `#005C53` | Highlight chip text |
| `on-surface` | `#333235` | Primary text (no pure black) |
| `on-surface-variant` | `#605E61` | Secondary text / metadata |
| `outline-variant` | `#B4B1B4` | Ghost border (@ 15% opacity) |
| `error` | `#9E3F4E` | Alert / negative trend |

**My Organization-specific rules:**
- Hero: soft mesh gradient using `primary-container` + `secondary-container`, 135° angle.
- Metric cards: `surface-container-lowest` bg, `xl` radius (0.75rem), no borders.
- Knowledge source tags: pill chips with `secondary-container` bg, `on-secondary-container` text, `border-radius: 9999px`.
- Trend indicators: small chip, `border-radius: 9999px`, `tertiary` (#006B60) for positive, `error` (#9E3F4E) for alerts, 10% background opacity of respective color.
- Glassmorphism: `surface` at 80% + `backdrop-filter: blur(20px)` for floating nav.
- Hero CTA gradient: 135° from `primary` (#2B5BB5) to `primary-container` (#D9E2FF).

---

### 1.3 Source Explorer Page — "The Architectural Curator" (Light Mode)

| Token | Hex | Usage |
|---|---|---|
| `surface` / `background` | `#F7F9FB` | Base layer |
| `surface-container-low` | `#F2F4F6` | Filter panel background |
| `surface-container-lowest` | `#FFFFFF` | Source cards |
| `surface-container-high` | `#E6E8EA` | Hover / active states |
| `surface-container-highest` | `#E0E3E5` | Input background |
| `primary` | `#152270` | Key accents, active states |
| `primary-container` | `#2E3A87` | Gradient end for CTAs |
| `on-primary` | `#FFFFFF` | Text on primary |
| `secondary` | `#515F74` | Metadata labels |
| `on-surface` | `#191C1E` | Primary text |
| `on-surface-variant` | `#454651` | Secondary text / metadata |
| `on-tertiary-container` | `#EA9C62` | Highlight / accent moments |
| `surface-tint` | `#4C58A6` | Metric card left accent bar |
| `outline-variant` | `#C6C5D3` | Ghost border (@ 15% opacity) |
| `outline` | `#767682` | Subtle separators |

**Source Explorer-specific rules:**
- Layout: rigid **left filter panel** (`surface-container-low`) + fluid **content area** (`surface`).
- Filter panel: 24px internal padding, `title-sm` for category headers, `body-sm` for options.
- Source cards: horizontal Editorial layout, `surface-container-lowest`, 16px vertical gap between cards (no dividers).
- Card metadata (date, source, author): `label-md` in `on-surface-variant`.
- Metric cards: `sm` rounding (0.25rem), left 4px vertical `surface-tint` accent bar for active.
- Primary button: gradient 45° from `primary` (#152270) → `primary-container` (#2E3A87).
- Input fields: `surface-container-highest` bg, no border unfocused; Ghost Border on focus.
- Glassmorphism: `surface-container-lowest` at 80% opacity + `backdrop-filter: blur(20px)` for dropdowns.

---

### 1.4 Decision Engine Page (app.py) — "The Architect's Blueprint" (Light Mode)

| Token | Hex | Usage |
|---|---|---|
| `surface` / `background` | `#F8F9FA` | Base layer |
| `surface-container-low` | `#F3F4F5` | Large background regions |
| `surface-container-lowest` | `#FFFFFF` | Primary work surface / cards |
| `surface-container` | `#EDEEEF` | Grouped panels |
| `surface-container-high` | `#E7E8E9` | Hover row state |
| `surface-container-highest` | `#E1E3E4` | Input background |
| `primary` | `#001736` | Darkest text / headings |
| `primary-container` | `#002B5B` | Deep navy accent |
| `secondary` | `#006970` | Teal — success / data growth |
| `secondary-container` | `#96F1FA` | Evidence card accent |
| `on-secondary-container` | `#006F77` | Evidence card accent text |
| `tertiary-container` | `#00313C` | Dark "Insight Box" background |
| `on-surface` | `#191C1D` | Primary text |
| `on-surface-variant` | `#43474F` | Secondary text / metadata |
| `outline-variant` | `#C4C6D0` | Ghost border (@ 15% opacity) |
| `on-primary-container` | `#7594CA` | Muted primary accent |

**Decision Engine-specific rules:**
- Evidence cards: `surface-container-lowest` bg + **2px left-accent border** of `secondary` (#006970) = "High Confidence" indicator.
- Insight Boxes: `tertiary-container` (#00313C) background with light text — dark island in a light layout.
- Metric rows: no dividers; 16px vertical padding + `surface-container-high` hover.
- Tabs: **pill style only** — active: `primary` bg + `on-primary` text; inactive: `surface-container-high` + `on-surface-variant`. No underline tabs.
- Primary CTA gradient: 135° from `primary` (#001736) to `primary-container` (#002B5B).
- Table headers: `surface-container-low` bg, no vertical lines, `title-sm` ALL CAPS with `letter-spacing: 0.05em`.
- Numbers in tables: must use `font-variant-numeric: tabular-nums`.

---

## 2. Typography

All pages share a **dual-typeface system**:

| Role | Font | Scale | Letter Spacing | Usage |
|---|---|---|---|---|
| Display | **Manrope** | `display-lg` / `display-md` | `-0.02em` | Hero metrics, big impact numbers |
| Headline | **Manrope** | `headline-lg` / `headline-sm` | `-0.02em` | Section titles, card headers |
| Title | **Inter** | `title-sm` | `+0.05em` (ALL CAPS) | Table headers, panel subtitles |
| Body | **Inter** | `body-md` (0.875rem) | normal | All data-driven content |
| Label | **Inter** | `label-md` / `label-sm` | `+0.10em` (ALL CAPS for labels) | Metadata, chips, status tags |

**Import (add to Streamlit via `st.markdown`):**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
```

**Hierarchy rules:**
- Pair `display-md` metrics with `label-md` descriptors for asymmetric focal points.
- Use `on-surface` for primary text, `on-surface-variant` for secondary — never pure black or pure white.
- `headline-sm` (Manrope) for card titles → `label-sm` (Inter, ALL CAPS, +10% tracking) for sub-labels.

---

## 3. Spacing Rules

| Name | Value | Usage |
|---|---|---|
| `xs` | 4px | Icon gaps, tight inline spacing |
| `sm` | 8px | Between related inline items |
| `md` | 16px | Between card content rows |
| `lg` | 24px | Internal card/panel padding |
| `xl` | 32px | Between major sections |
| `2xl` | 48px | Section-level vertical breathing |
| `3xl` | 64px | Hero top padding / major breaks |

**Rules:**
- If two elements feel crowded, **increase padding — do not add a line.**
- Asymmetric vertical padding is intentional: give headings more top-room than bottom-room.
- Between list items: **16px gap**, no dividers.
- Filter panels and sidebars: **24px internal padding**.

---

## 4. Border Radius

| Name | Value | Usage |
|---|---|---|
| `sm` | 4px (0.25rem) | Data input fields, table cells |
| `md` | 8px (0.5rem) / 12px (0.75rem) | Buttons inside cards, inner elements |
| `lg` | 12px (0.75rem) | Metric cards, content cards |
| `xl` | 16px–24px (1–1.5rem) | Large hero containers, main cards |
| `full` (pill) | 9999px | Tab pills, status chips, tag chips |

**Login page exception:** Primary cards use `xl` (1.5rem); CTA buttons use `full` (pill).

---

## 5. Surface / Card Styles

### The "No-Line" Rule (Universal)
**Never use `1px solid border` to define sections.** All layout boundaries must be defined through background color shifts.

### Card Anatomy
```
┌───────────────────────────────────┐
│  Background: surface-container-lowest (#FFF or dark equiv)  │
│  Border-radius: lg–xl (12px–24px)                           │
│  Padding: 24px (lg)                                         │
│  Shadow: 0px 4px 20px rgba(25,28,29,0.04),                  │
│           0px 12px 40px rgba(25,28,29,0.08)  ← light only  │
│  NO border stroke.                                          │
└───────────────────────────────────┘
```

### Card Variants

| Variant | Background | Border | Shadow | Radius | Use Case |
|---|---|---|---|---|---|
| Default Card | `surface-container-lowest` | None | Ambient (2-layer) | `lg` | Metric cards, content panels |
| Evidence Card | `surface-container-lowest` | 2px left `secondary` | None | `lg` | Decision evidence entries |
| Insight Box | `tertiary-container` (dark) | None | None | `lg` | Highlighted insights in Decision Engine |
| Floating / Modal | `surface-variant` @ 70% | Ghost border @ 15% | `0px 12px 32px rgba(...)` | `xl` | Popovers, modals |
| Hover Row | `surface-container-high` | None | None | — | Table/list row hover state |

### Ghost Border (Fallback Only)
Use only when accessibility requires a visible boundary:
```css
border: 1px solid rgba(outline-variant-hex, 0.15);
```

---

## 6. Button Styles

| Type | Background | Text | Border | Radius | Hover |
|---|---|---|---|---|---|
| **Primary** | Gradient 135° `primary` → `primary-container` | `on-primary` | None | `md` or `full` | Darken gradient |
| **Secondary** | `surface-container-highest` | `on-surface` | None | `md` | `surface-container-high` |
| **Tertiary / Ghost** | None | `primary` | None | `md` | Scale 1.02x |
| **Pill Tag** | `secondary-container` | `on-secondary-container` | None | `full` (9999px) | Darken bg slightly |
| **Danger** | `error-container` (@ 15% opacity) | `error` | None | `md` | Full `error-container` |

**Login page:** Primary CTA uses `full` pill radius.  
**Decision Engine:** Primary CTA uses gradient 135° `#001736` → `#002B5B`.

---

## 7. Tab Styles

### Pill Tabs (Universal — underline tabs are banned)

```
Active tab:   background: primary | text: on-primary | radius: full | padding: 8px 20px
Inactive tab: background: surface-container-high | text: on-surface-variant | radius: full | padding: 8px 20px
Tab container: background: surface-container | padding: 4px | radius: full
```

**No underline indicators. No bottom borders. No full-width dividers below tabs.**

---

## 8. Layout Rules Per Page

### 8.1 Login Page (`pages/1_Login.py`)
- **Full-screen dark background:** `#0A0E17`
- **Centered single-column card** (max-width ~420px), `surface-container-high` background, `xl` radius (1.5rem), ambient shadow.
- Left side (optional for wide layout): Brand hero panel with glassmorphism overlay.
- Inputs: full-width, `surface-container-lowest` background (recessed), `sm` radius (4px).
- CTA ("Sign In"): full-width pill button, gradient background.
- All text: `on-surface` (#DDE5FF) — never `#FFFFFF`.
- Status messages: "Status Orb" pattern — small colored dot with 4px blur, next to text label. No large banners.

### 8.2 My Organization Page (`pages/2_My_Organization.py`)
- **Light background:** `#FCF8F9`
- **Hero section** at top: mesh gradient (`primary-container` + `secondary-container`, 135°), left-aligned `headline-lg` (Manrope).
- **Executive Summary** inside hero: Glassmorphism card, `surface` at 80% opacity + blur(20px).
- **Metric row** below hero: 3–4 cards horizontally, `surface-container-lowest` bg, `xl` radius, no borders.
- **Knowledge Sources panel:** pill-chip cloud layout, `secondary-container` chips.
- **Active Participants:** no dividers, 8px gap between `surface-container-lowest` rows.
- Mobile: fixed bottom nav bar, `surface` @ 80% + blur(12px).

### 8.3 Source Explorer Page (`pages/source_explorer.py`)
- **Two-column layout:** left filter panel + right content area (asymmetric).
  - Left panel: `surface-container-low` bg, 24px padding, fixed width (~280px).
  - Right area: `surface` bg, fluid.
- **Source cards:** `surface-container-lowest`, horizontal layout, 16px gap (no dividers).
- **Metric summary row** at top: small cards with `sm` radius, left 4px `surface-tint` accent bar for active state.
- **Search/filter inputs:** `surface-container-highest` bg, ghost border on focus.
- **Status chips:** `full` radius pills for source type tags.

### 8.4 Decision Engine Page (`app.py`)
- **Light background:** `#F8F9FA`
- **Query input area:** prominent, top of page, `surface-container-lowest` bg, `lg` radius.
- **Results section:** below query. Evidence cards with 2px left `secondary` border.
- **Insight Box:** `tertiary-container` (#00313C) dark block, draws immediate focus inside light layout.
- **Tabs (if used):** pill style, centered or left-aligned above results.
- **Tables:** `surface-container-low` header bg, no vertical lines, tabular-nums for numbers.
- **Sidebar / metadata panel** (if applicable): `surface-container-low` bg, 24px padding.

---

## 9. Glassmorphism Pattern

Used for floating panels, modals, and navigation overlays:

```css
/* Light mode */
background: rgba(248, 249, 250, 0.80);
backdrop-filter: blur(20px);
-webkit-backdrop-filter: blur(20px);

/* Dark mode (Login page) */
background: rgba(25, 37, 63, 0.70);   /* surface-variant */
backdrop-filter: blur(12px);
-webkit-backdrop-filter: blur(12px);
```

---

## 10. Ambient Shadow Pattern

Used only for floating elements (modals, popovers, dragged cards):

```css
/* Light mode */
box-shadow:
  0px 4px 20px rgba(25, 28, 29, 0.04),
  0px 12px 40px rgba(25, 28, 29, 0.08);

/* Dark mode */
box-shadow: 0px 12px 32px rgba(0, 0, 0, 0.40);
```

Do **not** apply shadows to standard content cards. Depth is achieved via background token shifts.

---

## 11. Global Do's and Don'ts

### ✅ Do
- Use `surface-container-*` token shifts to define section boundaries.
- Use `secondary` (teal) for success states and positive data indicators.
- Use `tertiary-container` dark blocks as "Insight Boxes" for focus moments.
- Use `tabular-nums` on all numeric data columns.
- Use pill chips (`border-radius: 9999px`) for status tags, type labels, and source badges.
- Add `16px` bottom margin between list items instead of dividers.

### ❌ Don't
- Don't use `#000000` (pure black) anywhere. Darkest color is `#001736` or `#0A0E17`.
- Don't use `#0000FF` or any generic saturated blue.
- Don't use `1px solid` borders to define layout sections.
- Don't use drop shadows on every card.
- Don't use underline-style tabs.
- Don't use large "Success / Error" banners — use small Status Orb or chip patterns.
- Don't use `rounded-lg` uniformly — vary radius by element type (sm for inputs, xl for hero containers).

---

## 12. Streamlit Implementation Notes

Since Memora is built in Streamlit, all CSS overrides are injected via `st.markdown(..., unsafe_allow_html=True)`.

**Key patterns:**
- Target Streamlit container base classes (e.g., `[data-testid="column"]`, `[data-testid="stVerticalBlock"]`) — do NOT wrap widgets in raw `<div>` tags.
- Apply card backgrounds by targeting the outer Streamlit column/container test IDs with custom CSS classes injected before the block.
- Use `st.markdown('<style>...</style>', unsafe_allow_html=True)` at the top of each page for page-scoped styles.
- Google Fonts must be loaded via `st.markdown('<link ...>', unsafe_allow_html=True)` at the top of each page.
- Streamlit's default widget styles (buttons, inputs, selects) should be overridden via CSS targeting `.stButton > button`, `.stTextInput input`, etc.

**Button override example:**
```css
.stButton > button {
  background: linear-gradient(135deg, #001736, #002B5B);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-family: 'Inter', sans-serif;
  font-weight: 600;
  padding: 10px 24px;
  transition: opacity 0.2s ease;
}
.stButton > button:hover {
  opacity: 0.88;
}
```

**Pill tab override example:**
```css
.stTabs [data-baseweb="tab"] {
  background: #E7E8E9;
  border-radius: 9999px;
  padding: 8px 20px;
  border: none;
}
.stTabs [aria-selected="true"] {
  background: #001736;
  color: #ffffff;
  border-radius: 9999px;
}
```

---

*Generated from Stitch projects: Memora Login (3857141611714587184), Memora My Organization (18264104599879610119), Memora Source Explorer (11404184758896972745), Memora Decision Engine (2458086797470359753).*
