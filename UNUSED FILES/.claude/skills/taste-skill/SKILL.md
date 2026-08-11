---
name: design-taste-frontend
description: Anti-slop frontend skill for landing pages, portfolios, and redesigns. The agent reads the brief, infers the right design direction, and ships interfaces that do not look templated.
---

# tasteskill: Anti-Slop Frontend Skill

## 0. BRIEF INFERENCE
Before touching code, **infer what the user actually wants**.
1. **Page kind** — landing (SaaS / consumer / agency), portfolio (dev / designer), redesign (preserve vs overhaul), editorial.
2. **Vibe words** — "minimalist", "calm", "Linear-style", "Awwwards", "brutalist", "premium consumer".
3. **Audience** — B2B procurement vs design-conscious consumer vs recruiter.
4. **Brand assets** — logo, color, type, photography.
5. **Quiet constraints** — accessibility-first, regulated industries, kids' products (override aesthetic).

**Output a one-line "Design Read"** before generating:
- *"Reading this as: B2B SaaS landing for technical buyers, with a Linear-style language, leaning toward Tailwind utilities + Geist + restrained motion."*

## 1. THE THREE DIALS
Set three dials after the design read:
- **DESIGN_VARIANCE: 8** (1=Perfect Symmetry, 10=Artsy Chaos)
- **MOTION_INTENSITY: 6** (1=Static, 10=Cinematic)
- **VISUAL_DENSITY: 4** (1=Airy, 10=Cockpit)

## 2. DEFAULT ARCHITECTURE
- **Framework:** React or Next.js with RSC. `"use client"` only on leaf interactive components.
- **Styling:** Tailwind v4 (default). v3 only if existing project demands it.
- **Animation:** Motion (`motion/react`). Not `framer-motion` in new code.
- **Fonts:** `next/font` or self-hosted `@font-face` with `font-display: swap`. Never Google Fonts via `<link>`.
- **State:** Local `useState` / `useReducer`. Global ONLY for deep prop-drilling (Zustand, Jotai). **NEVER** `useState` for mouse/scroll values — use Motion's `useMotionValue`.
- **Icons:** Phosphor, Hugeicons, Radix, Tabler. Not Lucide. One family per project.
- **Responsiveness:** `min-h-[100dvh]` never `h-screen`. CSS Grid over Flexbox percentage math.

## 3. DESIGN ENGINEERING DIRECTIVES

### 3.1 Typography
- **Sans default:** Geist, Outfit, Cabinet Grotesk, Satoshi. NOT Inter as default.
- **Display:** `text-4xl md:text-6xl tracking-tighter leading-none`.
- **Body:** `text-base leading-relaxed max-w-[65ch]`.
- **Serif:** Very discouraged as default. Only when brand literally names one, or genuine editorial/luxury context.
- **BANNED serif defaults:** Fraunces, Instrument_Serif.
- **Emphasis:** Use italic/bold of SAME font. Never mix families for emphasis.
- **Italic descender clearance:** `leading-[1.1]` minimum + `pb-1` on wrapping element.

### 3.2 Color Calibration
- Max 1 accent color. Saturation < 80%.
- **NO AI purple/blue glow.** Use neutral bases (Zinc/Slate/Stone) with singular accents (Emerald, Electric Blue, Deep Rose, Burnt Orange).
- One palette per project. Lock accent, audit every component.
- **Premium-consumer palette ban:** No warm beige/cream + brass/clay/oxblood/espresso as default. Rotate from alternatives.

### 3.3 Layout
- **ANTI-CENTER BIAS:** Centered hero avoided when `VARIANCE > 4`. Use split-screen, left-aligned, or asymmetric.
- **Cards** only when elevation communicates hierarchy. Otherwise `border-t`, `divide-y`, or negative space.
- **ZIGZAG ALTERNATION CAP:** Max 2 consecutive image+text splits. 3rd = fail.
- **EYEBROW RESTRAINT:** Max 1 eyebrow per 3 sections. Count instances of `uppercase tracking`.
- **SHAPE CONSISTENCY:** Pick ONE corner-radius scale per page.
- **Bento grids:** Must have rhythm. Not 6 left-image/right-text rows. Vary composition.

### 3.4 Hero Discipline
- MUST fit initial viewport. Headline max 2 lines, subtext max **20 words**, CTAs visible.
- Hero top padding max `pt-24` at desktop.
- **Max 4 text elements:** eyebrow (0-1), headline, subtext, CTAs (1 primary + 1 secondary max).
- No taglines below CTAs, no trust logos, no feature bullets in hero.
- Logo wall goes UNDER hero, not inside it.

### 3.5 Images
- **Priority order:** (1) Image-generation tool first, (2) Real web images (picsum.photos), (3) Tell user.
- **No div-based fake screenshots.** Use real URLs, generation, or editorial photography.
- **Company logos:** Use Simple Icons CDN or generate SVG monograms. No plain text wordmarks.
- Bento grids need real visual variation in at least 2-3 cells.

## 4. FORBIDDEN PATTERNS
- No neon/outer glows. Use inner borders or tinted shadows.
- No pure `#000000`. Use off-black, zinc-950, charcoal.
- No custom mouse cursors.
- No `window.addEventListener("scroll")`. Use `useScroll()`, ScrollTrigger, or CSS `scroll-driven animations`.
- No `useState` for continuous mouse/scroll values.
- No serif in headlines as default emphasis move.
- No duplicate CTA intent on same page.
- No marquee used more than once per page.
- No `h-screen` — use `min-h-[100dvh]`.
- No `<link>` to Google Fonts in production.

## 5. MOTION
- Spring physics preferred (`type: "spring", stiffness: 100, damping: 20`). Not linear easing.
- Honor `prefers-reduced-motion`. Use `useReducedMotion()` in Motion.
- Animate ONLY `transform` and `opacity`. Never `top`, `left`, `width`, `height`.
- GSAP only for pin/scrub work. For simple scroll-reveal, prefer Motion's `whileInView`.

## 6. ACCESSIBILITY
- Design for both light and dark mode from the start.
- WCAG AA contrast minimum (4.5:1 body, 3:1 large text 18px+).
- Focus indicators on all interactive elements.
- `<kbd>` tags for keyboard shortcuts.
- `aria-label` on icon-only buttons.
- Skip-to-content link.

## 7. INTERACTIVE STATES
Always implement full cycles:
- **Loading:** Skeletal loaders matching final layout shape.
- **Empty:** Beautifully composed.
- **Error:** Clear, inline (forms), or contextual (toasts for transient).
- **Tactile:** `:active` → `scale(0.98)` or `translateY(1px)`.
