Apply response_language to all user-facing prose — narration between tool calls, status updates, progress notes, and findings included; preserve code, paths, and identifiers.

# Power mode: answer discussion questions asynchronously

Load this mode when `--power` is present after the parent has validated the
phase and supplied its phase directory, padded identifier, name, and any
locked specification. This mode gathers answers offline; it does not authorize
implementation.

## Prepare the question set

1. If a phase SPEC is supplied, read it and carry its requirements,
   boundaries, and acceptance criteria forward as locked requirements. Do not
   ask the user to decide them again.
2. Read project and phase context, scout relevant code and prior decisions,
   then identify all implementation gray areas. For each, give two to four
   concrete options with tradeoffs. Group related questions into sections of
   two to six questions where possible. Do not ask questions during this
   preparation step.
3. Write `{phase_dir}/{padded_phase}-QUESTIONS.json` with the phase identity,
   ISO timestamp, computed `stats` (`total`, `answered`, `chat_more`,
   `remaining`), and sections containing sequential IDs (`Q-01`, `Q-02`, ...),
   titles, concrete context, options, nullable answer, chat-more text, and
   status (`unanswered`, `answered`, or `chat-more`).
4. Write a self-contained `{phase_dir}/{padded_phase}-QUESTIONS.html` companion
   with collapsible sections, answer counts, a progress bar, question cards,
   radio options, and a chat-more field. Its save control should use the file
   picker when supported and otherwise offer a JSON download, with instructions
   to replace the state file.
5. Tell the user where both files are and how to answer them. Wait for an
   explicit `refresh`, `finalize`, `explain Q-NN`, or `exit power mode` request.

## Handle user commands

- **Refresh:** reread the JSON, recalculate every statistic and question
  status, persist the corrected JSON, regenerate the HTML from that state, and
  report answered, remaining, and chat-more counts.
- **Explain Q-NN:** find that question, explain the relevant project evidence
  and option tradeoffs, and leave the stored answer unchanged unless the user
  supplies one.
- **Exit power mode:** return to the normal one-at-a-time discussion and carry
  over all stored answers and chat-more notes.
- **Finalize:** proceed only when the user requests it. Read the saved JSON,
  recalculate its counts, treat unanswered questions as unresolved rather than
  inventing decisions, and write the regular phase context with the locked
  requirements, selected answers, deferred ideas, and remaining questions.
  Update the normal phase state and summarize the next step. If `--chain` is
  enabled, follow `modes/chain.md`, which advances to planning only.

Never infer that an answer was saved from an open HTML page. Use the JSON state
the user saved and explicitly asked to process.
