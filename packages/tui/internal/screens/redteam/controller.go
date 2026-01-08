// Package redteam provides the controller logic for red team configuration.
package redteam

import (
	"sort"

	tea "github.com/charmbracelet/bubbletea/v2"
)

// autoSave saves the configuration state to disk
func autoSave(state *RedTeamConfigState) {
	// Save configuration to .rogue/redteam.yaml
	// We don't block on errors - if save fails, user will just need to reconfigure next time
	_ = SaveRedTeamConfig(state)
}

// HandleKeyPress handles keyboard input for the red team config screen.
func HandleKeyPress(state *RedTeamConfigState, msg tea.KeyMsg) (*RedTeamConfigState, tea.Cmd) {
	// Handle dialog-specific input
	if state.ShowFrameworkDialog {
		return handleFrameworkDialogKey(state, msg)
	}

	switch msg.String() {
	case "tab":
		// Switch between panels - FocusedCategory is now local to each panel
		state.ActivePanel = (state.ActivePanel + 1) % 2
		// Start at first non-empty category
		var indices []int
		if state.ActivePanel == 0 {
			indices = getNonEmptyVulnCategoryIndices()
		} else {
			indices = getNonEmptyAttackCategoryIndices()
		}
		if len(indices) > 0 {
			state.FocusedCategory = indices[0]
		} else {
			state.FocusedCategory = 0
		}
		state.FocusedItem = -1

	case "up", "k":
		state = navigateUp(state)

	case "down", "j":
		state = navigateDown(state)

	case "left", "h":
		// Collapse category
		state = collapseCategory(state)

	case "right", "l":
		// Expand category
		state = expandCategory(state)

	case " ", "space":
		// Toggle selection
		state = toggleSelection(state)

	case "f":
		// Open framework dialog
		state.ShowFrameworkDialog = true

	// TODO: Re-enable when Qualifire API key feature is released
	// case "q":
	// 	// Return command to open API key dialog via main controller
	// 	return state, OpenAPIKeyDialogCmd(state.QualifireAPIKey)

	case "+", "=":
		// Increase attacks per vulnerability
		if state.AttacksPerVulnerability < 10 {
			state.AttacksPerVulnerability++
			autoSave(state)
		}

	case "-":
		// Decrease attacks per vulnerability
		if state.AttacksPerVulnerability > 1 {
			state.AttacksPerVulnerability--
			autoSave(state)
		}

	case "1":
		state = applyBasicPreset(state)
		autoSave(state)

	case "2":
		state = applyFullPreset(state)
		autoSave(state)

	case "3":
		state.ScanType = ScanTypeCustom
		autoSave(state)

	case "a":
		// Select all in current category
		state = selectAllInCategory(state)
		autoSave(state)

	case "n":
		// Deselect all in current category
		state = deselectAllInCategory(state)
		autoSave(state)
	}

	return state, nil
}

func handleFrameworkDialogKey(state *RedTeamConfigState, msg tea.KeyMsg) (*RedTeamConfigState, tea.Cmd) {
	switch msg.String() {
	case "esc":
		state.ShowFrameworkDialog = false

	case "enter":
		// Apply framework selection
		state = applyFrameworkSelection(state)
		state.ShowFrameworkDialog = false
		autoSave(state)

	case " ", "space":
		// Toggle framework (would need focused framework tracking)
		// For now, just close
	}

	return state, nil
}

// handleAPIKeyDialogKey is no longer used - API key dialog is now handled by the main controller
// using components.Dialog

// getCategoryKey returns the category key string for the current panel and focused category
func getCategoryKey(state *RedTeamConfigState) string {
	if state.ActivePanel == 0 {
		categories := GetVulnerabilityCategoryOrder()
		if state.FocusedCategory < len(categories) {
			return string(categories[state.FocusedCategory])
		}
	} else {
		categories := GetAttackCategoryOrder()
		if state.FocusedCategory < len(categories) {
			return string(categories[state.FocusedCategory])
		}
	}
	return ""
}

// getItemCountForCategory returns the number of items in the current category
func getItemCountForCategory(state *RedTeamConfigState) int {
	if state.ActivePanel == 0 {
		categories := GetVulnerabilityCategoryOrder()
		if state.FocusedCategory < len(categories) {
			vulns := GetSortedVulnerabilitiesForCategory(categories[state.FocusedCategory])
			return len(vulns)
		}
	} else {
		categories := GetAttackCategoryOrder()
		if state.FocusedCategory < len(categories) {
			attacks := GetSortedAttacksForCategory(categories[state.FocusedCategory])
			return len(attacks)
		}
	}
	return 0
}

// getNonEmptyVulnCategoryIndices returns indices of non-empty vulnerability categories
func getNonEmptyVulnCategoryIndices() []int {
	categories := GetVulnerabilityCategoryOrder()
	var indices []int
	for i, cat := range categories {
		vulns := GetSortedVulnerabilitiesForCategory(cat)
		if len(vulns) > 0 {
			indices = append(indices, i)
		}
	}
	return indices
}

// getNonEmptyAttackCategoryIndices returns indices of non-empty attack categories
func getNonEmptyAttackCategoryIndices() []int {
	categories := GetAttackCategoryOrder()
	var indices []int
	for i, cat := range categories {
		attacks := GetSortedAttacksForCategory(cat)
		if len(attacks) > 0 {
			indices = append(indices, i)
		}
	}
	return indices
}

// findNextNonEmptyCategory finds the next non-empty category index after current
func findNextNonEmptyCategory(state *RedTeamConfigState) int {
	var indices []int
	if state.ActivePanel == 0 {
		indices = getNonEmptyVulnCategoryIndices()
	} else {
		indices = getNonEmptyAttackCategoryIndices()
	}

	for _, idx := range indices {
		if idx > state.FocusedCategory {
			return idx
		}
	}
	return state.FocusedCategory // No next, stay where we are
}

// findPrevNonEmptyCategory finds the previous non-empty category index before current
func findPrevNonEmptyCategory(state *RedTeamConfigState) int {
	var indices []int
	if state.ActivePanel == 0 {
		indices = getNonEmptyVulnCategoryIndices()
	} else {
		indices = getNonEmptyAttackCategoryIndices()
	}

	prev := -1
	for _, idx := range indices {
		if idx >= state.FocusedCategory {
			break
		}
		prev = idx
	}
	if prev >= 0 {
		return prev
	}
	return state.FocusedCategory // No previous, stay where we are
}

func navigateUp(state *RedTeamConfigState) *RedTeamConfigState {
	if state.FocusedItem > -1 {
		// Move up within items
		state.FocusedItem--
	} else {
		// Move to previous non-empty category
		prevCat := findPrevNonEmptyCategory(state)
		if prevCat != state.FocusedCategory {
			state.FocusedCategory = prevCat
			// If the previous category is expanded, go to its last item
			categoryKey := getCategoryKey(state)
			if state.CategoryExpanded[categoryKey] {
				state.FocusedItem = getItemCountForCategory(state) - 1
			} else {
				state.FocusedItem = -1
			}
		}
	}
	return state
}

func navigateDown(state *RedTeamConfigState) *RedTeamConfigState {
	categoryKey := getCategoryKey(state)
	itemCount := getItemCountForCategory(state)

	// Check if category is expanded and we can move down within items
	if state.CategoryExpanded[categoryKey] && state.FocusedItem < itemCount-1 {
		state.FocusedItem++
	} else {
		// Move to next non-empty category
		nextCat := findNextNonEmptyCategory(state)
		if nextCat != state.FocusedCategory {
			state.FocusedCategory = nextCat
			state.FocusedItem = -1
		}
	}

	return state
}

func collapseCategory(state *RedTeamConfigState) *RedTeamConfigState {
	categoryKey := getCategoryKey(state)
	if categoryKey != "" {
		state.CategoryExpanded[categoryKey] = false
		state.FocusedItem = -1
	}
	return state
}

func expandCategory(state *RedTeamConfigState) *RedTeamConfigState {
	categoryKey := getCategoryKey(state)
	if categoryKey != "" {
		state.CategoryExpanded[categoryKey] = true
	}
	return state
}

func toggleSelection(state *RedTeamConfigState) *RedTeamConfigState {
	if state.FocusedItem == -1 {
		// Toggle entire category
		state = toggleCategorySelection(state)
		autoSave(state)
		return state
	}

	// Toggle individual item
	if state.ActivePanel == 0 {
		categories := GetVulnerabilityCategoryOrder()
		if state.FocusedCategory < len(categories) {
			vulns := GetSortedVulnerabilitiesForCategory(categories[state.FocusedCategory])
			if state.FocusedItem < len(vulns) {
				vuln := vulns[state.FocusedItem]
				// Check if premium and no API key
				if vuln.Premium && state.QualifireAPIKey == "" {
					return state // Can't select premium without API key
				}
				state.SelectedVulnerabilities[vuln.ID] = !state.SelectedVulnerabilities[vuln.ID]
			}
		}
	} else {
		categories := GetAttackCategoryOrder()
		if state.FocusedCategory < len(categories) {
			attacks := GetSortedAttacksForCategory(categories[state.FocusedCategory])
			if state.FocusedItem < len(attacks) {
				attack := attacks[state.FocusedItem]
				// Check if premium and no API key
				if attack.Premium && state.QualifireAPIKey == "" {
					return state // Can't select premium without API key
				}
				state.SelectedAttacks[attack.ID] = !state.SelectedAttacks[attack.ID]
			}
		}
	}

	state.ScanType = ScanTypeCustom
	autoSave(state)
	return state
}

func toggleCategorySelection(state *RedTeamConfigState) *RedTeamConfigState {
	if state.ActivePanel == 0 {
		categories := GetVulnerabilityCategoryOrder()
		if state.FocusedCategory < len(categories) {
			vulns := GetSortedVulnerabilitiesForCategory(categories[state.FocusedCategory])

			// Check if all are selected
			allSelected := true
			for _, vuln := range vulns {
				if !vuln.Premium || state.QualifireAPIKey != "" {
					if !state.SelectedVulnerabilities[vuln.ID] {
						allSelected = false
						break
					}
				}
			}

			// Toggle all
			for _, vuln := range vulns {
				if !vuln.Premium || state.QualifireAPIKey != "" {
					state.SelectedVulnerabilities[vuln.ID] = !allSelected
				}
			}
		}
	} else {
		categories := GetAttackCategoryOrder()
		if state.FocusedCategory < len(categories) {
			attacks := GetSortedAttacksForCategory(categories[state.FocusedCategory])

			// Check if all are selected
			allSelected := true
			for _, attack := range attacks {
				if !attack.Premium || state.QualifireAPIKey != "" {
					if !state.SelectedAttacks[attack.ID] {
						allSelected = false
						break
					}
				}
			}

			// Toggle all
			for _, attack := range attacks {
				if !attack.Premium || state.QualifireAPIKey != "" {
					state.SelectedAttacks[attack.ID] = !allSelected
				}
			}
		}
	}

	state.ScanType = ScanTypeCustom
	// Note: autoSave is called by the caller (toggleSelection)
	return state
}

func selectAllInCategory(state *RedTeamConfigState) *RedTeamConfigState {
	if state.ActivePanel == 0 {
		categories := GetVulnerabilityCategoryOrder()
		if state.FocusedCategory < len(categories) {
			vulns := GetSortedVulnerabilitiesForCategory(categories[state.FocusedCategory])
			for _, vuln := range vulns {
				if !vuln.Premium || state.QualifireAPIKey != "" {
					state.SelectedVulnerabilities[vuln.ID] = true
				}
			}
		}
	} else {
		categories := GetAttackCategoryOrder()
		if state.FocusedCategory < len(categories) {
			attacks := GetSortedAttacksForCategory(categories[state.FocusedCategory])
			for _, attack := range attacks {
				if !attack.Premium || state.QualifireAPIKey != "" {
					state.SelectedAttacks[attack.ID] = true
				}
			}
		}
	}

	state.ScanType = ScanTypeCustom
	return state
}

func deselectAllInCategory(state *RedTeamConfigState) *RedTeamConfigState {
	if state.ActivePanel == 0 {
		categories := GetVulnerabilityCategoryOrder()
		if state.FocusedCategory < len(categories) {
			vulns := GetSortedVulnerabilitiesForCategory(categories[state.FocusedCategory])
			for _, vuln := range vulns {
				state.SelectedVulnerabilities[vuln.ID] = false
			}
		}
	} else {
		categories := GetAttackCategoryOrder()
		if state.FocusedCategory < len(categories) {
			attacks := GetSortedAttacksForCategory(categories[state.FocusedCategory])
			for _, attack := range attacks {
				state.SelectedAttacks[attack.ID] = false
			}
		}
	}

	state.ScanType = ScanTypeCustom
	return state
}

func applyBasicPreset(state *RedTeamConfigState) *RedTeamConfigState {
	// Clear all selections
	state.SelectedVulnerabilities = make(map[string]bool)
	state.SelectedAttacks = make(map[string]bool)

	// Select basic vulnerabilities
	for _, id := range GetBasicScanVulnerabilities() {
		state.SelectedVulnerabilities[id] = true
	}

	// Select basic attacks
	for _, id := range GetBasicScanAttacks() {
		state.SelectedAttacks[id] = true
	}

	state.ScanType = ScanTypeBasic
	return state
}

func applyFullPreset(state *RedTeamConfigState) *RedTeamConfigState {
	// Clear all selections
	state.SelectedVulnerabilities = make(map[string]bool)
	state.SelectedAttacks = make(map[string]bool)

	// Select all free vulnerabilities
	for _, id := range GetFreeVulnerabilities() {
		state.SelectedVulnerabilities[id] = true
	}

	// Select all free attacks
	for _, id := range GetFreeAttacks() {
		state.SelectedAttacks[id] = true
	}

	// If API key present, also select premium
	if state.QualifireAPIKey != "" {
		for id, vuln := range VulnerabilityCatalog {
			if vuln.Premium {
				state.SelectedVulnerabilities[id] = true
			}
		}
		for id, attack := range AttackCatalog {
			if attack.Premium {
				state.SelectedAttacks[id] = true
			}
		}
	}

	state.ScanType = ScanTypeFull
	return state
}

func applyFrameworkSelection(state *RedTeamConfigState) *RedTeamConfigState {
	// Get unique vulnerabilities from selected frameworks
	selectedFWs := make([]string, 0)
	for id, selected := range state.SelectedFrameworks {
		if selected {
			selectedFWs = append(selectedFWs, id)
		}
	}

	// Clear and select vulnerabilities based on frameworks
	state.SelectedVulnerabilities = make(map[string]bool)
	for _, vulnID := range GetUniqueVulnerabilitiesForFrameworks(selectedFWs) {
		vuln := GetVulnerability(vulnID)
		if vuln != nil && (!vuln.Premium || state.QualifireAPIKey != "") {
			state.SelectedVulnerabilities[vulnID] = true
		}
	}

	// Auto-select default attacks for selected vulnerabilities
	attacksToSelect := make(map[string]bool)
	for vulnID, selected := range state.SelectedVulnerabilities {
		if selected {
			vuln := GetVulnerability(vulnID)
			if vuln != nil {
				for _, attackID := range vuln.DefaultAttacks {
					attack := GetAttack(attackID)
					if attack != nil && (!attack.Premium || state.QualifireAPIKey != "") {
						attacksToSelect[attackID] = true
					}
				}
			}
		}
	}

	state.SelectedAttacks = attacksToSelect
	state.ScanType = ScanTypeCustom

	return state
}

// GetSortedVulnerabilitiesForCategory returns vulnerabilities sorted by ID for consistent ordering
func GetSortedVulnerabilitiesForCategory(category VulnerabilityCategory) []*Vulnerability {
	byCategory := GetVulnerabilitiesByCategory()
	vulns := byCategory[category]

	// Sort by ID for consistent ordering
	sorted := make([]*Vulnerability, len(vulns))
	copy(sorted, vulns)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].ID < sorted[j].ID
	})

	return sorted
}

// GetSortedAttacksForCategory returns attacks sorted by ID for consistent ordering
func GetSortedAttacksForCategory(category AttackCategory) []*Attack {
	byCategory := GetAttacksByCategory()
	attacks := byCategory[category]

	// Sort by ID for consistent ordering
	sorted := make([]*Attack, len(attacks))
	copy(sorted, attacks)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].ID < sorted[j].ID
	})

	return sorted
}
