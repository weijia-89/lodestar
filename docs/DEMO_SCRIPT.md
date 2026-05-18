# lodestar 5-minute demo script

> **Status:** v0.1 artifact. The script below references multi-tool reports
> (Aider Week 20, voice synthesis memos, worked escalation) that do not exist
> in v0-min. Rewrite this to a 2-minute single-tool walkthrough when v0-min
> ships, then record at v0.1 scope when the deferred pillars land.
>
> **v0-min substitute:** the README + `docs/WRITEUP.md` + `reports/aider-week.md`
> together carry the demonstration for now. A recording becomes worth making
> once Cline + Continue + voice synthesis + worked escalation are also in
> scope.
>
> **Format (for v0.1 recording):** Screen recording + voiceover. 5:00 hard cap.
> Wei records once; ship the first take that passes the script. No editing.

## 0:00 — Frame (30 seconds)

**On screen:** lodestar README opened in browser.

**Voiceover (30s):**

> "lodestar is a public-source Voice-of-Customer v0 for three open-source
> agentic coding tools. The weekly priority report — a curated top-20 with
> human-written rationale for the priority five — is the demonstration.
> The pipeline underneath is supporting infrastructure."

## 0:30 — Priority report walkthrough (90 seconds)

**On screen:** `reports/2026-W20/aider/priority_report.md` in a Markdown
previewer. Walk through item #1.

**Voiceover (90s):**

> "This is the Aider Week 20 priority report. Issue #1234 — Aider crashes
> on empty Python files. The pipeline ranked it top because of [show
> breakdown: score, engagement, recency, label_weight]. My rationale:
> [Wei reads two sentences]. Customer impact hypothesis: [two sentences].
> Suggested response: [two sentences]. This pattern repeats five times
> per report; the pipeline does the discovery, I do the judgment."

## 2:00 — Voice synthesis memo (90 seconds)

**On screen:** `reports/2026-W20/aider/synthesis.md`. Show the
multi-source grouping (GitHub issues, Reddit, HN).

**Voiceover (90s):**

> "Synthesis memo for the same week. Public-data only — no Discord, no
> proprietary customer interviews. Three sources cross-referenced. The
> synthesis paragraph at the top is mine, written from the quotes below.
> This is what voice of customer looks like when you can't tap private
> telemetry. At Cursor, this would be the public half of a synthesis that
> also pulls in support tickets and product telemetry."

## 4:00 — Worked escalation (30 seconds)

**On screen:** `docs/WORKED_ESCALATION.md` and the Playwright trace viewer.

**Voiceover (30s):**

> "Real bug I found in [tool]. Playwright reproduction takes 30 seconds
> to run. Filed upstream as issue #[N]. Maintainer responded in [time];
> log lives here. This is the escalation discipline scaled."

## 4:30 — Manifest + close (30 seconds)

**On screen:** Brief glimpse of `docs/MANIFEST.md` table of contents.

**Voiceover (30s):**

> "Cursor manifest captures five friction points and three workflows from
> my existing Cursor use. No internal context. The thesis: lodestar
> demonstrates the public-source half of a real VoC program. The private
> half is what I'd build with you."

**End.**
