#!/bin/bash

# ================================
# Create GitHub Labels via CLI
# Requires: GitHub CLI (gh)
# Usage: ./create_labels.sh <org>/<repo>
# Example: ./create_labels.sh Yandex-Practicum-Students/57_58_booking_seats_team_2
# ================================

REPO=$1

if [ -z "$REPO" ]; then
  echo "❌ Укажите репозиторий: ./create_labels.sh <owner>/<repo>"
  exit 1
fi

echo "🏷 Создание labels в репозитории: $REPO"
echo ""

create_label() {
  local name="$1"
  local color="$2"
  local desc="$3"

  echo "Добавляется: $name"
  gh label create "$name" \
    --color "$color" \
    --description "$desc" \
    --repo "$REPO" 2>/dev/null || echo "⚠ Label '$name' уже существует"
}

# PRIORITY LABELS
create_label "P1" "B60205" "Critical priority"
create_label "P2" "D93F0B" "Main functionality (MVP)"
create_label "P3" "FBCA04" "Enhancement / improvements"
create_label "P4" "0E8A16" "Optional + time-permitting"

# MODULE LABELS
create_label "users" "5319E7" "Users module"
create_label "auth" "5319E7" "Authentication & authorization"
create_label "cafes" "1D76DB" "Cafes module"
create_label "tables" "1D76DB" "Tables module"
create_label "slots" "1D76DB" "Time slots module"
create_label "booking" "0E8A16" "Booking module"
create_label "media" "FBCA04" "Media & image upload"
create_label "celery" "D93F0B" "Celery tasks & notifications"

# TASK TYPE LABELS
create_label "models" "0366D6" "Database models"
create_label "schemas" "0366D6" "Pydantic schemas"
create_label "repository" "0E8A16" "CRUD repository layer"
create_label "service" "5319E7" "Business logic"
create_label "api" "1D76DB" "API routes"
create_label "tests" "5319E7" "Tests"
create_label "refactor" "D93F0B" "Code refactoring"

# TECHNICAL LABELS
create_label "backend" "5319E7" "Backend development"
create_label "infra" "0366D6" "Infrastructure setup"
create_label "devops" "1D76DB" "CI/CD, docker, workflows"
create_label "database" "0E8A16" "Database & migrations"
create_label "migrations" "FBCA04" "DB migrations"
create_label "logging" "B60205" "Log management"
create_label "docker" "2496ED" "Docker configuration"

# STATUS LABELS
create_label "in review" "5319E7" "Waiting for review"
create_label "blocked" "B60205" "Blocked by another task"
create_label "ready" "0E8A16" "Ready to start"
create_label "discussion" "FBCA04" "Needs discussion"

echo ""
echo "✅ Все labels созданы или уже существовали!"
