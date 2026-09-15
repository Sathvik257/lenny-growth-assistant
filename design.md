# Design rationale

The product is a research studio, organized around a question, its evidence, and an artifact. A quiet navigation rail holds persistent conversations. The center is a focused chat surface. The right panel lets the reader inspect evidence or work on a finished document without losing context.

The visual identity combines an orange audio mark, restrained gray surfaces, and Instrument Serif headlines with DM Sans controls. Fonts are bundled locally. Editorial typography connects the product to thoughtful long-form interviews. The only prominent orange actions are sending a question, selecting a mode, and following citations. Guest initials represent actual indexed people; no invented portraits or fake quotes are used.

The first screen contains four concrete starting questions, an editable composer and real corpus status. A starter fills the composer instead of sending immediately, leaving the user in control of the exact question. The user can switch between asking, essay writing and HTML/Markdown creation. Local/cloud selection is always visible.

## States

The empty state explains the next action. During generation, a timed progress indicator describes the current broad phase without pretending to show model reasoning. Errors preserve the user's draft for retry. Unsupported questions produce a clear answer with no fabricated sources. Sources expand to verbatim passages. Essay length deviations appear as a draft warning. Artifact previews offer source inspection, copy and download. Deletion has a confirmation dialog.

On large screens, the evidence panel is persistent. At narrower sizes it becomes an overlay and starts closed, protecting the working surface. Mobile navigation uses an explicit menu. The chat composer stays available while the conversation scrolls independently. Reduced-motion preferences disable animation. Native dialogs manage focus and Escape dismissal. Buttons have accessible names, controls are keyboard operable, and citations are focusable buttons. Generated HTML is isolated from the surrounding page.

## Boundaries

The interface does not label a retrieval score as model confidence. A checked citation label means it references a retrieved passage, not that semantic entailment has been proven. It does not claim the local model is connected until the configured model and agent service are available. Artifacts are scoped to the selected conversation.
