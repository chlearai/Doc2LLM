# Design Context

## Design Direction

Create a minimal, premium, calm product UI for an internal file-to-Markdown dashboard.

This is a task-first SaaS dashboard, not a marketing site. The interface should feel quiet, precise, and trustworthy.

## Scene

A developer, researcher, or operations teammate is working during the day on a laptop or desktop monitor. They need to quickly convert a document for AI or knowledge-work use, verify the Markdown, copy or download it, and move on.

This scene supports a light interface with restrained contrast, generous whitespace, and dense-but-readable working areas.

## Theme

Use a light theme by default.

The UI should avoid pure white and pure black. Use softly tinted neutrals so the surface feels polished without becoming decorative.

## Color Strategy

Use a restrained product palette:

- Tinted neutral background
- White-adjacent content surfaces
- One primary accent for conversion actions and focus states
- Semantic colors only for status and feedback

Recommended token direction:

```css
:root {
  --background: oklch(0.982 0.006 250);
  --surface: oklch(0.996 0.004 250);
  --surface-muted: oklch(0.955 0.007 250);
  --border: oklch(0.88 0.01 250);
  --text: oklch(0.22 0.012 250);
  --text-muted: oklch(0.48 0.012 250);
  --primary: oklch(0.52 0.11 245);
  --primary-hover: oklch(0.46 0.12 245);
  --success: oklch(0.56 0.12 155);
  --warning: oklch(0.72 0.12 85);
  --error: oklch(0.58 0.16 28);
}
```

Color rules:

- Use the primary accent only for primary actions, active nav, focus rings, and selected states.
- Use semantic colors only when there is real status.
- Do not create a multicolor dashboard.
- Do not use gradient text.
- Do not use decorative color blobs.

## Typography

Use sans-serif typography only. Prefer a system UI stack or Inter.

Recommended stack:

```css
font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
```

Typography rules:

- Use a compact product scale.
- Do not use display fonts.
- Do not use serif fonts.
- Do not use fluid viewport-based font sizing.
- Keep headings clear but not oversized.
- Body copy should be short and useful.
- Labels and buttons should be specific.

Suggested scale:

```css
--text-xs: 0.75rem;
--text-sm: 0.875rem;
--text-base: 1rem;
--text-lg: 1.125rem;
--text-xl: 1.25rem;
--text-2xl: 1.5rem;
```

## Layout

Use predictable product structure:

- Top bar or compact sidebar navigation
- Main upload/work area
- Recent conversions/history area
- Detail view for preview and actions

Layout rules:

- Avoid busy dashboards.
- Avoid too many cards.
- Do not nest cards.
- Use dividers, spacing, and alignment instead of framing every section.
- Keep the upload flow visually primary.
- Keep history useful but secondary.
- Make responsive behavior structural: stack panels on mobile, preserve clear action order.

Preferred dashboard shape:

```txt
App shell
  Header: product name, current user, sign out
  Main
    Upload/work area
    Recent conversions
```

Preferred conversion detail shape:

```txt
Header row: file name, status, actions
Main split:
  Left or top: conversion metadata/status
  Right or bottom: Markdown preview
```

## Component Style

Use familiar components:

- Buttons
- Inputs
- Upload dropzone
- Status badges
- Progress/status row
- Table or simple list for history
- Markdown preview panel
- Toasts for copy/download feedback

Component rules:

- Buttons should have default, hover, focus, active, disabled, and loading states.
- Primary button label should be action-specific: `Convert file`.
- Secondary actions: `Copy Markdown`, `Download .md`.
- Empty states should explain the next useful action.
- Loading states should use skeletons or specific status text, not generic spinners where content can be structured.

## Status UI

Statuses should be calm and readable:

- `PENDING`: Waiting
- `PROCESSING`: Processing
- `COMPLETED`: Completed
- `FAILED`: Failed
- `DELETED`: Deleted

Status copy examples:

- Waiting for a conversion slot.
- Converting your file. This usually takes less than a minute.
- Markdown is ready.
- Conversion failed. Upload the file again or try a smaller document.

## UX Writing

Use clear labels:

- Convert file
- Copy Markdown
- Download `.md`
- View history
- Upload another file
- Sign out

Avoid:

- Submit
- OK
- Yes/No
- Technical backend terms
- Long explanatory paragraphs

Error formula:

```txt
What happened. Why it happened. What to do next.
```

Examples:

- PDF is too large. PDF files can be up to 25 MB. Choose a smaller file and try again.
- Queue is full. Too many files are waiting right now. Try again in a few minutes.
- Conversion timed out. The file took more than 5 minutes to process. Try a smaller or simpler document.

## Motion

Use minimal motion:

- 150-200ms transitions
- State changes only
- No decorative page-load sequences
- No bounce or elastic motion

## Accessibility

Requirements:

- Keyboard-accessible upload and action controls.
- Visible focus states.
- Icon buttons must have `aria-label`.
- Status must not rely on color alone.
- Preview area should preserve readable line height.
- Error messages must be associated with the relevant control.

## Impeccable Constraints

Do not use:

- Gradient text
- Glassmorphism
- Decorative orbs
- Identical card grids
- Nested cards
- Hero metric templates
- Side-stripe accent borders
- Busy color systems

## Visual Quality Bar

The interface should feel like a focused internal tool from a high-quality SaaS company:

- Clear hierarchy
- Quiet confidence
- Strong alignment
- Intentional spacing
- Specific copy
- No visual clutter
- No decorative complexity
