---
name: operations-workbench-gui
description: "Design and build a restrained dark desktop operations workbench for crawler, automation, data-processing, and resource-management GUIs. Use with $web-design-engineer when a project needs a left navigation rail, right content workspace, explicit visual tokens, functional page grouping, and low-noise interaction states."
---

# Operations Workbench GUI

A reusable visual and architectural skill for desktop tools that execute operational workflows such as crawling, importing, transferring, processing, archiving, or decompression.

This skill is a specialization of **`$web-design-engineer`**. Apply the parent skill's principles for design calibration, existing-work audits, visual hierarchy, interaction states, placeholders, accessibility, and pre-delivery critique. This skill adds the concrete design language and implementation contract for a quiet, reliable operations console.

## 1. When to Use

Use this skill when the product is:

- a desktop GUI for a crawler, scraper, downloader, automation tool, converter, or batch processor;
- a multi-step utility where users configure a runtime, execute a task, inspect results, and process output;
- information-dense but not a real-time cockpit;
- better served by clear workflow navigation than by a dashboard full of decorative metrics.

Do not use this as a universal visual preset for consumer products, marketing pages, games, or brand-led experiences. The system is intentionally restrained and operational.

## 2. Required Invocation

Start the task with:

```text
Use $web-design-engineer and apply $operations-workbench-gui.
```

Then classify the work using the parent skill:

```yaml
mode: extension | redesign-preserve | redesign-overhaul | greenfield
artifact: desktop operations workbench
primary_task: configure -> execute -> inspect -> process
visual_language: restrained operations console / editorial data tool
```

For an existing GUI, read the source before designing from screenshots. Preserve public page properties, controller bindings, signals, field names, persistent state, task contracts, and accessibility behavior unless the user explicitly authorizes a contract change.

## 3. Design Direction

### Positioning

The interface should feel like a calm local control surface: reliable, precise, quiet, and slightly editorial. It is not a futuristic command center and it is not a generic SaaS dashboard.

Use these terms when describing the direction:

- restrained operations console;
- editorial data tool;
- local-first workspace;
- low-noise information architecture;
- progressive disclosure;
- workflow-oriented navigation;
- content-first utility UI;
- semantic state feedback;
- warm accent on neutral dark surfaces.

### Five Dials

Use these starting values for a typical crawler or resource-processing GUI:

```yaml
visual-variance: 5
motion-intensity: 2-3
information-density: 7
asset-dependence: 1-2
brand-fidelity: 7 for an existing product, 4-6 for a new utility
```

The values must change implementation decisions:

- **Variance 5**: use one strong structural move—the left navigation rail—while keeping the content grid stable.
- **Motion 2-3**: use hover, focus, pressed, checked, disabled, and task-state feedback; avoid decorative sequences.
- **Density 7**: support forms, selectors, lists, logs, previews, and actions in one desktop viewport through grouping and scrolling.
- **Asset dependence 1-2**: typography, spacing, contrast, and interface structure carry the design. Do not invent decorative imagery.
- **Brand fidelity 7**: preserve real product identity and workflow semantics while allowing a cohesive visual overhaul.

### Four Positioning Questions

Before implementing a screen, answer:

- **Narrative role**: operational step, configuration, execution, preview, result, or recovery state?
- **Viewing distance**: desktop laptop at approximately 1080×720 or larger; body text must remain readable at normal system scaling.
- **Visual temperature**: calm, authoritative, and focused; use warmth only for primary action emphasis.
- **Capacity check**: does the page fit its task parameters and result area without adding decorative filler? If it feels empty, improve composition before adding content.

## 4. Layout Contract

### Global Structure

Use a strict horizontal split:

```text
┌──────────────────────┬────────────────────────────────────────────┐
│ Fixed navigation rail│ Right content workspace                   │
│                      │                                            │
│ Brand                 │ Page title                                │
│ Navigation tabs       │ Page-specific content                     │
│ Flexible empty space  │                                            │
│                      │                                            │
└──────────────────────┴────────────────────────────────────────────┘
```

Use a `QHBoxLayout` or equivalent horizontal flex/grid as the root layout. The left rail is fixed; the right workspace takes the remaining width.

### Left Navigation Rail

Recommended contract:

- fixed width: **228px**;
- background: near-black charcoal;
- right border: one low-contrast hairline;
- top padding: 24px;
- left/right padding: 20px / 16px;
- brand block at the top;
- navigation begins after a generous 38px separation;
- tabs are stacked vertically;
- tab labels are plain text, left aligned;
- active tab uses a quiet warm surface and warm text;
- inactive tabs use muted neutral text;
- no numeric prefixes;
- no section heading such as `WORKFLOW`;
- no bottom footer, workspace metadata, version block, or decorative rule;
- flexible empty space below navigation is acceptable and intentional.

Default workflow tab order for this product family:

1. `登陆抓取`
2. `资源转存`
3. `资源解压`
4. `基本配置`

For another product, order tabs by the user's actual journey, not by implementation order. Configuration may be placed last when it is an infrequent setup surface; if configuration is a hard prerequisite users must see first, make that a deliberate product decision rather than a default.

### Right Workspace

Recommended contract:

- background: charcoal neutral, never pure black;
- horizontal padding: approximately 42px;
- top padding: 30px;
- bottom padding: 26px;
- page header and page content are vertically stacked;
- page header contains only a Chinese/localized title;
- no subtitle-like secondary heading is allowed anywhere in the GUI, including page headers, section cards, item cards, panels, toolbars, and brand blocks;
- do not add a page description, kicker, helper sentence, explanatory caption, or other secondary copy beneath a title;
- no English kicker, workflow sequence marker, or page ordinal;
- no top-right `LOCAL / READY` or equivalent decorative status pill;
- content begins after approximately 24px header spacing;
- page content may use two-column layouts for action parameters and result lists;
- page content should scroll internally when the task is larger than the viewport.

### Page Composition

Use the following composition hierarchy:

```text
Page header
  └─ localized page title

Content area
  ├─ task/action card
  ├─ result/list/preview card
  └─ semantic status feedback near the action or affected content
```

Do not add a second page title card inside each page. The shell owns page identity; page widgets own task content.

## 5. Visual Tokens

Treat these as the default token set. Override only with a documented reason or an existing brand requirement.

### Color Palette

```yaml
canvas:
  app: "#171A1D"
  workspace: "#171A1D"
  sidebar: "#0D0F10"

surface:
  card: "#1D2124"
  item: "#191D20"
  input: "#151819"
  input-disabled: "#1C2022"
  nav-hover: "#191E20"
  nav-active: "#29231D"
  list-selected: "#3D3023"
  secondary-button: "#252A2D"

border:
  rail: "#2B3033"
  default: "#30363A"
  control: "#3A4144"
  control-hover: "#555D60"
  active: "#60482F"

text:
  primary: "#F1F0EA"
  heading: "#F6F4EE"
  body: "#DCDAD3"
  secondary: "#989D9E"
  muted: "#8F9596"
  quiet: "#777D7F"
  disabled: "#707678"
  navigation: "#979C9D"

accent:
  primary: "#E6A15C"
  hover: "#F0B271"
  pressed: "#C98143"
  active-text: "#F0B678"
  button-ink: "#211810"

semantic:
  success: "#9DD5A7"
  warning: "#E2C077"
  error: "#E28C87"
```

Color rules:

- Use charcoal neutrals for most of the surface area.
- Use **one warm amber accent** for primary actions, focus, selected navigation, links, and important emphasis.
- Use green, yellow, and red only for semantic state feedback.
- Do not add unrelated blue, purple, pink, cyan, or neon hues.
- Keep borders visible but quiet; hierarchy should come from surface contrast, spacing, and typography before strong outlines.
- Do not use large gradients as a substitute for composition.

### Typography

Default font stack for PySide6 on Windows:

```text
"Microsoft YaHei UI", "Segoe UI", sans-serif
```

Recommended hierarchy:

```yaml
body:
  size: 14px
  weight: 400
  color: "#F1F0EA"

page-title:
  size: 28px
  weight: 800
  color: "#F6F4EE"

section-title:
  size: 16px
  weight: 750
  color: "#F1F0EA"

field-label:
  size: 14px
  weight: 650
  color: "#DCDAD3"

navigation:
  size: 13px
  weight: 600
  color: "#979C9D"

brand:
  size: 19px
  weight: 800
  letter-spacing: 1px
```

Typography rules:

- Use weight and spacing to create hierarchy instead of adding multiple font families.
- Keep the application to one primary UI family; use a monospace face only for paths, IDs, logs, or machine-generated values when needed.
- Do not default to Inter, Roboto, Arial, or system-ui as display fonts for a showcase web artifact. For this Windows desktop preset, Microsoft YaHei UI and Segoe UI are intentional platform-native choices.
- Keep page titles substantially larger than body text; do not create a second hierarchy level with a page subtitle or description.
- Prefer localized product language in visible UI. Do not use English labels as decoration.

### Spacing and Sizing

Use a **4px base unit**, with most layout values drawn from:

```text
4 / 8 / 12 / 16 / 20 / 24 / 30 / 38 / 42
```

Recommended values:

```yaml
sidebar:
  width: 228px
  top-padding: 24px
  horizontal-padding: 20px 16px
  brand-to-tabs-gap: 38px
  tab-gap: 4px

workspace:
  top-padding: 30px
  horizontal-padding: 42px
  bottom-padding: 26px
  header-to-content-gap: 24px

cards:
  inner-padding: 18px 20px 20px
  body-gap: 10px
  inter-card-gap: 16px

controls:
  horizontal-padding: 10px 15px
  vertical-padding: 8px 9px
```

Do not use spacing to create accidental page density. A dense operational screen should be dense because it contains useful controls and results, not because every edge is compressed.

### Radius and Elevation

```yaml
navigation-tab: 8px
control: 7px
scroll-area: 8px
item-card: 8px
section-card: 12px
```

Use no visible shadow by default. Use hairline borders and surface contrast as the primary elevation model. If a modal or floating surface is required, use a subtle dark shadow only to establish containment.

## 6. Component Recipes

### Navigation Tab

A navigation tab is a `checkable` button inside an exclusive button group.

Required states:

- default: transparent background, muted text;
- hover: slightly lighter charcoal surface, brighter text;
- checked: warm charcoal surface `#29231D`, amber text `#F0B678`, warm border `#60482F`;
- disabled: reduced contrast without disappearing entirely;
- keyboard focus: visible focus indication.

Do not prefix labels with sequence numbers. Do not add icons unless the product has a real icon set and the icon improves recognition.

### Section Card

Use a section card for a coherent task group, not for every individual field.

Required section-header contract:

- show the section title as the only header text;
- place a shallow, light-colored hairline immediately between the title and the body content;
- limit the hairline width to the rendered title width, or the title's local header width; never stretch it across the full card;
- keep the hairline visually quiet and subordinate to the title;
- do not render a section subtitle, helper sentence, explanatory caption, kicker, or other secondary copy anywhere in the section header;
- place necessary instructions next to the affected control or in inline status feedback, not below the section title.

For Qt Widgets, this may be implemented with a title `QLabel` followed by a one-pixel `QFrame` or equivalent local rule. For web implementations, use a local pseudo-element or dedicated rule element whose width is constrained to the title block.

```yaml
background: "#1D2124"
border: "1px solid #30363A"
radius: 12px
padding: "18px 20px 20px"
header-gap: 8px
section-rule:
  color: "#A9ACA7"
  height: 1px
  width: title-width
body-gap: 10px
```

Cards should group action controls, parameters, result lists, or previews. Avoid a card inside a card unless the nested region has a clear semantic boundary.

### Item Card

Use item cards for archive entries, resource entries, or other repeated result units.

```yaml
background: "#191D20"
border: "1px solid #30363A"
radius: 8px
```

### Primary Button

Use the warm accent only for the most important next action on a region.

```yaml
background: "#E6A15C"
text: "#211810"
hover: "#F0B271"
pressed: "#C98143"
radius: 7px
font-weight: 700
```

### Secondary Button

Use for browse, choose, clear, preview, and other non-committing actions.

```yaml
background: "#252A2D"
text: "#D8D7D0"
border: "1px solid #3A4144"
hover-background: "#30373A"
hover-border: "#596164"
```

### Form Control

Use consistent styling for `QLineEdit`, `QComboBox`, and `QListWidget`.

```yaml
background: "#151819"
border: "1px solid #3A4144"
hover-border: "#555D60"
focus-border: "#E6A15C"
radius: 7px
padding: "8px 10px"
```

Focus is a functional state, not decoration. Never remove it to make the interface look cleaner.

### Semantic Status

Keep status text close to the action or affected list. Use `success`, `warning`, `error`, and a neutral default state. Do not rely on color alone; the message must state what happened and what the user can do next.

The status bar is intentionally omitted in this design language. Prefer inline status labels inside the relevant section card.

## 7. Information Architecture

Model the product as a workflow, not as a collection of unrelated tools.

Typical operational sequence:

```text
登陆抓取 -> 资源转存 -> 资源解压
                         ^
                    基本配置
```

The navigation order should reflect the primary user journey. In this preset, `基本配置` is placed last because it is a setup surface and the three task pages are the primary workflow. If another product has configuration as a hard prerequisite, place it first and document the reason.

Each page should answer three questions immediately:

1. What operation is this?
2. What input or selection is required?
3. What is the next safe action?

Use progressive disclosure for advanced options. Keep destructive, irreversible, or network-affecting actions visually explicit and separate from browsing or preview actions.

## 8. Explicitly Removed Design Elements

The following elements are intentionally excluded from this design system because they increase chrome without improving task comprehension:

- top-level horizontal navigation tabs;
- the `WORKFLOW` sidebar section heading;
- numeric prefixes such as `01`, `02`, `03`, `04` before Tab labels;
- English page kickers such as `01 / WORKFLOW`;
- right-top decorative status pills such as `LOCAL / READY`;
- bottom status bars used only to display passive messages such as `正在加载本地配置…`;
- page and section subtitles, helper sentences, kickers, or explanatory captions used as secondary headings;
- secondary descriptor text beneath brand names or other titles;
- bottom-left workspace metadata, version blocks, or decorative separator rules;
- duplicate page title cards inside page content;
- large outer containers with 16–20px radius around the entire page;
- strong drop shadows as the primary hierarchy mechanism;
- emoji used as icons or decoration;
- fabricated statistics, fake task counts, placeholder testimonials, or invented data;
- unrelated accent colors added to make a dense screen look more complete.

A removed element may return only when it has a clear user task, accessibility, or product requirement. Decorative chrome needs a documented reason.

## 9. Technical Framework

### Current Reference Implementation

The reference implementation uses:

- **Python 3.13**;
- **PySide6 6.8+**;
- Qt Widgets, not QML;
- `QMainWindow` as the application shell;
- `QHBoxLayout` for the left/right split;
- `QVBoxLayout` for vertical navigation and page composition;
- `QStackedWidget` for page switching;
- `QButtonGroup` with checkable `QPushButton` instances for exclusive Tabs;
- Qt signals for page-to-controller events;
- background task coordination through application controllers and services;
- a centralized Qt stylesheet generated by a function such as `build_application_stylesheet()`.

### Recommended Architecture

Keep visual composition separate from business logic:

```text
MainWindow / Page Widgets
        ↓ signals and view state
Controllers
        ↓ task coordination
Services
        ↓ I/O and domain operations
Core, browser, network, filesystem adapters
```

Use the same separation for other frameworks:

- React/Vue/Svelte: shell + pages/components → hooks/store/controller → services/adapters;
- Qt Widgets: widgets → signals → controllers → services;
- Tkinter: frames → callbacks/commands → application services.

Do not put crawling, network calls, filesystem traversal, or decompression directly inside view-building methods. Views own layout and user intent; controllers coordinate; services perform work.

### Implementation Rules

- Preserve page/controller APIs while changing visual layout.
- Keep page metadata in one immutable structure so navigation labels, order, and titles cannot drift apart.
- Make page switching update both `QStackedWidget` and the selected navigation button.
- Guard page indexes before switching.
- Keep `set_busy()` as a single shell-level busy-state entry point.
- Use object names or scoped class names for style targeting; do not rely on accidental widget hierarchy.
- Prefer semantic widget names such as `sidebarRail`, `navigationButton`, `pageSurface`, `sectionCard`, `itemCard`, and `statusLabel`.
- Do not create a global `styles` object in React; namespace style objects if inline styles are required.
- For web implementations, use CSS custom properties for the token set and CSS Grid/Flexbox for the split layout.
- For Qt implementations, use a centralized QSS string and `WA_StyledBackground` only where custom widget backgrounds need to render reliably.
- Treat external tasks as asynchronous. Disable navigation and controls while a task is running, then restore them when it finishes.
- Keep status messages inline near the affected action or result area.

## 10. Responsive and Accessibility Rules

For desktop Qt:

- design for a minimum window size around 1080×720;
- keep the navigation rail wide enough for localized labels;
- allow result lists and preview panes to scroll rather than compressing controls into unreadable widths;
- preserve keyboard focus visibility and logical tab order;
- use sufficient text contrast against charcoal surfaces;
- never communicate task state by color alone;
- keep primary action targets large enough to activate reliably;
- avoid motion that competes with long-running operations.

For web adaptations:

- keep the left rail at desktop widths;
- below the desktop breakpoint, collapse it into a compact drawer or a deliberate top navigation—do not let a 228px rail squeeze the task surface indefinitely;
- maintain the same semantic order and active-state model;
- use `prefers-reduced-motion` for any non-essential animation;
- use `text-wrap: pretty` and responsive typography where supported.

## 11. Workflow for Reuse

1. Invoke `$web-design-engineer` and this skill.
2. Audit the existing GUI and classify it as extension, redesign-preserve, or redesign-overhaul.
3. Record protected contracts: routes, page APIs, signals, forms, selectors, persistence, and accessibility behavior.
4. Write a short Design Read with the five dials.
5. Confirm the four positioning questions for the target screen.
6. Declare or adapt the tokens in this document before coding.
7. Build a v0 shell with the left rail, right workspace, page header, and placeholder cards.
8. Confirm the direction before implementing every page detail when the redesign is non-trivial.
9. Implement states: default, hover, checked/active, focus, pressed, disabled, loading, empty, and error where relevant.
10. Run the project tests, compile/lint checks, and the parent skill's pre-delivery checklist.
11. If the user explicitly asks for browser/UI acceptance, run the relevant acceptance procedure and report evidence.

## 12. Copy-Paste Prompt

Use this prompt to start a future GUI redesign:

```text
Use $web-design-engineer and apply $operations-workbench-gui.

Build or redesign this as a restrained operations workbench:
- use a fixed left navigation rail and a flexible right content workspace;
- use localized, plain-text navigation labels with no numeric prefixes;
- keep navigation in the user's operational order;
- use a dark charcoal neutral palette with one warm amber action accent;
- use Microsoft YaHei UI / Segoe UI for Windows Qt interfaces;
- use a compact page header containing only the localized title;
- use section cards for meaningful task groups, not for every field;
- separate every section title from its body with a quiet one-pixel rule limited to the title width;
- never add subtitles, descriptions, helper sentences, kickers, or explanatory secondary headings anywhere in the GUI;
- keep status feedback inline near the affected action or result;
- omit WORKFLOW headings, English kickers, decorative status pills, passive bottom status bars, and bottom workspace metadata;
- preserve existing business contracts, page APIs, signals, and controller/service boundaries;
- use the existing framework rather than introducing a new UI stack without a reason;
- verify the final result with tests, lint/compile checks, and the parent skill checklist.
```