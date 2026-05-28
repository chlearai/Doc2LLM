# Product Context

## Product Name

Doc2LLM

## Register

product

## Product Purpose

Doc2LLM helps internal teams convert documents into clean, AI-ready Markdown through a secure, simple dashboard.

Users sign in, upload a supported file, wait for conversion, preview the Markdown, copy it, or download the generated `.md` file. The source document is never stored permanently.

## Target Users

- Internal team members
- Developers
- AI engineers
- Researchers
- Agencies
- Non-technical users who need a simple document-to-Markdown workflow

## Primary User Need

Users need a calm, reliable way to turn documents into Markdown without using scripts, manual copy-paste workflows, or technical conversion tools.

## Core Workflow

```txt
Sign in
Upload file
Wait for conversion
Preview Markdown
Copy or download output
Return to history when needed
```

## Product Principles

- Make the next action obvious.
- Keep the dashboard focused on conversion, status, preview, and history.
- Avoid admin complexity in the MVP.
- Avoid permanent source file storage.
- Use plain language instead of technical jargon where possible.
- Optimize for trust, clarity, and speed.
- Prefer fewer screens with stronger workflows over many shallow pages.

## Experience Goals

The UX must feel:

- Premium
- Minimal
- Calm
- Enterprise-grade
- Extremely intuitive
- Uncluttered
- Self-explanatory

## Anti-References

Avoid:

- Busy dashboards
- Complex enterprise admin panels
- Too many cards
- Too many colors
- Visual noise
- Decorative metrics
- Marketing-page composition inside the app
- Technical script-like UI
- Cluttered file manager interfaces

## Feature Scope

MVP includes:

- Supabase Auth login and sign up
- File upload
- File validation
- Conversion status
- Markdown preview
- Copy Markdown
- Download `.md`
- Conversion history
- Basic account/sign-out area

MVP excludes:

- Admin dashboard
- Cloudflare R2
- Billing
- Team management
- Complex roles
- OCR
- Markdown search
- Permanent source file storage

## Storage Positioning

The product stores only generated Markdown outputs in Supabase Storage. Uploaded source files are temporary and deleted after success, failure, or timeout.

This should be reflected in the UI as a trust signal, but not over-explained.

## Voice And Tone

Voice:

- Clear
- Direct
- Calm
- Competent
- Human

Tone by moment:

- Upload: confident and simple.
- Processing: reassuring and specific.
- Success: brief and useful.
- Failure: clear, non-blaming, and actionable.
- Empty states: helpful without sounding promotional.

Preferred terms:

- Sign in
- Convert file
- Markdown
- Download `.md`
- Copy Markdown
- History
- Processing
- Failed
- Completed

Avoid:

- Submit
- OK
- Oops
- Magic
- AI-powered unless the feature explicitly uses AI
- Enterprise jargon

## Success Criteria

The MVP succeeds when:

- A non-technical user can convert a document without help.
- A technical user trusts the workflow and output handling.
- Users can understand status and errors immediately.
- The UI feels calm under both empty and active states.
- The implementation remains small enough for one team to maintain.
