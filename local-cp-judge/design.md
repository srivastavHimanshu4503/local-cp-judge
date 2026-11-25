# Local CP Judge — Design System & UI Specification (`design.md`)

> **Theme:** Obsidian Minimalist Dark (Linear / Zed IDE Inspired)  
> **Visual Source of Truth:** Approved Option 1 Obsidian Dark mockup (`watermarked_img_12627604716509282423.jpg`). Do not deviate from these tokens, structural proportions, or border/scrollbar rules.

---

## 1. Design Philosophy

1. **Zero Visual Noise:** Deep matte zinc surfaces (`#09090B` / `#111115`) separated by crisp `1px` hairlines (`#27272A`) instead of heavy drop shadows or bright clashing boxes.
2. **Reading-First Left Pane:** Treat the Problem Statement like editorial technical documentation (`Inter`, generous `1.65` line-height, muted monochrome metadata chips) with **custom thin dark scrollbars** (never native bright white OS scrollbars).
3. **Unified Single-Row Toolbars:** Collapse redundant multi-row file headers and raw OS paths (`E:\Personal projects\...`) into a compact `40px` tab bar + slim `.../workspace/solution.py` breadcrumb.
4. **High-Contrast Execution Focus:** Reserve saturated color strictly for status and primary actions — emerald (`#10B981`) for `AC` / `Run Samples` and indigo-blue (`#4F46E5` / `#3B82F6`) for `Judge All`.

---

## 2. Design Tokens

Add these custom properties to your global CSS (and map them into Tailwind if used):

```css
:root {
  /* Surfaces */
  --bg-app: #09090B;              /* Deep matte obsidian canvas */
  --bg-panel: #111115;            /* Elevated pane / header surface */
  --bg-surface-subtle: #18181B;   /* Inputs, code example boxes, inactive pills */
  --bg-surface-hover: #1F1F24;    /* Hover state for tabs & rows */
  --bg-editor: #0D0D11;           /* Code editor canvas */

  /* Borders & Hairlines */
  --border-subtle: #27272A;       /* Primary 1px pane & card dividers */
  --border-strong: #3F3F46;       /* Active input / button borders */

  /* Typography Colors */
  --text-primary: #FAFAFA;        /* Headings & active labels */
  --text-secondary: #A1A1AA;      /* Problem statement body & descriptions */
  --text-muted: #71717A;          /* Line numbers, breadcrumbs, inactive tabs */

  /* Brand & Semantic Accents */
  --accent-judge: #4F46E5;        /* Judge All primary CTA */
  --accent-judge-hover: #4338CA;
  --accent-ac: #10B981;           /* AC dot & Run Samples accent */
  --accent-ac-bg: rgba(16, 185, 129, 0.12);
  --accent-ac-border: rgba(16, 185, 129, 0.30);
  --accent-wa: #EF4444;           /* Wrong Answer / Error */
  --accent-tle: #F59E0B;          /* Time Limit / Warning */

  /* Radii & Dimensions */
  --radius-control: 8px;
  --radius-card: 10px;
  --radius-pill: 9999px;
  --header-height: 48px;
  --footer-height: 44px;
}

/* Custom Thin Dark Scrollbar (Replaces jarring white OS scrollbar) */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: #27272A;
  border-radius: 9999px;
}
::-webkit-scrollbar-thumb:hover {
  background: #3F3F46;
}
```

### Typography
- **UI Sans:** `Inter` (`400`, `500`, `600`, `700`)
- **Code & Math/Timer Mono:** `JetBrains Mono` (`400`, `500`)
- **Scale:**
  - Problem H1 (`Problem A — Rabbit / Frog 1`): `22px`, `font-weight: 700`, `tracking: -0.02em`, `#FAFAFA`
  - Section Headings (`Problem Statement`, `Constraints`, `Examples`): `13px`, `font-weight: 600`, `#E4E4E7`
  - Statement Body: `14px`, `line-height: 1.65`, `#A1A1AA` (`max-w-[68ch]`)
  - Code Editor & Sample I/O: `13.5px` (`JetBrains Mono`), `line-height: 1.6`
  - Pills / Tabs / Metadata: `12px`, `font-weight: 500`

---

## 3. Workspace Layout & Component Specifications

### A. Slim Top Navigation Bar (`h-12 bg-[#111115] border-b border-[#27272A] px-4 flex items-center justify-between`)
- **Left:**
  - `Local CP Judge` wordmark + compact geometric icon.
  - Contest selector pill (`10Sep Contest ▾`, `bg-[#18181B] border border-[#27272A] rounded-lg px-3 py-1.5 text-xs`).
- **Center (Segmented Problem Switcher):**
  - Horizontal pill group (`bg-[#09090B] p-1 rounded-full border border-[#27272A] flex items-center gap-1`):
    - Active problem (`A · Rabbit / Frog 1`): `bg-[#18181B] text-[#FAFAFA] border border-[#3F3F46] rounded-full px-3 py-1` with a `6px` `#10B981` emerald AC dot.
    - Inactive problems (`B`, `C`, `D`): compact pills with status dot (`#71717A` or `#10B981`) that expand tooltip on hover.
- **Right:**
  - Monospace timer (`00:00:00` in `JetBrains Mono`) + crisp `Play` / `Reset` icon buttons.
  - `Practice` mode pill (`bg-[#18181B] border border-[#27272A] text-xs`).
  - Compact `Upload` icon/button (`Upload Archive`).

### B. Main Split Workspace (`h-[calc(100vh-48px)] grid grid-cols-1 lg:grid-cols-12 overflow-hidden`)
- **Left Pane — Problem Statement (`lg:col-span-5 bg-[#09090B] border-r border-[#27272A] overflow-y-auto px-7 py-6`):**
  - **Metadata Strip (Top):** Compact muted monochrome chips (`AtCoder`, `DP`, `2.0s`, `1024MB`) styled uniformly (`bg-[#18181B] border border-[#27272A] text-[#A1A1AA] text-xs px-2.5 py-0.5 rounded-md`) — **no** clashing rainbow pills.
  - **Title Row:** Bold `Problem A — Rabbit / Frog 1` on left + subtle `View on AtCoder ↗` text link (`text-xs text-[#71717A] hover:text-[#FAFAFA]`) on right.
  - **Content Sections:** Generous vertical spacing (`space-y-6`) for `Problem Statement`, `Input Format`, `Output Format`, `Constraints`, and `Examples`.
  - **Example Cards:** Side-by-side 2-column grid (`grid-cols-2 gap-3`): `Example 1 Input` and `Example 1 Output` inside `bg-[#111115] border border-[#27272A] rounded-[10px] p-3` with a top-right subtle `Copy` button.

- **Right Pane — Editor + Test Runner (`lg:col-span-7 flex flex-col h-full bg-[#0D0D11] overflow-hidden`):**
  1. **Unified Editor Tab Bar (`h-10 bg-[#111115] border-b border-[#27272A] px-3 flex items-center justify-between`):**
     - Left: Language file tabs (`solution.py` active with `#0D0D11` background & top accent, `solution.cpp`, `Main.java`).
     - Right: `Reference` selector (compact dropdown), `Auto-Sync` subtle indicator, `VS Code` button, and `Save` icon button.
  2. **Slim Breadcrumb Bar (`h-7 px-4 flex items-center justify-between border-b border-[#27272A]/60 text-[11px] font-mono text-[#71717A]`):**
     - Displays truncated path `.../workspace/solution.py` (full Windows/POSIX path shown only on hover tooltip).
     - Subtle `- 100% +` font-size control on far right (default `13.5px–14px`, not oversized `172%`).
  3. **Code Editor Canvas (`flex-1 min-h-0 overflow-hidden`):**
     - Clean `#0D0D11` background, muted `#52525B` line numbers, crisp `JetBrains Mono` syntax highlighting.
  4. **Docked Bottom Test Runner (`h-[240px] border-t border-[#27272A] bg-[#111115] flex flex-col`):**
     - **Tab Header (`h-10 px-4 border-b border-[#27272A] flex items-center gap-6`):** `Test Verdicts` (active with `2px` `#FAFAFA` bottom underline), `Custom Input`, `Stress Tester`.
     - **Body (`flex-1 overflow-y-auto p-4`):** Clean empty state or live verdict cards (`AC` / `WA` / `TLE` with runtime & diff).
     - **Footer Action Bar (`h-11 px-4 border-t border-[#27272A] bg-[#09090B] flex items-center justify-between`):**
       - Left: `Console` toggle + `Fail Fast` switch (`#27272A` track).
       - Right: `Run My Tests` (ghost/bordered), **`Run Samples`** (`bg-[#10B981]/15 border border-[#10B981]/40 text-[#34D399] hover:bg-[#10B981]/25`), and **`Judge All`** (`bg-[#4F46E5] hover:bg-[#4338CA] text-white font-medium`).

---

## 4. Responsive Rules (`< 1024px`)

- **Top Bar:** Collapse problem pills into a compact dropdown (`Problem A ▾`) beside the contest selector so the header stays on one clean row.
- **Workspace Switcher:** Add a sticky 2-tab bar (`Problem` | `Code & Tests`) below the header on `< 1024px` so mobile/tablet users never have to scroll past a giant problem statement to reach the editor.
- **Examples:** Stack `Example Input` and `Example Output` vertically (`grid-cols-1 sm:grid-cols-2`).
