#!/bin/bash
################################################################################
# Check if Turso Upload Succeeded
################################################################################

echo "========================================================================"
echo "CHECKING TURSO DATABASE"
echo "========================================================================"
echo ""

echo "Year breakdown in Turso:"
turso db shell alberta-procurement "SELECT year, COUNT(*) as count FROM opportunities GROUP BY year ORDER BY year DESC;"

echo ""
echo "Total records:"
turso db shell alberta-procurement "SELECT COUNT(*) as total FROM opportunities;"

echo ""
echo "Expected: 14,064 total postings (2021-2025)"
echo ""
