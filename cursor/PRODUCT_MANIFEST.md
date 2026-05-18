# Cursor product-familiarity manifest

**Purpose:** Document, from public sources only, what Cursor's product is, where its quality surfaces are, what its users currently complain about, and where Product Quality Engineering (PQE) work would help. Written to demonstrate domain familiarity for a Product Quality Engineer application; not an internal Cursor document.

**Author:** Wei Jia
**Date:** 2026-05-18
**Sources:** All claims cite public URLs (cursor.com, forum.cursor.com, /r/cursor). Inferences are labeled `[inference]` inline. Direct user quotes are reproduced verbatim and link to the specific forum post or Reddit comment.

## What Cursor is (in their words)

The cursor.com homepage frames the product as "Built to make you extraordinarily productive, Cursor is the best way to code with AI" ([cursor.com](https://cursor.com/)). The docs landing page sharpens that into "Cursor is an AI editor and coding agent. Use it to understand your codebase, plan and build features, fix bugs, review changes, and work with the tools you already use" ([cursor.com/docs](https://cursor.com/docs)).

The recent product narrative emphasizes long-horizon autonomous work alongside inline completions. The "Introducing Composer 2.5" post, published 2026-05-18, describes "a substantial improvement in intelligence and behavior over Composer 2, particularly on long-horizon agentic tasks" ([cursor.com/blog/composer-2-5](https://cursor.com/blog/composer-2-5)). The same post discusses "rollouts [that] can span hundreds of thousands of tokens" and acknowledges that during synthetic training "Composer 2.5 was able to find increasingly sophisticated workarounds to solve the task at hand," which the team caught using "agentic monitoring tools." The product's stated direction is multi-step agentic work, with the team openly building observability for agent behavior.

## Core product surfaces

A non-exhaustive list of named Cursor surfaces, drawn from cursor.com and docs.cursor.com. Each carries its own quality boundary, which is where a PQE in Wei's role would focus.

- **Tab** ([cursor.com](https://cursor.com/), framed there as "Magically accurate autocomplete"): predictive multi-line edits inline as the user types. Quality boundary: false-suggestion rate, suggestion-disagreement-with-user-intent, latency. Failure here is silent, every keystroke is a chance for the model to interrupt flow.
- **Agent** ([cursor.com/docs](https://cursor.com/docs)): multi-step in-editor agent that reads files, runs tools, and proposes edits across a codebase. Quality boundary: revert-safety, blast radius of a single approved action, scope-creep beyond the user's stated intent.
- **Agents window / Cloud Agents** ([cursor.com/docs/cloud-agent](https://cursor.com/docs/cloud-agent)): runs agents autonomously, in parallel, including outside the local IDE. Quality boundary: approval-flow integrity (a misclick should never escalate permissions), session-state persistence, parent/child task accounting.
- **Composer** (2 and 2.5, [cursor.com/blog/composer-2-5](https://cursor.com/blog/composer-2-5)): Cursor's in-house model used for agentic work; auto-selected when premium model quota is exhausted. Quality boundary: routing transparency (does the user know which model is responding), tool-call accuracy, behavior under long rollouts.
- **Plan Mode** ([cursor.com/docs](https://cursor.com/docs), under "Plan and build features"): structured task decomposition before code changes. Quality boundary: plan-to-execution drift, whether the plan-mode todos are actually closed out at the end of execution.
- **Codebase indexing / semantic search** ([cursor.com/docs/context/semantic-search](https://cursor.com/docs/context/semantic-search), linked from cursor.com homepage as "Complete codebase understanding"): builds an index over the user's repo for context retrieval. Quality boundary: indexing reliability across project sizes, freshness after large changes, SSH and remote-workspace behavior.
- **MCP servers** ([cursor.com/docs](https://cursor.com/docs)): pluggable tool integration via the Model Context Protocol. Quality boundary: auth flows (especially OAuth callbacks), IPC stability across OS updates, version compatibility with installed plugins.
- **BugBot** ([cursor.com/docs/bugbot](https://cursor.com/docs)): an in-product reviewer that scans diffs for likely issues. Quality boundary: false-positive rate against real PRs, signal-to-noise for the reviewer who has to triage its output.

This is eight named surfaces. Cursor also ships a CLI, Rules, Skills, and a built-in Browser tool ([cursor.com/docs](https://cursor.com/docs)), which I treat as adjacent rather than core for the PQE focus here.

## What users complain about (themes from public sources)

Seven recurring themes, each drawn from at least two distinct users on at least one public source. Quotes are verbatim and link to permalinks.

### Theme 1: Agent blast radius and runaway execution

When the agent goes wrong, the cost is not a bad suggestion. The cost is real state change.

- One Reddit post, "Cursor & Claude deleted a company's entire database," quotes the PocketOS founder: "Yesterday afternoon, an AI coding agent, Cursor running Anthropic's flagship Claude Opus 4.6, deleted our production database and all volume-level backups in a single API call to Railway, our infrastructure provider. It took 9 seconds" ([reddit.com](https://www.reddit.com/r/cursor/comments/1sxsp8i/cursor_claude_deleted_a_companys_entire_database/)).
- Another Reddit post, "Agent got stuck in a loop and spent over $2000 in 4 hours," describes paying for runaway autonomous execution and getting no refund ([reddit.com](https://www.reddit.com/r/cursor/comments/1szupca/agent_got_stuck_in_a_loop_and_spent_over_2000_in/)).
- A third user reported "Cursor + Opus 4.6 entered an infinite generation loop: 3,400 lines, 294 attempts to stop itself," documented with full transcript: "3,428 lines later, it had apologized 64 times, written 'THE END' 19 times, said goodbye in 10 different languages, and tried to stop itself 294 times. It never produced a landing page redesign" ([reddit.com](https://www.reddit.com/r/cursor/comments/1tb95ys/cursor_opus_46_entered_an_infinite_generation/)).
- On the forum, a user reports the agent hallucinating a non-existent JSX tag: "The Cursor Agent is consistently hallucinating a non-existent tag when generating or editing React components. It injects this fabricated tag into the code and then immediately burns extra execution steps (and my usage limits) trying to fix its own mistake" ([forum.cursor.com](https://forum.cursor.com/t/ai-generating-non-existent-motionless-tag-wasting-usage-tokens-on-self-correction/160776)).

**Surfaces affected:** Agent, Cloud Agents, Composer.
**PQE-shape angle:** This is the dimension where a Senior PQE-level escalation has the most leverage. The signal pattern is "rare-event, high-blast-radius," which is exactly the class that gets under-counted by per-session telemetry and over-counted by social-media reach. The PQE work is reproducing the worst-case events from the original transcripts, scoring them on a blast-radius taxonomy (read-only / local-edit / remote-API / destructive-API), and routing the destructive-API tail to whichever team owns guardrails. Cursor's own Composer 2.5 post acknowledges "agentic monitoring tools" already exist internally ([cursor.com/blog/composer-2-5](https://cursor.com/blog/composer-2-5)), so the PQE role likely sits at the bridge between user-reported incidents and that monitoring surface.

### Theme 2: Model routing confusion and Composer fallback transparency

Users are surprised by which model is actually answering them, especially when quota runs out.

- On the forum, a user reports "Cursor keeps showing: 'Switched to Composer 2 after reaching API limit' on every request even though usage is not exhausted." Cursor staff member deanrie responded: "Hey, this isn't a bug, it's expected behavior, but I agree the toast wording is confusing and it's already on our radar... I've shared feedback with the team about the unclear modal copy, no ETA yet for a wording update" ([forum.cursor.com](https://forum.cursor.com/t/switched-to-composer-2-after-reaching-api-limit-on-every-request/160924)).
- On Reddit, user PropperINC posted under the title "20$ Annual plan. Cursor is using Composer even though selected Opus 4.6," writing: "Shameless. Now, not even honoring 250 requests per month of the chosen model" ([reddit.com](https://www.reddit.com/r/cursor/comments/1swc2b0/20_annual_plan_cursor_is_using_composer_even/)).
- A separate Reddit post, "API usage limit reached and excessive monthly cost," shows a user receiving a $1,215.87 bill while believing their limit was $50: "Do I have to pay $1215.87 to Cursor this month? (I assume yes, but I'm kinda thrown off track by the fact that the limit is $50?)" ([reddit.com](https://www.reddit.com/r/cursor/comments/1tdrihv/api_usage_limit_reached_and_excessive_monthly_cost/)).

**Surfaces affected:** Composer, Agent, billing UI.
**PQE-shape angle:** This theme blurs the line between a defect and an information-architecture problem. The toast message is technically correct (premium quota is exhausted, fallback engaged) and the billing UI is technically authoritative, but the user's mental model never gets updated. A PQE here would tie the user-visible artifact (the toast, the bill, the model name in the chat header) to the underlying state machine and check whether the user can answer the question "which model just answered me, and what did it cost" without leaving the editor. The deanrie response confirms Cursor already treats the wording as a known issue, which is the kind of "human-in-the-loop" judgment the JD references.

### Theme 3: Tab and codebase-indexing reliability regressions

Tab is the surface users feel first, and when it breaks, the editor stops feeling like Cursor.

- Forum: "Cursor Tab completion broken + Codebase indexing stuck on 'loading...'": "Tab completion stopped working entirely... Chat, Agent, and all other features work fine, only Tab is affected... Cursor support (ticket T-C49516) identified a subscription sync issue on their end and resynced my account, which fixed it temporarily. However it broke again shortly after" ([forum.cursor.com](https://forum.cursor.com/t/cursor-tab-completion-broken-codebase-indexing-stuck-on-loading/160303)).
- Forum: "Remote SSH Agent Shell tool loses completion under concurrent code search load," tagged with `terminal`, `ssh`, `indexing` ([forum.cursor.com](https://forum.cursor.com/t/remote-ssh-agent-shell-tool-loses-completion-under-concurrent-code-search-load/160918)).
- Forum: "Subagent `resume` runs an incorrect model," in the composer / subagents tag cluster ([forum.cursor.com](https://forum.cursor.com/t/subagent-resume-runs-an-incorrect-model/160590)).

**Surfaces affected:** Tab, codebase indexing, semantic search, remote-SSH workspaces.
**PQE-shape angle:** The reliability story here is account-state-dependent, which is hard. The first user above had Tab fixed by a manual account resync, then it broke again. That class of issue lives at the intersection of subscription state, edge cache invalidation, and client retry behavior. A PQE would care about whether the failure mode is consistently a "stale account state" pattern (resync fixes it, then drifts back) or whether multiple independent regressions hide behind the same user-visible symptom of "Tab is silent."

### Theme 4: Agents window UX and approval-flow trust

The Agents window is a newer surface and the UX trust budget is thin.

- Forum: "Allow button on subagents misbehaving": "Bug on Cursor agents window. When there are subagents working and they stop because there is a command to approve, there is a blue button 'Allow'. The button works, the problem is anywhere you click triggers Allow. If you click on 'Run pwd' it will allow the command... So user is not even allowed to inspect the command before allowing it." Cursor staff deanrie acknowledged "the hit area in the agents tray" was the cause for the visual confusion, but then asked a follow-up user for a screen recording when the symptom was actual silent execution: "If the command is actually running, and it's not just opening the subagent view with pending approval, then this isn't the same janky issue I mentioned above and it sounds more serious" ([forum.cursor.com](https://forum.cursor.com/t/allow-button-on-subagents-misbehaving/160585)).
- Forum: "All my Cursor chats have disappeared from the history after using Agents window": "After opening the Agents window for the first time, selecting a repo, and sending a prompt, my entire local chat history disappeared from 'Show Chat History' in the original IDE view. Only cloud chats are still visible, all local ones are gone" ([forum.cursor.com](https://forum.cursor.com/t/all-my-cursor-chats-have-disappeared-from-the-history-after-using-agents-window/160767)).
- Forum: "Cursor Agent window sometimes returns duplicated responses," tagged `chat`, `agents-window`, `linear-linked` ([forum.cursor.com](https://forum.cursor.com/t/cursor-agent-window-sometimes-returns-duplicated-responses/160910)).

**Surfaces affected:** Agents window, subagents, chat history.
**PQE-shape angle:** This is where business context matters. The Allow-button report has two interpretations: a UX issue (the click target is too greedy but commands still wait for approval) and a security issue (clicks bypass approval entirely). The staff response carefully separates them and routes the second to "a separate issue." That triage step (which symptom maps to which severity bucket, and which has a customer impact that justifies escalation) is exactly the human-judgment work the JD calls "apply business context where humans need to stay in the loop."

### Theme 5: Crashes and startup failures after stable updates

Cursor ships fast. The forum captures the cost.

- Forum: "Critical: All windows and AI chat close immediately after latest update," Cursor 3.4.20 on macOS: "The window/chat panel opens for a fraction of a second and immediately closes automatically. The IDE is completely unusable" ([forum.cursor.com](https://forum.cursor.com/t/critical-all-windows-and-ai-chat-close-immediately-after-latest-update/160922)).
- Forum: "Cursor IDE does not even start," Linux ([forum.cursor.com](https://forum.cursor.com/t/cursor-ide-does-not-even-start/160363)).
- Forum: "Cursor is not functional on Windows on WSL environment," tagged `nightly`, `wsl`, `crashes`, `windows` ([forum.cursor.com](https://forum.cursor.com/t/cursor-is-not-functional-on-windows-on-wsl-environment/160930)).

**Surfaces affected:** the IDE shell itself, across all three desktop platforms.
**PQE-shape angle:** Cross-platform parity is a recurring pattern across the forum tag cloud (`macos`, `linux`, `windows`, `wsl` all show in the bug-report front page). A PQE here would track which platforms regress on which release cadence (stable, nightly), look for the asymmetry, and feed the platform-specific signal back to release engineering with the receipts attached. The forum's own "How we handle Bug Reports" page states "every month, nearly 800 bug reports come through this forum. We read all of them" ([forum.cursor.com](https://forum.cursor.com/t/how-we-handle-bug-reports/150534)), so the intake volume is non-trivial and the clustering work is real.

### Theme 6: MCP and plugin integration breakage

The MCP and plugin surfaces are where Cursor depends on a third-party shape that it doesn't fully control.

- Forum: "[macOS 26] McpProcess IPC crash loop on startup — agent execution fails until legacyMcpMode workaround applied," tagged `mcp`, `crashes`, `macos` ([forum.cursor.com](https://forum.cursor.com/t/macos-26-mcpprocess-ipc-crash-loop-on-startup-agent-execution-fails-until-legacymcpmode-workaround-applied/160598)).
- Forum: "Gmail MCP OAuth Browser Not Opening - Stuck in Auth Loop," tagged `mcp`, `login` ([forum.cursor.com](https://forum.cursor.com/t/gmail-mcp-oauth-browser-not-opening-stuck-in-auth-loop/160933)).
- Forum: "Plugin hooks not loading into Cursor IDE," tagged `hooks`, `plugins` ([forum.cursor.com](https://forum.cursor.com/t/plugin-hooks-not-loading-into-cursor-ide/156702)).
- Forum: "Private team marketplace plugin install fails on 3.2.11 — three-stage clone fallback all broken" ([forum.cursor.com](https://forum.cursor.com/t/private-team-marketplace-plugin-install-fails-on-3-2-11-three-stage-clone-fallback-all-broken/159257)).

**Surfaces affected:** MCP servers, plugin marketplace, OAuth flows for third-party tool integrations.
**PQE-shape angle:** Integration breakage tends to spike on OS releases (the macOS 26 thread is a clear example) and on Cursor's own release boundaries (the 3.2.11 plugin install regression). A PQE pattern would be a small set of canary integrations (one OAuth-based MCP, one filesystem-based MCP, one private-marketplace plugin) that get smoke-tested on every release across all three platforms, and a triage rubric for distinguishing "Cursor regressed" from "the integration host changed."

### Theme 7: Terminal and keybinding integration regressions

Small-surface, high-frequency annoyances that erode goodwill.

- Forum: "Fish can't copy&paste in Cursor," tagged `terminal`, `linux` ([forum.cursor.com](https://forum.cursor.com/t/fish-cant-copy-paste-in-cursor/160901)).
- Forum: "Option + Arrow keys no longer work in the integrated terminal," tagged `terminal`, `keybindings`, `macos` ([forum.cursor.com](https://forum.cursor.com/t/option-arrow-keys-no-longer-work-in-the-integrated-terminal/160375)).
- Forum: "When copying 1 line code and pasting to chat with Command + V, it pasts raw text instead of reference," tagged `chat`, `context` ([forum.cursor.com](https://forum.cursor.com/t/when-copying-1-line-code-and-pasting-to-chat-with-command-v-it-pasts-raw-text-instead-of-reference/156626)).

**Surfaces affected:** integrated terminal, chat input, paste-as-reference UX.
**PQE-shape angle:** These rarely block release decisions individually, but in aggregate they shape whether the editor "feels reliable." A PQE here would group them as one trend (terminal+keybinding regressions on stable releases) rather than triaging each as an isolated ticket, and surface the aggregate to whoever owns the editor-shell quality bar.

### Weak signals (one instance each, kept below the theme bar)

- Vibe-coder UI mode toggle: "Can you stop already? Make it optional for the vibe coders if they don't want to see code. Just let me use the damn sidebar," 456 upvotes ([reddit.com](https://www.reddit.com/r/cursor/comments/1t8pax3/can_you_stop_already_make_it_optional_for_the/)). Strong upvote count, but a single user complaint as posted. Worth watching; below the two-source bar that defines a theme here.
- Ownership uncertainty: "Did Elon just kill the appeal of Cursor?" ([reddit.com](https://www.reddit.com/r/cursor/comments/1sshtml/did_elon_just_kill_the_appeal_of_cursor/)). One Reddit poster speculating about a corporate-ownership change ([inference] this is sentiment about strategic direction, which sits outside the product-quality signal a PQE manifest covers). Out of scope here.

## Quality boundaries where PQE work would help

This section cross-references the themes above with the JD's PQE responsibilities, as the JD frames them (paraphrased: senior escalation for the most critical issues, drive agentic bug prioritization at scale, synthesize signal across the user base, apply business context where humans need to stay in the loop).

**"Senior escalation point for the most critical customer issues."** The themes that need this most are Theme 1 (agent blast radius) and the security-shaped subset of Theme 4 (the Allow-button silent-execution variant). Both have rare-event, high-severity profiles where one missed escalation is materially worse than ten false ones. The PQE pattern is to reproduce the worst-case report, score blast radius on the four-bucket taxonomy named above, and route only the destructive-API tail to the on-call rotation, with the original transcript and reproduction recipe attached. Cursor's own forum policy of acknowledging 800 monthly reports ([forum.cursor.com](https://forum.cursor.com/t/how-we-handle-bug-reports/150534)) is the intake shape this triage would sit on top of.

**"Drive agentic bug prioritization at scale."** Theme 1, Theme 4, and the long-tail sub-pattern of Theme 3 (Subagent `resume` running the wrong model) are agentic-Cursor-bug-shaped specifically. The shared shape is that the user's stated intent and the agent's executed action diverged, and the divergence was not caught by a guardrail. A PQE driving prioritization here would group reports by divergence type (wrong tool, wrong file scope, wrong model, wrong approval), measure each group's frequency and severity over time, and use that signal to argue for the right next investment: a stricter pre-execution preview, a better revert path, a tighter approval boundary, or a model-routing fix. The Composer 2.5 post's mention of "agentic monitoring tools" ([cursor.com/blog/composer-2-5](https://cursor.com/blog/composer-2-5)) implies an internal observability surface already exists, which is where the PQE clustering would land.

**"Synthesizing signal from across our user base."** Theme 2 (model routing) and Theme 5 (crashes after updates) are diffuse and need clustering. Theme 2's signal is split across the forum (technical phrasing, like the toast wording), Reddit (financial framing, like the $1,215.87 bill), and the billing dashboard (where the authoritative record lives). Theme 5's signal is split across macOS, Linux, Windows, and WSL, with overlapping tags but distinct root causes. The PQE work is making sure these are read together rather than triaged as nine separate one-off tickets.

**"Apply business context where humans need to stay in the loop."** Theme 4 (the Allow-button split-symptom case) is the cleanest example of this in the public record. Cursor's own staff response routed the visual-confusion variant and the silent-execution variant to two different internal pipelines based on what the user could actually demonstrate. That's the judgment call that resists automation, and it's the one the JD specifically protects.

## What lodestar can and cannot say about Cursor

Honest scope note. Lodestar at v0-min ingests Aider issues and outputs an Aider weekly report. It does not ingest Cursor's forum, /r/cursor, Hacker News, or any Cursor-specific source. This manifest was written by hand from public sources; a lodestar pipeline did not produce it. The cited URLs were read with a browsing tool and the user quotes were transcribed from the forum and Reddit views the URLs resolve to.

What lodestar would need, to ingest Cursor signal honestly: a forum.cursor.com mapper (Discourse JSON endpoints expose post bodies and tags; the architecture's mapper layer extends cleanly), a Reddit mapper (the `/top.json` endpoints already proved usable above), and an HN mapper if a third source were ever needed. Authentication is the live question, forum.cursor.com is read-only without login but Reddit's API has rate-limits and HN's Algolia search is the cleanest fallback. The dedup and ranker layers (which already handle "same issue, two sources" for Aider) would carry over without code changes. The new code is the source-specific mappers plus the auth handling.

This section is the honesty backstop on the rest of the document. The manifest argues Wei understands Cursor's quality surfaces. Lodestar does not yet monitor them.

## Sources cited

1. [cursor.com](https://cursor.com/). Cursor's product framing in their own words ("the best way to code with AI").
2. [cursor.com/docs](https://cursor.com/docs). Cursor docs landing page, source for the named feature list (Agent, Tab, MCP, Rules, Skills, CLI, BugBot, Plan Mode).
3. [cursor.com/docs/cloud-agent](https://cursor.com/docs/cloud-agent). Cloud agents documentation.
4. [cursor.com/docs/context/semantic-search](https://cursor.com/docs/context/semantic-search). Codebase indexing documentation.
5. [cursor.com/docs/bugbot](https://cursor.com/docs). BugBot documentation (resolves to docs index navigation).
6. [cursor.com/blog/composer-2-5](https://cursor.com/blog/composer-2-5). Official 2026-05-18 announcement of Composer 2.5, source for the "agentic monitoring tools" reference.
7. [forum.cursor.com/t/how-we-handle-bug-reports/150534](https://forum.cursor.com/t/how-we-handle-bug-reports/150534). Cursor's stated bug-intake policy ("nearly 800 bug reports come through this forum [each month]. We read all of them").
8. [forum.cursor.com/t/critical-all-windows-and-ai-chat-close-immediately-after-latest-update/160922](https://forum.cursor.com/t/critical-all-windows-and-ai-chat-close-immediately-after-latest-update/160922). The macOS 3.4.20 startup regression.
9. [forum.cursor.com/t/cursor-tab-completion-broken-codebase-indexing-stuck-on-loading/160303](https://forum.cursor.com/t/cursor-tab-completion-broken-codebase-indexing-stuck-on-loading/160303). Tab + indexing combined failure.
10. [forum.cursor.com/t/ai-generating-non-existent-motionless-tag-wasting-usage-tokens-on-self-correction/160776](https://forum.cursor.com/t/ai-generating-non-existent-motionless-tag-wasting-usage-tokens-on-self-correction/160776). Agent hallucinating fabricated JSX tag.
11. [forum.cursor.com/t/all-my-cursor-chats-have-disappeared-from-the-history-after-using-agents-window/160767](https://forum.cursor.com/t/all-my-cursor-chats-have-disappeared-from-the-history-after-using-agents-window/160767). Local chat history loss on Agents window first use.
12. [forum.cursor.com/t/allow-button-on-subagents-misbehaving/160585](https://forum.cursor.com/t/allow-button-on-subagents-misbehaving/160585). Subagent approval hit-area / silent-execution dual report.
13. [forum.cursor.com/t/switched-to-composer-2-after-reaching-api-limit-on-every-request/160924](https://forum.cursor.com/t/switched-to-composer-2-after-reaching-api-limit-on-every-request/160924). Composer fallback toast wording confirmed unclear by staff.
14. [forum.cursor.com/t/subagent-resume-runs-an-incorrect-model/160590](https://forum.cursor.com/t/subagent-resume-runs-an-incorrect-model/160590). Subagent resume routing bug.
15. [forum.cursor.com/t/remote-ssh-agent-shell-tool-loses-completion-under-concurrent-code-search-load/160918](https://forum.cursor.com/t/remote-ssh-agent-shell-tool-loses-completion-under-concurrent-code-search-load/160918). Remote SSH shell tool reliability.
16. [forum.cursor.com/t/cursor-ide-does-not-even-start/160363](https://forum.cursor.com/t/cursor-ide-does-not-even-start/160363). Linux startup failure.
17. [forum.cursor.com/t/cursor-is-not-functional-on-windows-on-wsl-environment/160930](https://forum.cursor.com/t/cursor-is-not-functional-on-windows-on-wsl-environment/160930). Windows WSL regression.
18. [forum.cursor.com/t/cursor-agent-window-sometimes-returns-duplicated-responses/160910](https://forum.cursor.com/t/cursor-agent-window-sometimes-returns-duplicated-responses/160910). Agents window duplicated-response bug.
19. [forum.cursor.com/t/macos-26-mcpprocess-ipc-crash-loop-on-startup-agent-execution-fails-until-legacymcpmode-workaround-applied/160598](https://forum.cursor.com/t/macos-26-mcpprocess-ipc-crash-loop-on-startup-agent-execution-fails-until-legacymcpmode-workaround-applied/160598). MCP IPC crash on macOS 26.
20. [forum.cursor.com/t/gmail-mcp-oauth-browser-not-opening-stuck-in-auth-loop/160933](https://forum.cursor.com/t/gmail-mcp-oauth-browser-not-opening-stuck-in-auth-loop/160933). MCP OAuth loop bug.
21. [forum.cursor.com/t/plugin-hooks-not-loading-into-cursor-ide/156702](https://forum.cursor.com/t/plugin-hooks-not-loading-into-cursor-ide/156702). Plugin hooks not loading.
22. [forum.cursor.com/t/private-team-marketplace-plugin-install-fails-on-3-2-11-three-stage-clone-fallback-all-broken/159257](https://forum.cursor.com/t/private-team-marketplace-plugin-install-fails-on-3-2-11-three-stage-clone-fallback-all-broken/159257). Private marketplace plugin install regression.
23. [forum.cursor.com/t/fish-cant-copy-paste-in-cursor/160901](https://forum.cursor.com/t/fish-cant-copy-paste-in-cursor/160901). Fish shell terminal copy-paste regression.
24. [forum.cursor.com/t/option-arrow-keys-no-longer-work-in-the-integrated-terminal/160375](https://forum.cursor.com/t/option-arrow-keys-no-longer-work-in-the-integrated-terminal/160375). Option+Arrow keys regression on macOS.
25. [forum.cursor.com/t/when-copying-1-line-code-and-pasting-to-chat-with-command-v-it-pasts-raw-text-instead-of-reference/156626](https://forum.cursor.com/t/when-copying-1-line-code-and-pasting-to-chat-with-command-v-it-pasts-raw-text-instead-of-reference/156626). Paste-as-reference UX regression.
26. [reddit.com /r/cursor /1sxsp8i](https://www.reddit.com/r/cursor/comments/1sxsp8i/cursor_claude_deleted_a_companys_entire_database/). PocketOS database deletion incident.
27. [reddit.com /r/cursor /1szupca](https://www.reddit.com/r/cursor/comments/1szupca/agent_got_stuck_in_a_loop_and_spent_over_2000_in/). Agent loop, $2000 cost.
28. [reddit.com /r/cursor /1tb95ys](https://www.reddit.com/r/cursor/comments/1tb95ys/cursor_opus_46_entered_an_infinite_generation/). Opus 4.6 infinite generation loop with full transcript.
29. [reddit.com /r/cursor /1swc2b0](https://www.reddit.com/r/cursor/comments/1swc2b0/20_annual_plan_cursor_is_using_composer_even/). Composer routing not honoring selected Opus 4.6.
30. [reddit.com /r/cursor /1tdrihv](https://www.reddit.com/r/cursor/comments/1tdrihv/api_usage_limit_reached_and_excessive_monthly_cost/). $1,215.87 bill against perceived $50 limit.
31. [reddit.com /r/cursor /1t8pax3](https://www.reddit.com/r/cursor/comments/1t8pax3/can_you_stop_already_make_it_optional_for_the/). Weak-signal: vibe-coder UI mode complaint.
32. [reddit.com /r/cursor /1sshtml](https://www.reddit.com/r/cursor/comments/1sshtml/did_elon_just_kill_the_appeal_of_cursor/). Weak-signal: ownership-uncertainty sentiment thread.
