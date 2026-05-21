#!/usr/bin/env bash
# Idempotent installer for the Karpathy + Superpowers Claude Code plugins.
# Runs on SessionStart so ephemeral remote containers pick the plugins back up
# without needing the interactive trust prompt.
set -u

log() { printf '[install-plugins] %s\n' "$*" >&2; }

if ! command -v claude >/dev/null 2>&1; then
  log "claude CLI not on PATH; skipping plugin install"
  exit 0
fi

marketplaces_json="$(claude plugin marketplace list --json 2>/dev/null || echo '[]')"
has_marketplace() { printf '%s' "$marketplaces_json" | grep -q "\"$1\""; }

ensure_marketplace() {
  local name="$1" source="$2"
  if has_marketplace "$name"; then
    return 0
  fi
  log "adding marketplace $name ($source)"
  claude plugin marketplace add "$source" >/dev/null 2>&1 || log "marketplace add failed: $source"
}

ensure_marketplace superpowers-marketplace obra/superpowers-marketplace
ensure_marketplace karpathy-skills forrestchang/andrej-karpathy-skills

installed_list="$(claude plugin list 2>/dev/null || true)"
ensure_plugin() {
  local spec="$1"
  if printf '%s' "$installed_list" | grep -q "$spec"; then
    return 0
  fi
  log "installing $spec"
  claude plugin install "$spec" --scope user >/dev/null 2>&1 || log "plugin install failed: $spec"
}

ensure_plugin superpowers@superpowers-marketplace
ensure_plugin andrej-karpathy-skills@karpathy-skills

exit 0
