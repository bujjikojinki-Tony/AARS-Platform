# 10 NUREG-0700 Computer-Based Procedure Substandard

Source: `/Users/maolei/Documents/数字化/Nureg 0700 Rev3.pdf`

## CBP rules to carry forward

- Present the procedure identification, current step, warnings, cautions, notes, and reference materials together.
- Support procedure supervision, monitoring, and assessment.
- Make it easy to see step status, path status, and where the user is in a sequence.
- Provide navigation between procedure steps and related support information.
- Preserve access to backup procedures if the computer-based procedure path fails.
- Show procedure content in a clear, concise layout that supports operational use rather than reading-only review.
- Support interruption, pause, resume, back, cancel, restart, review, and suspend behavior where relevant.
- Keep resumption of interrupted sequences lightweight.

## HMI implications

When a page implements or assists a procedure:

- show the current step and the next step
- show required cautions and warnings before action
- show whether the procedure is active, paused, suspended, or completed
- show links to supporting evidence and backup paths
- show where the user can safely resume after interruption

