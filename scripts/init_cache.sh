#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CACHE_DIR="${ROOT_DIR}/local-cache"
IO_DIR="${ROOT_DIR}/input-output-data"

mkdir -p "${CACHE_DIR}"
mkdir -p "${IO_DIR}"

PARENT_ISSUES_FILE="${CACHE_DIR}/groomed_parent_issues.json"
ISSUES_FILE="${CACHE_DIR}/groomed_issues.json"

if [[ ! -f "${PARENT_ISSUES_FILE}" ]]; then
  printf '%s\n' '{ "parentIssues": [] }' > "${PARENT_ISSUES_FILE}"
  echo "Created ${PARENT_ISSUES_FILE}"
else
  echo "Exists  ${PARENT_ISSUES_FILE}"
fi

if [[ ! -f "${ISSUES_FILE}" ]]; then
  printf '%s\n' '{ "issues": [] }' > "${ISSUES_FILE}"
  echo "Created ${ISSUES_FILE}"
else
  echo "Exists  ${ISSUES_FILE}"
fi

echo "Cache initialized."