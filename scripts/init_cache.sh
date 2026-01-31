#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

CACHE_DIR="${ROOT_DIR}/local-cache"
IO_DIR="${ROOT_DIR}/input-output-data"

mkdir -p "${CACHE_DIR}"
mkdir -p "${IO_DIR}"

EPICS_FILE="${CACHE_DIR}/groomed_epics.json"
ISSUES_FILE="${CACHE_DIR}/groomed_issues.json"

if [[ ! -f "${EPICS_FILE}" ]]; then
  printf '%s\n' '{ "epics": [] }' > "${EPICS_FILE}"
  echo "Created ${EPICS_FILE}"
else
  echo "Exists  ${EPICS_FILE}"
fi

if [[ ! -f "${ISSUES_FILE}" ]]; then
  printf '%s\n' '{ "issues": [] }' > "${ISSUES_FILE}"
  echo "Created ${ISSUES_FILE}"
else
  echo "Exists  ${ISSUES_FILE}"
fi

echo "Cache initialized."