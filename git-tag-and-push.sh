#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<EOF
Usage: $0 <tag>

Examples:
  $0 v1.3.5

This script will create a git tag with the given name on the current HEAD and push it to origin.
If the tag already exists you will be prompted to confirm force-recreate.
EOF
  exit 2
}

if [ "$#" -lt 1 ]; then
  usage
fi

TAG="$1"

# find repository root (must be run from somewhere inside the repo)
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
  echo "Error: this script must be run inside a git repository." >&2
  exit 1
}

cd "$REPO_ROOT"

echo "Repository root: $REPO_ROOT"

# Optional safety: warn if working tree has changes
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Warning: you have unstaged or staged changes in the working tree." >&2
  read -r -p "Continue and tag current HEAD anyway? [y/N] " yn
  case "$yn" in
    [Yy]*) ;;
    *) echo "Aborted."; exit 1 ;;
  esac
fi

# If tag exists, offer to force recreate
if git rev-parse "refs/tags/$TAG" >/dev/null 2>&1; then
  echo "Tag '$TAG' already exists locally." >&2
  read -r -p "Delete existing tag and recreate (force)? [y/N] " confirm
  case "$confirm" in
    [Yy]*)
      echo "Deleting local tag $TAG..."
      git tag -d "$TAG"
      echo "Deleting remote tag $TAG (if exists)..."
      # ignore non-zero in case remote tag doesn't exist
      git push --delete origin "$TAG" || true
      ;;
    *)
      echo "Aborted: tag already exists.";
      exit 1 ;;
  esac
fi

# Create the tag (lightweight, matching your example). To annotate use: git tag -a "$TAG" -m "Release $TAG"
echo "Creating tag '$TAG' on HEAD..."
git tag "$TAG"

echo "Pushing tag to origin..."
git push origin "$TAG"

echo "Tag $TAG created and pushed."
exit 0
