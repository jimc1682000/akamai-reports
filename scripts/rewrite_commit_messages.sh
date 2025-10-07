#!/bin/bash
# Script to rewrite commit messages to follow Conventional Commits
# WARNING: This rewrites git history. Use with caution!

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  Commit Message Rewriter${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Safety checks
echo -e "${YELLOW}⚠️  WARNING: This will rewrite git history!${NC}"
echo ""
echo "This script will:"
echo "  1. Rewrite non-conventional commit messages"
echo "  2. Change all commit SHAs"
echo "  3. Require force push if already pushed to remote"
echo ""
echo -e "${RED}Only proceed if:${NC}"
echo "  - You have a backup of your repository"
echo "  - No one else is working on this branch"
echo "  - You understand the implications"
echo ""

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ You have uncommitted changes. Please commit or stash them first.${NC}"
    git status --short
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "${BLUE}Current branch: ${CURRENT_BRANCH}${NC}"
echo ""

# Ask for confirmation
read -p "Do you want to proceed with rewriting commit history? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Aborted.${NC}"
    exit 0
fi

echo ""
echo -e "${GREEN}Creating backup branch...${NC}"
BACKUP_BRANCH="backup-before-rewrite-$(date +%Y%m%d-%H%M%S)"
git branch "$BACKUP_BRANCH"
echo -e "${GREEN}✅ Backup created: ${BACKUP_BRANCH}${NC}"
echo ""

# Create rewrite map
echo -e "${BLUE}Preparing commit message rewrites...${NC}"
cat > /tmp/commit-rewrite-map.txt << 'EOF'
ce41f4f8cc21e555d1507985b6b94a48296d141b|feat: initialize Akamai V2 Traffic Reporting System
c9ddcceb901bc3b94729bbc85498fe5d221d5eb8|feat(di): implement Dependency Injection pattern with ServiceContainer
c7765669c18fb315994e028ed6fbe0f3b790e6ff|feat(resilience): implement Circuit Breaker pattern for API protection
729f50b4577feeb12e96bae1a9300c82d699fe0a|feat(performance): implement concurrent API calls with ThreadPoolExecutor
9afefd2877a6db71f50690c3ab31b29ca3711880|fix(tests): fix integration tests for ServiceContainer pattern
7418fc45df5c14717fd3ad4205028b5c0b9b5cf4|feat(logging): implement structured logging with JSON format
458e093e8f77d847f1e1a67f6c9fcdd3bfdaa5d9|fix(tests): fix test_get_all_regional_traffic for concurrent execution
bf2af87587f852f9062f51d452183c0d14bb3cc1|feat(cache): implement response caching system with TTL
EOF

echo -e "${GREEN}✅ Rewrite map created${NC}"
echo ""

# Display what will be changed
echo -e "${BLUE}The following commits will be rewritten:${NC}"
echo ""
while IFS='|' read -r commit_hash new_message; do
    old_message=$(git log -1 --format=%s "$commit_hash" 2>/dev/null || echo "NOT FOUND")
    echo -e "${YELLOW}OLD:${NC} $old_message"
    echo -e "${GREEN}NEW:${NC} $new_message"
    echo ""
done < /tmp/commit-rewrite-map.txt

read -p "Proceed with rewriting? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Aborted.${NC}"
    rm /tmp/commit-rewrite-map.txt
    exit 0
fi

echo ""
echo -e "${BLUE}Starting git filter-repo rewrite...${NC}"

# Check if git-filter-repo is available
if ! command -v git-filter-repo &> /dev/null; then
    echo -e "${RED}❌ git-filter-repo not found. Installing...${NC}"
    echo ""
    echo "Please install git-filter-repo:"
    echo "  brew install git-filter-repo"
    echo ""
    echo "Or use alternative method with git rebase -i"
    exit 1
fi

# Create commit message map file
cat > /tmp/commit-msg-map.txt << 'EOF'
# Commit message rewrite map
# OLD_MESSAGE==>NEW_MESSAGE

Initial commit: Akamai V2 Traffic Reporting System==>feat: initialize Akamai V2 Traffic Reporting System
Implement Dependency Injection Pattern==>feat(di): implement Dependency Injection pattern with ServiceContainer
Implement Circuit Breaker Pattern==>feat(resilience): implement Circuit Breaker pattern for API protection
Implement Concurrent API Calls==>feat(performance): implement concurrent API calls with ThreadPoolExecutor
Fix integration tests for ServiceContainer pattern==>fix(tests): fix integration tests for ServiceContainer pattern
Implement Structured Logging==>feat(logging): implement structured logging with JSON format
Fix test_get_all_regional_traffic for concurrent execution==>fix(tests): fix test_get_all_regional_traffic for concurrent execution
Implement Response Caching System==>feat(cache): implement response caching system with TTL
EOF

echo -e "${YELLOW}⚠️  git-filter-repo will rewrite history. This operation is complex.${NC}"
echo -e "${YELLOW}⚠️  Alternative: Use interactive rebase (safer for small changes)${NC}"
echo ""
echo -e "${BLUE}Recommended: Use git rebase -i instead${NC}"
echo ""
echo "To manually rewrite commits:"
echo "  1. git rebase -i --root"
echo "  2. Change 'pick' to 'reword' for commits you want to change"
echo "  3. Save and close editor"
echo "  4. For each commit, update the message and save"
echo ""

rm /tmp/commit-rewrite-map.txt
rm /tmp/commit-msg-map.txt

echo -e "${GREEN}✅ Preparation complete${NC}"
echo -e "${BLUE}Backup branch created: ${BACKUP_BRANCH}${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. git rebase -i --root"
echo "  2. Change commits to 'reword' (or 'r')"
echo "  3. Update each commit message"
echo "  4. Verify with: git log --oneline"
echo "  5. If satisfied: git push --force-with-lease origin $CURRENT_BRANCH"
echo "  6. If issues: git reset --hard $BACKUP_BRANCH"
