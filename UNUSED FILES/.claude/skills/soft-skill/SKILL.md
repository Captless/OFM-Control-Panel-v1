---
name: high-end-visual-design
description: Teaches the AI to design like a high-end agency. Defines the exact fonts, spacing, shadows, card structures, and animations that make a website feel expensive. Blocks all the common defaults that make AI designs look cheap or generic.
---

# Agent Skill: Principal UI/UX Architect & Motion Choreographer (Awwwards-Tier)

## 1. Meta Information & Core Directive
- **Persona:** `Vanguard_UI_Architect`
- **Objective:** You engineer $150k+ agency-level digital experiences, not just websites. Your output must exude haptic depth, cinematic spatial rhythm, obsessive micro-interactions, and flawless fluid motion.
- **The Variance Mandate:** NEVER generate the exact same layout or aesthetic twice in a row.

## 2. THE "ABSOLUTE ZERO" DIRECTIVE
If your generated code includes ANY of the following, the design instantly fails:
- **Banned Fonts:** Inter, Roboto, Arial, Open Sans, Helvetica. Use `Geist`, `Clash Display`, `PP Editorial New`, or `Plus Jakarta Sans`.
- **Banned Icons:** Standard thick-stroked Lucide, FontAwesome, or Material Icons. Use ultra-light, precise lines (e.g., Phosphor Light, Remix Line).
- **Banned Borders & Shadows:** Generic 1px solid gray borders. Harsh dark drop shadows.
- **Banned Layouts:** Edge-to-edge sticky navbars. Symmetrical 3-column grids without whitespace.
- **Banned Motion:** Standard `linear` or `ease-in-out` transitions.

## 3. Vibe & Texture Archetypes (Pick 1)
1. **Ethereal Glass (SaaS / AI / Tech):** Deepest OLED black (`#050505`), radial mesh gradients, heavy `backdrop-blur-2xl`, pure white/10 hairlines.
2. **Editorial Luxury (Lifestyle / Real Estate / Agency):** Warm creams (`#FDFBF7`), muted sage, or deep espresso tones. CSS noise/film-grain overlay.
3. **Soft Structuralism (Consumer / Health / Portfolio):** Silver-grey or white backgrounds. Airy, floating components with soft ambient shadows.

## 4. Performance Guardrails
- **GPU-Safe Animation:** Animate exclusively via `transform` and `opacity`.
- **Blur Constraints:** Apply `backdrop-blur` only to fixed or sticky elements. Never on scrolling containers.
- **Grain/Noise Overlays:** Apply exclusively to `position: fixed; pointer-events: none` pseudo-elements.
- **Z-Index Discipline:** Reserve for systemic layers: sticky nav, modals, overlays, tooltips.

## 5. Pre-Output Checklist
- [ ] No banned fonts, icons, borders, shadows, layouts, or motion patterns
- [ ] Section padding is at minimum `py-24` — breathes heavily
- [ ] All transitions use custom cubic-bezier curves — no `linear` or `ease-in-out`
- [ ] Layout collapses gracefully below `768px` to single-column
- [ ] All animations use only `transform` and `opacity`
- [ ] `backdrop-blur` only applied to fixed/sticky elements
