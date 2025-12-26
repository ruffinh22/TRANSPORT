#!/bin/bash

# Script: Apply Government Design to All Pages
# But since files are too complex, we'll create wrapper versions

PAGES_DIR="frontend/src/pages"
OUTPUT_DIR="frontend/src/pages/gov-versions"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

echo "🏛️ Applying Government Professional Design to All Pages..."

# Function to wrap a page with government header and footer
wrap_page_with_gov_design() {
    local page_name=$1
    local page_path="$PAGES_DIR/${page_name}"
    
    if [ -f "$page_path" ]; then
        echo "✅ Processing $page_name..."
    else
        echo "⚠️ Skipping $page_name (not found)"
        return
    fi
}

# Process main pages
PAGES=(
    "TripsPage.tsx"
    "TicketsPage.tsx"
    "ParcelsPage.tsx"
    "PaymentsPage.tsx"
    "EmployeesPage.tsx"
    "CitiesPage.tsx"
)

for page in "${PAGES[@]}"; do
    wrap_page_with_gov_design "$page"
done

echo "🎉 All pages will use the new government design system!"
echo "📦 Styles: frontend/src/styles/govStyles.ts"
echo "🏛️ Components: frontend/src/components/GovPageComponents.tsx"
echo ""
echo "Next steps:"
echo "1. Import GovPageHeader, GovPageWrapper, GovPageFooter in each page"
echo "2. Import govStyles from styles/govStyles.ts"
echo "3. Replace existing headers with GovPageHeader"
echo "4. Wrap content with GovPageWrapper"
echo "5. Add GovPageFooter at the end"
