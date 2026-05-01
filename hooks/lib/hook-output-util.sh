#!/bin/sh
# hook-output-util.sh — Shared hook JSON output helpers.
# Requires: json-util.sh sourced and parser detected.

# Cursor IDE hook envelope (set RTL_HOOK_OUTPUT_FORMAT=cursor in wrappers).
_hook_out_cursor_p() {
  [ "${RTL_HOOK_OUTPUT_FORMAT:-claude}" = "cursor" ]
}

# Emit a continue response with optional additionalContext message, then exit 0.
# Usage: emit_continue "message"   or   emit_continue ""
emit_continue() {
  _EC_MSG="$1"
  if _hook_out_cursor_p; then
    if [ -n "$_EC_MSG" ]; then
      printf '{"permission":"allow","agent_message":"%s"}' "$(jsonu_escape "$_EC_MSG")"
    else
      printf '{"permission":"allow"}'
    fi
    exit 0
  fi
  if [ -n "$_EC_MSG" ]; then
    printf '{"continue":true,"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}' "$(jsonu_escape "$_EC_MSG")"
  else
    printf '{"continue":true}'
  fi
  exit 0
}

# Emit a block/deny response with reason message, then exit 0.
# Usage: emit_block "reason message"
emit_block() {
  _EB_MSG="$1"
  if _hook_out_cursor_p; then
    printf '{"permission":"deny","user_message":"%s"}' "$(jsonu_escape "$_EB_MSG")"
    exit 0
  fi
  printf '{"continue":false,"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"%s"}}' "$(jsonu_escape "$_EB_MSG")"
  exit 0
}

# Emit a Stop-hook block response with reason, then exit 0.
# Usage: emit_stop_block "reason message"
emit_stop_block() {
  _ESB_MSG="$1"
  if _hook_out_cursor_p; then
    printf '{"followup_message":"%s"}' "$(jsonu_escape "$_ESB_MSG")"
    exit 0
  fi
  printf '{"continue":false,"decision":"block","reason":"%s"}' "$(jsonu_escape "$_ESB_MSG")"
  exit 0
}

# Emit a PostToolUse continue response (no additionalContext), then exit 0.
# Usage: emit_post_continue
emit_post_continue() {
  if _hook_out_cursor_p; then
    printf '{}'
    exit 0
  fi
  printf '{"continue":true}'
  exit 0
}

# PostToolUse / edit tracker: optional extra context for Cursor.
# Usage: emit_post_additional_context "message"
emit_post_additional_context() {
  _EPA_MSG="$1"
  if _hook_out_cursor_p; then
    if [ -n "$_EPA_MSG" ]; then
      printf '{"additional_context":"%s"}' "$(jsonu_escape "$_EPA_MSG")"
    else
      printf '{}'
    fi
    exit 0
  fi
  if [ -n "$_EPA_MSG" ]; then
    printf '{"continue":true,"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}' "$(jsonu_escape "$_EPA_MSG")"
  else
    printf '{"continue":true}'
  fi
  exit 0
}
