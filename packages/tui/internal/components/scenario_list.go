package components

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// handleListMode handles keyboard input in list mode
func (e ScenarioEditor) handleListMode(msg tea.KeyMsg) (ScenarioEditor, tea.Cmd) {
	switch msg.String() {
	case "escape", "esc":
		// Request parent to exit the scenarios screen
		return e, func() tea.Msg { return ScenarioEditorMsg{Action: "exit"} }
	case "up":
		if e.bizContextSelected {
			// Move from business context to last scenario
			e.bizContextSelected = false
			if len(e.filteredIdx) > 0 {
				e.selectedIndex = len(e.filteredIdx) - 1
				e.updateScroll()
			}
		} else if e.selectedIndex > 0 {
			e.selectedIndex--
			e.updateScroll()
		} else if len(e.filteredIdx) > 0 {
			// Move from first scenario to business context
			e.bizContextSelected = true
		}
		return e, nil

	case "down":
		if e.bizContextSelected {
			// Move from business context to first scenario
			e.bizContextSelected = false
			e.selectedIndex = 0
			e.updateScroll()
		} else if e.selectedIndex < len(e.filteredIdx)-1 {
			e.selectedIndex++
			e.updateScroll()
		} else {
			// Move from last scenario to business context
			e.bizContextSelected = true
		}
		return e, nil

	case "b":
		// Enter business context edit mode
		e.mode = BusinessContextMode
		if e.bizTextArea != nil {
			bizContext := ""
			if e.businessContext != nil {
				bizContext = *e.businessContext
			}
			e.bizTextArea.SetValue(bizContext)
			e.bizTextArea.Focus()
		}
		return e, nil

	case "/":
		// Open a dialog to enter search query (single OK button, no Cancel)
		dialog := NewInputDialog("Search Scenarios", "Type to filter scenarios:", e.searchQuery)
		dialog.Buttons = []DialogButton{{Label: "OK", Action: "ok", Style: PrimaryButton}}
		return e, func() tea.Msg { return DialogOpenMsg{Dialog: dialog} }

	case "enter":
		if e.bizContextSelected {
			// Enter business context edit mode
			e.mode = BusinessContextMode
			if e.bizTextArea != nil {
				bizContext := ""
				if e.businessContext != nil {
					bizContext = *e.businessContext
				}
				e.bizTextArea.SetValue(bizContext)
				e.bizTextArea.Focus()
			}
			e.errorMsg = ""
			e.infoMsg = ""
			return e, nil
		}
		if len(e.filteredIdx) == 0 {
			return e, nil
		}
		if e.selectedIndex > len(e.filteredIdx)-1 {
			e.selectedIndex = len(e.filteredIdx) - 1
		}

		idx := e.filteredIdx[e.selectedIndex]
		e.mode = EditMode
		e.editing = e.scenarios[idx]
		e.currentField = 0
		e.errorMsg = ""
		e.infoMsg = ""

		// Set up TextAreas with current values
		if e.scenarioTextArea != nil {
			e.scenarioTextArea.SetValue(e.editing.Scenario)
			e.scenarioTextArea.Focus()
		}
		if e.expectedOutcomeTextArea != nil {
			outVal := ""
			if e.editing.ExpectedOutcome != nil {
				outVal = *e.editing.ExpectedOutcome
			}
			e.expectedOutcomeTextArea.SetValue(outVal)
			e.expectedOutcomeTextArea.Blur()
		}
		return e, nil

	case "n", "a":
		// Add new scenario
		e.mode = AddMode
		e.editing = ScenarioData{ScenarioType: "policy"}
		e.currentField = 0
		e.errorMsg = ""
		e.infoMsg = ""

		// Set up TextAreas for new scenario
		if e.scenarioTextArea != nil {
			e.scenarioTextArea.SetValue("")
			e.scenarioTextArea.Focus()
		}
		if e.expectedOutcomeTextArea != nil {
			e.expectedOutcomeTextArea.SetValue("")
			e.expectedOutcomeTextArea.Blur()
		}
		return e, nil

	case "d", "delete":
		if e.bizContextSelected || len(e.filteredIdx) == 0 {
			return e, nil
		}
		// Ask for confirmation using a modal dialog
		idx := e.filteredIdx[e.selectedIndex]
		name := e.scenarios[idx].Scenario
		if len(name) > 60 {
			name = name[:57] + "..."
		}
		dialog := ShowDeleteConfirmationDialog(name)
		return e, func() tea.Msg { return DialogOpenMsg{Dialog: dialog} }

	case "s", "ctrl+s":
		// Save all scenarios to file
		if err := e.saveScenarios(); err != nil {
			e.errorMsg = fmt.Sprintf("Save error: %v", err)
		} else {
			e.infoMsg = "Scenarios saved"
		}
		return e, func() tea.Msg { return ScenarioEditorMsg{Action: "saved"} }

	case "i":
		// Start interview mode - enter the mode immediately and trigger API call
		e.mode = InterviewMode
		e.infoMsg = ""
		e.errorMsg = "" // Clear any previous errors

		// Initialize ChatView if not already done
		if e.interviewChatView == nil {
			chatView := NewChatView(9990, e.width, e.height, theme.CurrentTheme())
			e.interviewChatView = chatView
		}

		// Set loading state and clear any previous messages
		e.interviewChatView.ClearMessages()
		e.interviewChatView.SetLoading(true)

		// Send message to app.go to start the interview API call
		cmds := []tea.Cmd{
			func() tea.Msg { return StartInterviewMsg{} },
		}
		if e.interviewChatView != nil {
			cmds = append(cmds, e.interviewChatView.StartSpinner())
		}
		return e, tea.Batch(cmds...)

	default:
		return e, nil
	}
}

// renderListView renders the list of scenarios
func (e ScenarioEditor) renderListView(t theme.Theme) string {
	// file path and search status
	searchDisplay := e.searchQuery
	if searchDisplay == "" {
		searchDisplay = "(none)"
	}
	sub := lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render(
		fmt.Sprintf("File: %s  |  Search: %s  |  Matches: %d/%d", e.displayPath(), searchDisplay, len(e.filteredIdx), len(e.scenarios)),
	)

	// Business context section
	bizContext := ""
	if e.businessContext != nil {
		bizContext = *e.businessContext
	}
	bizLabel := "Business Context:"
	if e.bizContextSelected {
		bizLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("› Business Context:")
	} else {
		bizLabel = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Accent()).Render("Business Context:")
	}

	// Update viewport content and render
	var bizText string

	// Choose border style based on selection state
	var borderStyle lipgloss.Style
	if e.bizContextSelected {
		// Primary border and panel background when selected
		borderStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.Primary()).
			Background(t.BackgroundPanel()).
			BorderBackground(t.BackgroundPanel()).
			Padding(0, 1).
			Width(e.width - 8) // Account for padding and border
	} else {
		// Subtle border when not selected
		borderStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.TextMuted()).
			BorderBackground(t.BackgroundPanel()).
			Background(t.BackgroundPanel()).
			Padding(0, 1).
			Width(e.width - 8) // Account for padding and border
	}

	if e.bizViewport != nil {
		e.bizViewport.SetContent(bizContext)
		viewportContent := e.bizViewport.View()
		bizText = borderStyle.Render(viewportContent)
	} else {
		content := ellipsis(bizContext, e.width-20)
		bizText = borderStyle.Render(content)
	}

	// Show empty state banner if no scenarios and no business context
	var emptyBanner string
	if len(e.scenarios) == 0 && e.businessContext == nil {
		bannerWidth := e.width - 12
		emptyBanner = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(t.Primary()).
			Background(t.Background()).
			Padding(1, 2).
			Width(bannerWidth).
			Render(lipgloss.JoinVertical(
				lipgloss.Center,
				lipgloss.NewStyle().Foreground(t.Primary()).Bold(true).Width(bannerWidth-4).Align(lipgloss.Center).Render("🤖 No scenarios yet"),
				"",
				lipgloss.NewStyle().Foreground(t.Text()).Width(bannerWidth-4).Align(lipgloss.Center).Render("Let AI help you create scenarios through a quick interview"),
				"",
				lipgloss.NewStyle().Foreground(t.Accent()).Width(bannerWidth-4).Align(lipgloss.Center).Render("Press 'i' to start interview  or  'n' to add manually"),
			))
	}

	var body string
	if len(e.filteredIdx) == 0 {
		if emptyBanner != "" {
			body = emptyBanner
		} else {
			body = lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render("No scenarios match your search. Press 'n' to add.")
		}
	} else {
		start := e.scrollOffset
		end := start + e.visibleItems
		if end > len(e.filteredIdx) {
			end = len(e.filteredIdx)
		}

		// use near-full panel width (account for outer layout padding)
		contentWidth := e.width - 4
		if contentWidth < 60 {
			contentWidth = 60
		}
		typeWidth := 12
		remainingWidth := contentWidth - typeWidth
		colWidth := remainingWidth / 2
		if colWidth < 20 {
			colWidth = 20
		}

		// table header
		typeCol := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Accent()).Width(typeWidth).Render("Type")
		scenCol := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Accent()).Width(colWidth).Render("Scenario")
		outcomeCol := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Accent()).Width(colWidth).Render("Expected Outcome")
		rows := []string{lipgloss.JoinHorizontal(lipgloss.Left, typeCol, scenCol, outcomeCol)}

		for i := start; i < end; i++ {
			idx := e.filteredIdx[i]
			s := e.scenarios[idx]
			// Less intrusive selection: change type cell style only and use a subtle pointer
			pointer := "  "
			typeStyle := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text())
			scenStyle := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text())

			scenText := ellipsis(strings.ReplaceAll(s.Scenario, "\n", " "), colWidth-2)
			scenOutcome := ""
			if s.ExpectedOutcome != nil {
				scenOutcome = *s.ExpectedOutcome
				scenOutcome = strings.ReplaceAll(scenOutcome, "\n", " ")
			}
			scenOutcome = ellipsis(scenOutcome, colWidth-2)

			if i == e.selectedIndex && !e.bizContextSelected {
				pointer = "› "
				typeStyle = typeStyle.Background(t.Background()).Foreground(t.Primary()).Bold(true)
				scenStyle = scenStyle.Background(t.Background()).Foreground(t.Primary()).Bold(true)
			}

			line := lipgloss.JoinHorizontal(
				lipgloss.Left,
				typeStyle.Width(typeWidth).Render(pointer+s.ScenarioType),
				scenStyle.Width(colWidth).Render(scenText),
				scenStyle.Width(colWidth).Render(scenOutcome),
			)
			rows = append(rows, line)
		}

		// Add scroll indicators if needed
		scrollInfo := ""
		if len(e.filteredIdx) > e.visibleItems {
			canScrollUp := e.scrollOffset > 0
			canScrollDown := e.scrollOffset+e.visibleItems < len(e.filteredIdx)

			upIndicator := " "
			downIndicator := " "
			if canScrollUp {
				upIndicator = "↑"
			}
			if canScrollDown {
				downIndicator = "↓"
			}

			visibleCount := end - start
			scrollInfo = lipgloss.NewStyle().
				Background(t.Background()).
				Foreground(t.TextMuted()).
				Render(fmt.Sprintf(" Scroll: %s%s (%d-%d of %d)",
					upIndicator, downIndicator,
					start+1,
					start+visibleCount,
					len(e.filteredIdx)))
		}

		tableContent := strings.Join(rows, "\n")
		if scrollInfo != "" {
			tableContent += "\n" + scrollInfo
		}

		// Render table within a compact width and keep it left-aligned inside the panel
		body = lipgloss.NewStyle().Width(contentWidth).Background(t.Background()).Render(tableContent)
	}

	// Build lines and push help to bottom (above footer)
	help := lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render(
		"↑/↓ navigate  Enter edit  n new  i interview  d delete  / search  Esc back",
	)

	errorLine := ""
	if e.errorMsg != "" {
		errorLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Error()).Render("⚠ " + e.errorMsg)
	}
	infoLine := ""
	if e.infoMsg != "" {
		infoLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Success()).Render("✓ " + e.infoMsg)
	}

	// Build content sections
	var contentParts []string
	contentParts = append(contentParts, "", sub, "", bizLabel, bizText, "", body, "")

	// Add error/info messages if present
	if errorLine != "" {
		contentParts = append(contentParts, errorLine)
	}
	if infoLine != "" {
		contentParts = append(contentParts, infoLine)
	}

	// Add help at the end
	contentParts = append(contentParts, "", help)

	content := strings.Join(contentParts, "\n")

	// No outer border/background; return plain content to fill full height under layout
	return content
}

// updateScroll updates the scroll offset to keep selected item visible
func (e *ScenarioEditor) updateScroll() {
	// Ensure we have valid visible items calculation
	if e.visibleItems <= 0 {
		e.calculateVisibleItems()
	}

	// Clamp scroll offset to valid bounds
	maxScroll := len(e.filteredIdx) - e.visibleItems
	if maxScroll < 0 {
		maxScroll = 0
	}

	if e.selectedIndex < e.scrollOffset {
		e.scrollOffset = e.selectedIndex
	} else if e.selectedIndex >= e.scrollOffset+e.visibleItems {
		e.scrollOffset = e.selectedIndex - e.visibleItems + 1
	}

	// Ensure scroll offset is within bounds
	if e.scrollOffset < 0 {
		e.scrollOffset = 0
	}
	if e.scrollOffset > maxScroll {
		e.scrollOffset = maxScroll
	}
}

// rebuildFilter recalculates filtered indices based on fuzzy text search in scenario
func (e *ScenarioEditor) rebuildFilter() {
	e.filteredIdx = e.filteredIdx[:0]
	query := strings.ToLower(strings.TrimSpace(e.searchQuery))
	for i, s := range e.scenarios {
		if query == "" || strings.Contains(strings.ToLower(s.Scenario), query) {
			e.filteredIdx = append(e.filteredIdx, i)
		}
	}
	if e.selectedIndex >= len(e.filteredIdx) {
		e.selectedIndex = 0
	}
	if e.selectedIndex < 0 {
		e.selectedIndex = 0
	}
	// Reset business context selection when filtering
	if e.searchQuery != "" {
		e.bizContextSelected = false
	}
}

// rebuildFilterResetSelection resets selection and scroll when search changes
func (e *ScenarioEditor) rebuildFilterResetSelection() {
	e.rebuildFilter()
	e.selectedIndex = 0
	e.scrollOffset = 0
	e.bizContextSelected = false
}

// SetSearchQuery updates the search query and rebuilds the filtered list
func (e *ScenarioEditor) SetSearchQuery(query string) {
	e.searchQuery = strings.TrimSpace(query)
	e.rebuildFilterResetSelection()
}

// ClearSearchQuery clears the search query and rebuilds the filtered list
func (e *ScenarioEditor) ClearSearchQuery() {
	e.searchQuery = ""
	e.rebuildFilterResetSelection()
}

// ConfirmDelete deletes the currently selected scenario (after a confirmation dialog)
func (e *ScenarioEditor) ConfirmDelete() {
	if len(e.filteredIdx) == 0 {
		return
	}
	idx := e.filteredIdx[e.selectedIndex]
	if idx < 0 || idx >= len(e.scenarios) {
		return
	}
	e.scenarios = append(e.scenarios[:idx], e.scenarios[idx+1:]...)
	if e.selectedIndex >= len(e.filteredIdx)-1 && e.selectedIndex > 0 {
		e.selectedIndex--
	}
	e.rebuildFilter()
	if err := e.saveScenarios(); err != nil {
		e.errorMsg = fmt.Sprintf("Save error: %v", err)
		e.infoMsg = ""
		return
	}
	e.infoMsg = "Deleted scenario"
}
