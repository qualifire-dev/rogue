// Package redteam provides the red team configuration screen view.
package redteam

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
)

// Styles for the red team config view
var (
	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#FF6B6B")).
			MarginBottom(1)

	panelStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(lipgloss.Color("#444")).
			Padding(0, 1)

	activePanelStyle = lipgloss.NewStyle().
				Border(lipgloss.RoundedBorder()).
				BorderForeground(lipgloss.Color("#FF6B6B")).
				Padding(0, 1)

	categoryHeaderStyle = lipgloss.NewStyle().
				Bold(true).
				Foreground(lipgloss.Color("#88C0D0"))

	focusedCategoryStyle = lipgloss.NewStyle().
				Bold(true).
				Foreground(lipgloss.Color("#ECEFF4")).
				Background(lipgloss.Color("#5E81AC"))

	itemStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#D8DEE9"))

	focusedItemStyle = lipgloss.NewStyle().
				Foreground(lipgloss.Color("#ECEFF4")).
				Background(lipgloss.Color("#4C566A"))

	selectedStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#A3BE8C"))

	premiumStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#EBCB8B"))

	disabledStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#4C566A"))

	helpStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#616E88")).
			MarginTop(1)

	countStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#88C0D0"))

	statusBarStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#D8DEE9")).
			Background(lipgloss.Color("#3B4252")).
			Padding(0, 1)
)

// RenderConfigScreen renders the red team configuration screen.
func RenderConfigScreen(state *RedTeamConfigState, width, height int) string {
	var b strings.Builder

	// Title
	b.WriteString(titleStyle.Render("🔴 Red Team Configuration"))
	b.WriteString("\n\n")

	// Calculate panel dimensions
	// Account for: 2 borders per panel (4 total) + 2 padding per panel (4 total) + 2 space between
	// Total overhead = 10, so each panel gets (width - 10) / 2
	panelWidth := (width - 10) / 2
	panelHeight := height - 12 // Leave room for title, status bar, and help

	// Render panels side by side
	vulnPanel := renderVulnerabilityPanel(state, panelWidth, panelHeight)
	attackPanel := renderAttackPanel(state, panelWidth, panelHeight)

	// Apply active/inactive styling
	if state.ActivePanel == 0 {
		vulnPanel = activePanelStyle.Width(panelWidth).Height(panelHeight).Render(vulnPanel)
		attackPanel = panelStyle.Width(panelWidth).Height(panelHeight).Render(attackPanel)
	} else {
		vulnPanel = panelStyle.Width(panelWidth).Height(panelHeight).Render(vulnPanel)
		attackPanel = activePanelStyle.Width(panelWidth).Height(panelHeight).Render(attackPanel)
	}

	// Join panels horizontally
	panels := lipgloss.JoinHorizontal(lipgloss.Top, vulnPanel, "  ", attackPanel)
	b.WriteString(panels)
	b.WriteString("\n")

	// Status bar
	statusBar := renderStatusBar(state, width)
	b.WriteString(statusBar)
	b.WriteString("\n")

	// Help text
	helpText := renderHelpText(state)
	b.WriteString(helpStyle.Render(helpText))

	return b.String()
}

func renderVulnerabilityPanel(state *RedTeamConfigState, width, height int) string {
	var b strings.Builder

	// Panel header
	selectedCount := state.GetSelectedVulnerabilityCount()
	totalCount := len(VulnerabilityCatalog)
	header := fmt.Sprintf("Vulnerabilities (%d/%d)", selectedCount, totalCount)
	b.WriteString(categoryHeaderStyle.Render(header))
	b.WriteString("\n\n")

	// Render categories
	categories := GetVulnerabilityCategoryOrder()
	for catIdx, category := range categories {
		vulns := GetSortedVulnerabilitiesForCategory(category)
		if len(vulns) == 0 {
			continue
		}

		// Count selected in category
		categorySelected := 0
		for _, vuln := range vulns {
			if state.SelectedVulnerabilities[vuln.ID] {
				categorySelected++
			}
		}

		// Category header
		categoryKey := string(category)
		expanded := state.CategoryExpanded[categoryKey]
		expandIcon := "▸"
		if expanded {
			expandIcon = "▾"
		}

		catHeader := fmt.Sprintf("%s %s (%d/%d)", expandIcon, category, categorySelected, len(vulns))

		// Style based on focus - FocusedCategory is panel-local (0-indexed within this panel)
		isFocused := state.ActivePanel == 0 && state.FocusedCategory == catIdx && state.FocusedItem == -1
		if isFocused {
			b.WriteString(focusedCategoryStyle.Render(catHeader))
		} else {
			b.WriteString(categoryHeaderStyle.Render(catHeader))
		}
		b.WriteString("\n")

		// Render items if expanded
		if expanded {
			for itemIdx, vuln := range vulns {
				// Checkbox
				checkbox := "[ ]"
				if state.SelectedVulnerabilities[vuln.ID] {
					checkbox = "[✓]"
				}

				// Item text with premium indicator
				itemText := fmt.Sprintf("  %s %s", checkbox, vuln.Name)
				if vuln.Premium {
					itemText += " ★"
				}

				// Style based on focus and selection
				isFocusedItem := state.ActivePanel == 0 && state.FocusedCategory == catIdx && state.FocusedItem == itemIdx
				if isFocusedItem {
					b.WriteString(focusedItemStyle.Render(itemText))
				} else if vuln.Premium && state.QualifireAPIKey == "" {
					b.WriteString(disabledStyle.Render(itemText))
				} else if state.SelectedVulnerabilities[vuln.ID] {
					b.WriteString(selectedStyle.Render(itemText))
				} else {
					b.WriteString(itemStyle.Render(itemText))
				}
				b.WriteString("\n")
			}
		}
	}

	return b.String()
}

func renderAttackPanel(state *RedTeamConfigState, width, height int) string {
	var b strings.Builder

	// Panel header
	selectedCount := state.GetSelectedAttackCount()
	totalCount := len(AttackCatalog)
	header := fmt.Sprintf("Attacks (%d/%d)", selectedCount, totalCount)
	b.WriteString(categoryHeaderStyle.Render(header))
	b.WriteString("\n\n")

	// Render categories
	categories := GetAttackCategoryOrder()
	for catIdx, category := range categories {
		attacks := GetSortedAttacksForCategory(category)
		if len(attacks) == 0 {
			continue
		}

		// Count selected in category
		categorySelected := 0
		for _, attack := range attacks {
			if state.SelectedAttacks[attack.ID] {
				categorySelected++
			}
		}

		// Category header
		categoryKey := string(category)
		expanded := state.CategoryExpanded[categoryKey]
		expandIcon := "▸"
		if expanded {
			expandIcon = "▾"
		}

		catHeader := fmt.Sprintf("%s %s (%d/%d)", expandIcon, category, categorySelected, len(attacks))

		// Style based on focus - FocusedCategory is panel-local (0-indexed within this panel)
		isFocused := state.ActivePanel == 1 && state.FocusedCategory == catIdx && state.FocusedItem == -1
		if isFocused {
			b.WriteString(focusedCategoryStyle.Render(catHeader))
		} else {
			b.WriteString(categoryHeaderStyle.Render(catHeader))
		}
		b.WriteString("\n")

		// Render items if expanded
		if expanded {
			for itemIdx, attack := range attacks {
				// Checkbox
				checkbox := "[ ]"
				if state.SelectedAttacks[attack.ID] {
					checkbox = "[✓]"
				}

				// Item text with premium indicator
				itemText := fmt.Sprintf("  %s %s", checkbox, attack.Name)
				if attack.Premium {
					itemText += " ★"
				}

				// Style based on focus and selection
				isFocusedItem := state.ActivePanel == 1 && state.FocusedCategory == catIdx && state.FocusedItem == itemIdx
				if isFocusedItem {
					b.WriteString(focusedItemStyle.Render(itemText))
				} else if attack.Premium && state.QualifireAPIKey == "" {
					b.WriteString(disabledStyle.Render(itemText))
				} else if state.SelectedAttacks[attack.ID] {
					b.WriteString(selectedStyle.Render(itemText))
				} else {
					b.WriteString(itemStyle.Render(itemText))
				}
				b.WriteString("\n")
			}
		}
	}

	return b.String()
}

func renderStatusBar(state *RedTeamConfigState, width int) string {
	vulnCount := state.GetSelectedVulnerabilityCount()
	attackCount := state.GetSelectedAttackCount()
	frameworkCount := state.GetSelectedFrameworkCount()

	status := fmt.Sprintf(
		"Scan: %s | Vulnerabilities: %d | Attacks: %d | Frameworks: %d | Attacks/Vuln: %d",
		state.ScanType,
		vulnCount,
		attackCount,
		frameworkCount,
		state.AttacksPerVulnerability,
	)

	if state.HasPremiumSelections() && state.QualifireAPIKey == "" {
		status += " | ⚠ Premium features require API key"
	}

	return statusBarStyle.Width(width).Render(status)
}

func renderHelpText(state *RedTeamConfigState) string {
	if state.ShowFrameworkDialog {
		return "↑/↓: Navigate | Space: Toggle | Enter: Apply | Esc: Cancel"
	}
	if state.ShowAPIKeyDialog {
		return "Enter API key | Enter: Save | Esc: Cancel"
	}

	return "Tab: Switch panel | ↑/↓: Navigate | ←/→: Collapse/Expand | Space: Toggle | f: Frameworks | 1: Basic | 2: Full | Esc: Back"
}

// RenderFrameworkDialog renders the framework selection dialog.
func RenderFrameworkDialog(state *RedTeamConfigState, width, height int) string {
	var b strings.Builder

	dialogWidth := 50
	dialogHeight := 15

	b.WriteString(titleStyle.Render("Select Frameworks"))
	b.WriteString("\n\n")

	// List frameworks
	frameworks := GetAllFrameworks()
	for _, fw := range frameworks {
		checkbox := "[ ]"
		if state.SelectedFrameworks[fw.ID] {
			checkbox = "[✓]"
		}

		itemText := fmt.Sprintf("%s %s", checkbox, fw.Name)
		if state.SelectedFrameworks[fw.ID] {
			b.WriteString(selectedStyle.Render(itemText))
		} else {
			b.WriteString(itemStyle.Render(itemText))
		}
		b.WriteString("\n")
		b.WriteString(disabledStyle.Render("    " + fw.Description))
		b.WriteString("\n")
	}

	// Show unique vulnerability count
	selectedFWs := make([]string, 0)
	for id, selected := range state.SelectedFrameworks {
		if selected {
			selectedFWs = append(selectedFWs, id)
		}
	}
	uniqueVulns := GetUniqueVulnerabilitiesForFrameworks(selectedFWs)
	b.WriteString("\n")
	b.WriteString(countStyle.Render(fmt.Sprintf("Unique vulnerabilities: %d", len(uniqueVulns))))

	dialog := panelStyle.Width(dialogWidth).Height(dialogHeight).Render(b.String())

	// Center the dialog
	return lipgloss.Place(width, height, lipgloss.Center, lipgloss.Center, dialog)
}

// RenderAPIKeyDialog renders the API key input dialog.
func RenderAPIKeyDialog(state *RedTeamConfigState, width, height int) string {
	var b strings.Builder

	dialogWidth := 60

	b.WriteString(titleStyle.Render("Qualifire API Key"))
	b.WriteString("\n\n")
	b.WriteString(itemStyle.Render("Premium features require a Qualifire API key."))
	b.WriteString("\n")
	b.WriteString(itemStyle.Render("Get your key at: https://qualifire.ai/api-keys"))
	b.WriteString("\n\n")

	// Input field
	inputStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#5E81AC")).
		Padding(0, 1)

	maskedKey := strings.Repeat("*", len(state.APIKeyInput))
	if maskedKey == "" {
		maskedKey = "Enter your API key..."
	}
	b.WriteString(inputStyle.Width(dialogWidth - 4).Render(maskedKey))

	dialog := panelStyle.Width(dialogWidth).Render(b.String())

	return lipgloss.Place(width, height, lipgloss.Center, lipgloss.Center, dialog)
}
