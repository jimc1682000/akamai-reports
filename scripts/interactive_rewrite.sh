#!/bin/bash
# Interactive commit message rewriter
# Uses git rebase -i for safe, controlled rewriting

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

clear
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}      Interactive Commit Message Rewriter${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Safety checks
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ You have uncommitted changes.${NC}"
    echo "Please commit or stash them first:"
    echo "  git stash"
    exit 1
fi

# Check remote status
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${BLUE}Current branch:${NC} $CURRENT_BRANCH"

# Check if pushed to remote
if git ls-remote --exit-code --heads origin "$CURRENT_BRANCH" &>/dev/null; then
    echo -e "${YELLOW}⚠️  This branch exists on remote!${NC}"
    echo "Rewriting will require force push."
    echo ""
fi

# List commits that need rewriting
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Commits that need rewriting:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Display non-conventional commits with suggested rewrites
declare -A REWRITE_MAP
REWRITE_MAP["Initial commit: Akamai V2 Traffic Reporting System"]="feat: initialize Akamai V2 Traffic Reporting System"
REWRITE_MAP["Implement Dependency Injection Pattern"]="feat(di): implement Dependency Injection pattern with ServiceContainer"
REWRITE_MAP["Implement Circuit Breaker Pattern"]="feat(resilience): implement Circuit Breaker pattern for API protection"
REWRITE_MAP["Implement Concurrent API Calls"]="feat(performance): implement concurrent API calls with ThreadPoolExecutor"
REWRITE_MAP["Fix integration tests for ServiceContainer pattern"]="fix(tests): fix integration tests for ServiceContainer pattern"
REWRITE_MAP["Implement Structured Logging"]="feat(logging): implement structured logging with JSON format"
REWRITE_MAP["Fix test_get_all_regional_traffic for concurrent execution"]="fix(tests): fix test_get_all_regional_traffic for concurrent execution"
REWRITE_MAP["Implement Response Caching System"]="feat(cache): implement response caching system with TTL"

counter=1
for old_msg in "${!REWRITE_MAP[@]}"; do
    new_msg="${REWRITE_MAP[$old_msg]}"
    echo -e "${YELLOW}${counter}.${NC}"
    echo -e "   ${RED}OLD:${NC} $old_msg"
    echo -e "   ${GREEN}NEW:${NC} $new_msg"
    echo ""
    ((counter++))
done

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}This will:${NC}"
echo "  1. Create a backup branch"
echo "  2. Open interactive rebase editor"
echo "  3. Let you reword commit messages one by one"
echo ""
echo -e "${YELLOW}⚠️  WARNING:${NC} This rewrites git history!"
echo ""

read -p "Do you want to proceed? [y/N] " -n 1 -r
echo
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Aborted.${NC}"
    exit 0
fi

# Create backup
BACKUP_BRANCH="backup-before-rewrite-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP_BRANCH"
echo -e "${GREEN}✅ Backup created: ${BACKUP_BRANCH}${NC}"
echo ""

# Save rewrite suggestions to a file for reference
SUGGESTION_FILE="/tmp/commit-rewrite-suggestions.txt"
echo "# Commit Message Rewrite Suggestions" > "$SUGGESTION_FILE"
echo "# Use these as reference during interactive rebase" >> "$SUGGESTION_FILE"
echo "" >> "$SUGGESTION_FILE"

for old_msg in "${!REWRITE_MAP[@]}"; do
    new_msg="${REWRITE_MAP[$old_msg]}"
    echo "OLD: $old_msg" >> "$SUGGESTION_FILE"
    echo "NEW: $new_msg" >> "$SUGGESTION_FILE"
    echo "" >> "$SUGGESTION_FILE"
done

echo -e "${BLUE}📝 Rewrite suggestions saved to: ${SUGGESTION_FILE}${NC}"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}Starting Interactive Rebase...${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}Instructions:${NC}"
echo "  1. Editor will open with commit list"
echo "  2. Change 'pick' to 'reword' (or 'r') for commits to modify"
echo "  3. Save and close editor"
echo "  4. For each marked commit, update message and save"
echo "  5. Check suggestions: cat $SUGGESTION_FILE"
echo ""
echo -e "${BLUE}Press Enter to continue...${NC}"
read

# Start interactive rebase from root
echo ""
echo -e "${GREEN}🚀 Starting git rebase -i --root...${NC}"
echo ""

export GIT_SEQUENCE_EDITOR="sed -i '' 's/^pick \([^ ]*\) \(Implement\|Fix test\|Fix integration\|Initial commit\)/reword \1 \2/'"
git rebase -i --root

# Check if rebase was successful
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}✅ Rebase completed successfully!${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${BLUE}Verifying commits:${NC}"
    echo ""
    git log --oneline -10
    echo ""
    echo -e "${CYAN}Next steps:${NC}"
    echo ""
    echo -e "${GREEN}If everything looks good:${NC}"
    echo "  git push --force-with-lease origin $CURRENT_BRANCH"
    echo ""
    echo -e "${YELLOW}If you want to undo:${NC}"
    echo "  git reset --hard $BACKUP_BRANCH"
    echo "  git branch -D $BACKUP_BRANCH  # Optional: delete backup"
    echo ""
else
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${RED}❌ Rebase failed or was aborted${NC}"
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}To restore from backup:${NC}"
    echo "  git rebase --abort"
    echo "  git reset --hard $BACKUP_BRANCH"
    echo ""
fi
