# Design System Documentation: The Academic Atelier

## 1. Overview & Creative North Star
**Creative North Star: "The Prestigious Conservatory"**

This design system moves away from the sterile, "SaaS-standard" dashboard and toward a high-end editorial experience. We are not just building a booking tool; we are designing a digital concierge for a prestigious institution. 

The aesthetic breaks the traditional "box-in-a-box" grid through **Intentional Asymmetry** and **Tonal Depth**. By utilizing wide margins, overlapping display typography, and a "No-Line" philosophy, we create a space that feels authoritative yet breathable. We prioritize the "Human Scale"—ensuring that while the institution is grand, the interface feels personal, curated, and effortless.

---

## 2. Colors & Surface Architecture

The palette transitions from the deep, scholarly authority of `primary` (#00236f) to the illuminating clarity of `tertiary` gold.

### The "No-Line" Rule
**Borders are a failure of hierarchy.** In this system, explicit 1px solid borders for sectioning are strictly prohibited. Boundaries must be defined through:
- **Background Shifts:** Placing a `surface-container-lowest` card (#ffffff) against a `surface-container-low` (#f2f4f6) background.
- **Tonal Transitions:** Using subtle shifts in the surface tier to imply containment.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers—like stacked sheets of fine vellum.
- **Base Layer:** `surface` (#f7f9fb)
- **Content Regions:** `surface-container-low` (#f2f4f6)
- **Interactive Cards:** `surface-container-lowest` (#ffffff) for maximum "pop."
- **Nesting:** When placing a search bar inside a header, use `surface-container-high` (#e6e8ea) to create a "recessed" feel without using an inner shadow.

### The "Glass & Gradient" Rule
To elevate the dashboard, use **Glassmorphism** for floating navigation or quick-action panels.
- **Token:** `surface-container-lowest` at 80% opacity with a `24px` backdrop-blur.
- **Signature Gradients:** For primary CTAs, use a linear gradient from `primary` (#00236f) to `primary_container` (#1e3a8a) at a 135-degree angle. This adds "soul" and prevents the gold accents from feeling flat.

---

## 3. Typography: Editorial Authority

We use a dual-typeface strategy to balance academic tradition with modern functionality.

*   **Display & Headlines (Manrope):** Chosen for its geometric confidence. Use `display-lg` for welcome states and `headline-sm` for section titles.
*   **Body & UI (Inter):** The workhorse. Inter provides exceptional legibility for complex booking forms and schedules.

**The Signature Scale:**
- **Asymmetric Headers:** Pair a `display-sm` (Manrope) page title with a `label-md` (Inter) uppercase subtitle tracked out to `0.1em`.
- **High Contrast:** Always ensure `on_surface_variant` (#444651) is used for secondary metadata to maintain a clear visual path for the user’s eye.

---

## 4. Elevation & Depth

### The Layering Principle
Avoid the "standard shadow" look. Depth is primarily achieved via **Tonal Layering**. 
- Place a `surface-container-lowest` object on a `surface-container` background to create a soft, natural lift.

### Ambient Shadows
When a component must "float" (e.g., a booking confirmation modal):
- **Blur:** `32px` to `64px`
- **Opacity:** 4% - 6%
- **Color:** Use a tinted version of `on_surface` (#191c1e) rather than pure black to simulate natural light.

### The "Ghost Border" Fallback
If a border is required for accessibility (e.g., in a high-density data table):
- Use `outline-variant` (#c5c5d3) at **15% opacity**. 100% opaque borders are forbidden.

---

## 5. Components

### Buttons: The Weighted Action
- **Primary:** Gradient fill (`primary` to `primary_container`), `xl` (1.5rem) roundedness. No border.
- **Secondary:** `surface-container-high` background with `on_primary_fixed_variant` text.
- **Tertiary (The "Academic Link"):** No container. `primary` text with a `tertiary` (gold) 2px underline that appears on hover.

### Cards: The Floating Canvas
- **Style:** No borders. Background `surface-container-lowest`. 
- **Separation:** Forbid the use of divider lines within cards. Use **8px / 16px / 24px vertical white space** to separate the header, body, and footer.

### Input Fields: Recessed Clarity
- **Style:** Background `surface-container-high`. 
- **Focus State:** No thick glow. Transition the background to `surface-container-lowest` and add a `1px` Ghost Border in `primary`.

### Specialized Component: The Booking Timeline
- Use `tertiary_fixed` (Gold) for "Current Time" indicators.
- Use `secondary_container` for "Pending" slots and `primary` for "Confirmed" slots.
- Avoid grid lines; use a soft `surface-variant` subtle fill for alternate hours.

---

## 6. Do’s and Don’ts

### Do:
- **Do** use `xl` (1.5rem) corner radii for large cards to soften the academic environment.
- **Do** allow typography to overlap slightly with background elements for a "magazine" feel.
- **Do** use `tertiary` (Gold) sparingly—it is a highlighter, not a primary surface color.

### Don't:
- **Don't** use 100% black text; always use `on_surface` for a softer, premium feel.
- **Don't** use standard "drop shadows" on every card. If everything floats, nothing is important.
- **Don't** use dividers or lines to separate list items; let the white space do the work.
- **Don't** use "Blue" for errors. Even though the brand is blue, always use the `error` (#ba1a1a) tokens for critical feedback.