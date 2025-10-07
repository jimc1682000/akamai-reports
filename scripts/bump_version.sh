#!/bin/bash
# Automated version bump and CHANGELOG generation script
# Usage: ./scripts/bump_version.sh [major|minor|patch]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Version file location
VERSION_FILE="VERSION"

# Function to display usage
usage() {
    echo "Usage: $0 [major|minor|patch]"
    echo ""
    echo "Examples:"
    echo "  $0 patch   # 0.1.0 -> 0.1.1"
    echo "  $0 minor   # 0.1.0 -> 0.2.0"
    echo "  $0 major   # 0.1.0 -> 1.0.0"
    exit 1
}

# Function to print colored messages
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if bump type is provided
if [ $# -eq 0 ]; then
    print_error "No version bump type specified"
    usage
fi

BUMP_TYPE=$1

# Validate bump type
if [[ ! "$BUMP_TYPE" =~ ^(major|minor|patch)$ ]]; then
    print_error "Invalid bump type: $BUMP_TYPE"
    usage
fi

# Check if git-cliff is installed
if ! command -v git-cliff &> /dev/null; then
    print_error "git-cliff is not installed"
    echo "Install with: brew install git-cliff"
    exit 1
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    print_error "You have uncommitted changes. Please commit or stash them first."
    git status --short
    exit 1
fi

# Check if we're on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    print_warning "You are not on the main branch (current: $CURRENT_BRANCH)"
    read -p "Do you want to continue? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Aborted"
        exit 0
    fi
fi

# Get current version
if [ -f "$VERSION_FILE" ]; then
    CURRENT_VERSION=$(cat "$VERSION_FILE")
    print_info "Current version: $CURRENT_VERSION"
else
    # Try to get from git tags
    CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
    print_info "No VERSION file found, using git tag: $CURRENT_VERSION"
    # Strip 'v' prefix if present
    CURRENT_VERSION=${CURRENT_VERSION#v}
fi

# Parse version components
IFS='.' read -r -a VERSION_PARTS <<< "$CURRENT_VERSION"
MAJOR=${VERSION_PARTS[0]:-0}
MINOR=${VERSION_PARTS[1]:-0}
PATCH=${VERSION_PARTS[2]:-0}

# Bump version based on type
case $BUMP_TYPE in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"
NEW_TAG="v${NEW_VERSION}"

print_info "New version: $NEW_VERSION"
print_info "New tag: $NEW_TAG"

# Confirm the bump
read -p "Proceed with version bump? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Nn]$ ]]; then
    print_info "Aborted"
    exit 0
fi

# Update VERSION file
echo "$NEW_VERSION" > "$VERSION_FILE"
print_success "Updated VERSION file"

# Generate CHANGELOG
print_info "Generating CHANGELOG.md..."
git-cliff --tag "$NEW_TAG" --output CHANGELOG.md

if [ $? -eq 0 ]; then
    print_success "Generated CHANGELOG.md"
else
    print_error "Failed to generate CHANGELOG.md"
    # Restore VERSION file
    echo "$CURRENT_VERSION" > "$VERSION_FILE"
    exit 1
fi

# Stage changes
git add VERSION CHANGELOG.md

# Commit changes
COMMIT_MSG="chore(release): prepare for $NEW_TAG"
git commit -m "$COMMIT_MSG"
print_success "Committed version bump: $COMMIT_MSG"

# Create git tag
git tag -a "$NEW_TAG" -m "Release $NEW_TAG"
print_success "Created tag: $NEW_TAG"

# Display summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
print_success "Version bump complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
print_info "Summary:"
echo "  Old version: $CURRENT_VERSION"
echo "  New version: $NEW_VERSION"
echo "  Git tag: $NEW_TAG"
echo ""
print_info "Next steps:"
echo "  1. Review the changes:"
echo "     git show HEAD"
echo "     cat CHANGELOG.md"
echo ""
echo "  2. Push to remote:"
echo "     git push origin $CURRENT_BRANCH"
echo "     git push origin $NEW_TAG"
echo ""
print_warning "Note: Changes have been committed but not pushed yet"
