package components

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea/v2"
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// handleBusinessContextMode handles keyboard input in business context edit mode
func (e ScenarioEditor) handleBusinessContextMode(msg tea.KeyMsg) (ScenarioEditor, tea.Cmd) {
	switch msg.String() {
	case "escape", "esc":
		// Save and exit business context edit mode
		if e.bizTextArea != nil {
			content := e.bizTextArea.GetValue()
			if content == "" {
				e.businessContext = nil
			} else {
				e.businessContext = &content
			}
			e.bizTextArea.Blur()
		}
		e.mode = ListMode
		e.calculateVisibleItems()   // Recalculate for list mode
		e.bizContextSelected = true // Keep business context selected when exiting edit mode
		e.errorMsg = ""
		e.infoMsg = ""
		return e, nil

	case "ctrl+s":
		// Save business context
		if e.bizTextArea != nil {
			content := e.bizTextArea.GetValue()
			if content == "" {
				e.businessContext = nil
			} else {
				e.businessContext = &content
			}
		}
		// Save to file
		if err := e.saveScenarios(); err != nil {
			e.errorMsg = fmt.Sprintf("Save error: %v", err)
		} else {
			e.infoMsg = "Business context saved"
		}
		return e, nil

	default:
		// Pass through to TextArea
		if e.bizTextArea != nil {
			updatedTextArea, cmd := e.bizTextArea.Update(msg)
			*e.bizTextArea = *updatedTextArea
			return e, cmd
		}
		return e, nil
	}
}

// renderBusinessContextView renders the business context editing interface
func (e ScenarioEditor) renderBusinessContextView(t theme.Theme) string {
	title := lipgloss.NewStyle().Background(t.Background()).Foreground(t.Primary()).Bold(true).Render("\nEdit Business Context")

	help := lipgloss.NewStyle().Background(t.Background()).Foreground(t.TextMuted()).Render("Esc save and exit  Ctrl+S save  Standard text editing keys")
	errorLine := ""
	if e.errorMsg != "" {
		errorLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Error()).Render("⚠ " + e.errorMsg)
	}
	infoLine := ""
	if e.infoMsg != "" {
		infoLine = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Success()).Render("✓ " + e.infoMsg)
	}

	// Calculate available height for textarea and border
	usedHeight := 0
	usedHeight += 2 // title (1 line) + blank line after title
	usedHeight += 2 // border top and bottom
	usedHeight += 1 // blank line before help
	usedHeight += 1 // help line
	if errorLine != "" {
		usedHeight += 1 // error line
	}
	if infoLine != "" {
		usedHeight += 1 // info line
	}

	// Calculate maximum textarea height (subtract from total available height)
	availableHeight := e.height - 1                    // -1 for parent layout
	textAreaHeight := availableHeight - usedHeight - 5 // -5 to prevent footer overflow
	if textAreaHeight < 5 {
		textAreaHeight = 5 // Minimum height
	}

	// Update textarea size to use maximum available height (account for border padding)
	var bizTextArea string
	if e.bizTextArea != nil {
		e.bizTextArea.SetSize(e.width-10, textAreaHeight) // -8 for border and padding
		bizTextArea = e.bizTextArea.View()
	} else {
		bizTextArea = lipgloss.NewStyle().Background(t.Background()).Foreground(t.Text()).Render("TextArea not available")
	}

	// Create bordered container for the textarea (primary border when editing)
	borderStyle := lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Primary()).
		Background(t.BackgroundPanel()).
		Padding(1, 1).
		Width(e.width - 4).        // Account for outer padding
		Height(textAreaHeight + 2) // +2 for border padding

	borderedTextArea := borderStyle.Render(bizTextArea)

	content := strings.Join([]string{
		title,
		"",
		borderedTextArea,
		"",
		help,
		errorLine,
		infoLine,
	}, "\n")

	return content
}
