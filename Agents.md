# AGENTS.md

## Project Context

Project root:

`D:\Chlear Projects\Markdown IT Project\Markdown Dashboard\markdown-it-master`

Current folders:

* `backend/`
* `docs/`
* `skills/`

Core project context files:

* `PRODUCT.md`
* `DESIGN.md`
* `implementation_plan.md`

The Impeccable Style skill is located at:

`skills/impeccable-style-universal`

This is an AI-agent skill folder, not an npm package, app template, or frontend dependency.

Do not install it as a package.

Use it as a UI/UX and frontend design guidance system.

---

## Main Goal

Build this application from scratch using the project documents and Impeccable Style guidance.

This is not only a redesign task.

This is a full product creation task.

Use the `docs/` folder as the source of truth for product requirements, architecture, workflows, features, limits, and implementation rules.

Use Impeccable Style to shape the frontend experience from day one.

This project should be implemented through the sprint plan in:

* `docs/sprints.md`

---

## Required Reading Before Work

Before planning or writing code, Codex must read:

1. `PRODUCT.md`
2. `DESIGN.md`
3. `implementation_plan.md`
4. `docs/file_to_markdown_converter_prd_v2.md`
5. `docs/file_to_markdown_architecture.md`
6. `docs/data_models.md`
7. `docs/api_reference.md`
8. `docs/storage_and_security.md`
9. `docs/environment_config.md`
10. `docs/sprints.md`
11. `skills/impeccable-style-universal/README.txt`
12. `skills/impeccable-style-universal/.codex/`

The `.codex` folder is the relevant Impeccable folder for Codex.

Other folders such as `.claude`, `.cursor`, `.gemini`, `.kiro`, `.opencode`, `.qoder`, `.trae`, etc. are for other AI tools and should not be treated as primary Codex instructions unless explicitly asked.

---

## Source Of Truth

Use these files for these decisions:

* Product behavior and MVP scope: `docs/file_to_markdown_converter_prd_v2.md`
* System architecture: `docs/file_to_markdown_architecture.md`
* Database tables and status lifecycle: `docs/data_models.md`
* FastAPI endpoints, Swagger/OpenAPI behavior, request/response contracts: `docs/api_reference.md`
* Storage, source deletion, security, access control: `docs/storage_and_security.md`
* Environment variables and runtime config: `docs/environment_config.md`
* Sprint execution order: `docs/sprints.md`
* Overall build checklist: `implementation_plan.md`
* Product voice, target users, and UX goals: `PRODUCT.md`
* Visual design system and UI constraints: `DESIGN.md`

If files disagree, use the more specific file for that topic and update the conflicting doc before implementing.

---

## First-Principles Build Rule

Build the app based on what the product must do.

Do not start from random templates.

Do not blindly copy Impeccable files.

First understand:

1. Who the user is
2. What problem the app solves
3. What the main workflow is
4. What data moves through the system
5. What screens are required
6. What backend services are required
7. What frontend experience makes the workflow simple

Then build.

---

## Product Direction

This project is a Markdown/File Conversion Dashboard.

The app should help users upload documents/files and convert them into clean Markdown or LLM-friendly output.

The UX should be simple, direct, and premium.

The product should feel like a clean SaaS tool, not a technical script UI.

The user should understand the workflow without needing technical knowledge.

Target users:

* Internal team members
* Developers
* AI engineers
* Researchers
* Agencies
* Non-technical users who need a simple document-to-Markdown workflow

The UX must feel:

* premium
* minimal
* calm
* enterprise-grade
* extremely intuitive
* uncluttered
* self-explanatory

---

## UX Principles

Use Impeccable Style to make the app:

* clean
* modern
* premium
* simple
* fast-feeling
* self-explanatory
* responsive
* easy for non-technical users
* suitable for a SaaS dashboard

Prefer:

* clear upload flow
* step-by-step conversion journey
* obvious primary actions
* clean dashboard layout
* useful empty states
* clear loading states
* conversion progress feedback
* simple language
* minimal clutter
* good spacing
* readable typography
* reusable components

Avoid:

* overcomplicated layouts
* unnecessary animations
* vague buttons
* technical jargon
* confusing navigation
* fake features not present in docs
* adding scope not approved in docs
* busy dashboards
* complex enterprise admin-panel feeling
* too many cards
* too many colors
* visual noise

---

## App Creation Scope

Codex may create:

* frontend app structure
* backend app structure
* upload screen
* conversion dashboard
* file history screen
* conversion status UI
* settings/account UI if required by docs
* login/auth UI if required by docs
* reusable frontend components
* API routes/services as required
* database models only if required by docs
* queue/job processing only if required by docs
* documentation updates

Codex must not invent major product features outside the docs.

---

## Architecture Rule

Use the project docs as the source of truth.

If docs define architecture, follow them.

If docs are incomplete, Codex must make the smallest reasonable implementation decision and clearly explain it before coding.

Prefer simple architecture first.

Do not overengineer.

Build the smallest strong SaaS MVP that can work.

Hard architecture decisions:

* Do not use Cloudflare R2.
* Do not permanently store source documents.
* Store source files only temporarily during conversion.
* Delete source files after success, failure, or timeout.
* Store only generated Markdown `.md` outputs in Supabase Storage.
* Store metadata/history/status in Supabase Postgres.
* Use the in-app conversion limiter for the MVP, not Redis or BullMQ.
* Build the admin dashboard later, not in this MVP.

---

## Backend Rule

Backend must be built around the actual product workflow:

1. user uploads file
2. file is validated
3. file is stored or temporarily processed
4. file is converted
5. converted Markdown/output is returned or saved
6. user can download/copy/view result

Do not create backend abstractions before they are needed.

Do not add unnecessary microservices.

Do not add complex queue systems unless the docs require them or file processing clearly needs async handling.

Use the MarkItDown conversion implementation already present under:

`backend/markitdown-main/`

Important:

* The product backend should use the MarkItDown conversion package/code it needs.
* Do not copy unrelated upstream repository material into the product app runtime.
* Prefer using the local package at `backend/markitdown-main/markitdown-main/packages/markitdown`.
* Keep sample plugins, upstream tests, MCP package, OCR package, and unrelated upstream files out of the product backend unless a later approved requirement needs them.

---

## Frontend Rule

The frontend should be designed from scratch using Impeccable Style principles.

The first version should include a clear user journey:

1. Landing or dashboard entry
2. Upload area
3. File validation feedback
4. Conversion progress
5. Markdown preview/result
6. Copy/download actions
7. Conversion history if required

Use clean SaaS UI patterns.

The interface should make the user feel:

“I know exactly what to do next.”

Typography must be sans-serif only. Follow `DESIGN.md`.

Do not use:

* serif fonts
* display fonts
* gradient text
* glassmorphism
* decorative orbs
* nested cards
* identical card grids everywhere
* hero metric templates

---

## Implementation Workflow for Codex

When asked to build the app, Codex must follow `docs/sprints.md`.

If the user asks for a plan before implementation, output:

1. What docs were found
2. What Impeccable files were read
3. What app architecture is proposed
4. What frontend screens will be created
5. What backend modules will be created
6. What files/folders will be added or changed
7. What assumptions are being made
8. What will be built first

After the plan, Codex may implement only when instructed.

If the user says “implement directly,” Codex may proceed without waiting.

Sprint order:

1. Sprint 0: project setup and MarkItDown integration
2. Sprint 1: database, storage, and auth foundation
3. Sprint 2: conversion API
4. Sprint 3: authenticated frontend shell
5. Sprint 4: upload, status, preview, download
6. Sprint 5: history and finish pass

---

## Hard Rules

Do not:

* treat Impeccable as an npm dependency
* install Impeccable
* copy random files blindly
* ignore docs
* invent unapproved product scope
* create a bloated enterprise architecture too early
* change product intent
* overcomplicate the MVP

Do:

* read docs first
* read Impeccable skill first
* build from first principles
* keep architecture simple
* create clean, premium UX
* explain assumptions
* preserve clarity
* build incrementally

---

## Codex Default Behavior

For every major task, Codex should think in this order:

1. Product requirements
2. User workflow
3. Data flow
4. Backend needs
5. Frontend screens
6. UI/UX quality
7. Implementation files
8. Testing/checks

The app must be useful first, beautiful second, and scalable third.

Do not make a beautiful useless shell.

Do not make a technically complex but confusing app.

Build a working product with a clean SaaS experience.
