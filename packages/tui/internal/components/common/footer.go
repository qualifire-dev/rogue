package common

import (
	"strings"

	"github.com/charmbracelet/lipgloss"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/commands"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/styles"
)

// Footer represents the application footer component with shortcuts
type Footer struct {
	width      int
	styles     *styles.Styles
	keyMap     *commands.KeyMap
	context    commands.CommandContext
	statusText string
	showStatus bool
}

// NewFooter creates a new footer component
func NewFooter(styles *styles.Styles, keyMap *commands.KeyMap) *Footer {
	return &Footer{
		width:      80,
		styles:     styles,
		keyMap:     keyMap,
		context:    commands.ContextGlobal,
		statusText: "",
		showStatus: false,
	}
}

// SetWidth sets the footer width
func (f *Footer) SetWidth(width int) {
	f.width = width
}

// SetContext sets the current context for showing relevant shortcuts
func (f *Footer) SetContext(context commands.CommandContext) {
	f.context = context
}

// SetStatus sets the status text
func (f *Footer) SetStatus(status string) {
	f.statusText = status
	f.showStatus = status != ""
}

// ClearStatus clears the status text
func (f *Footer) ClearStatus() {
	f.statusText = ""
	f.showStatus = false
}

// View renders the footer
func (f *Footer) View() string {
	// Get relevant shortcuts for current context
	shortcuts := f.getContextShortcuts()

	var content string
	if f.showStatus {
		// Show status and a few key shortcuts
		statusPart := f.styles.Text.Copy().Render(f.statusText)
		shortcutsPart := f.renderCustomShortcuts(shortcuts[:min(3, len(shortcuts))])

		content = lipgloss.JoinHorizontal(
			lipgloss.Bottom,
			statusPart,
			strings.Repeat(" ", max(0, f.width-lipgloss.Width(statusPart)-lipgloss.Width(shortcutsPart))),
			shortcutsPart,
		)
	} else {
		// Show more shortcuts when no status
		content = f.renderCustomShortcuts(shortcuts[:min(6, len(shortcuts))])
	}

	return f.styles.Footer.Copy().
		Width(f.width).
		Render(content)
}

// getContextShortcuts returns the most relevant shortcuts for the current context
func (f *Footer) getContextShortcuts() []string {
	shortcuts := []string{}

	switch f.context {
	case commands.ContextDashboard:
		shortcuts = []string{
			"ctrl+n new",
			"ctrl+e evaluations",
			"ctrl+i interview",
			"ctrl+c config",
			"ctrl+h help",
			"ctrl+q quit",
		}

	case commands.ContextEvaluations:
		shortcuts = []string{
			"↑↓ navigate",
			"enter view",
			"ctrl+n new",
			"ctrl+r refresh",
			"esc back",
			"ctrl+q quit",
		}

	case commands.ContextEvalDetail:
		shortcuts = []string{
			"↑↓ scroll",
			"ctrl+r refresh",
			"ctrl+e export",
			"esc back",
			"ctrl+q quit",
		}

	case commands.ContextInterview:
		shortcuts = []string{
			"type message",
			"enter send",
			"↑↓ scroll",
			"ctrl+e export",
			"esc end",
			"ctrl+q quit",
		}

	case commands.ContextConfig:
		shortcuts = []string{
			"tab navigate",
			"enter edit",
			"ctrl+s save",
			"esc back",
			"ctrl+q quit",
		}

	case commands.ContextNewEval:
		shortcuts = []string{
			"tab navigate",
			"enter continue",
			"ctrl+t test",
			"esc back",
			"ctrl+q quit",
		}

	case commands.ContextScenarios:
		shortcuts = []string{
			"↑↓ navigate",
			"enter edit",
			"ctrl+n new",
			"esc back",
			"ctrl+q quit",
		}

	default:
		shortcuts = []string{
			"/ commands",
			"ctrl+h help",
			"ctrl+q quit",
		}
	}

	return shortcuts
}

// calculateMaxShortcuts calculates how many shortcuts can fit in the available width
func (f *Footer) calculateMaxShortcuts() int {
	shortcuts := f.getContextShortcuts()
	if len(shortcuts) == 0 {
		return 0
	}

	// Estimate space needed for each shortcut (including separators)
	avgShortcutLength := 0
	for _, shortcut := range shortcuts {
		avgShortcutLength += len(shortcut)
	}
	avgShortcutLength = avgShortcutLength / len(shortcuts)

	// Add space for separators
	estimatedSpacePerShortcut := avgShortcutLength + 2

	return max(1, (f.width-4)/estimatedSpacePerShortcut) // -4 for padding
}

// ViewWithCustomShortcuts renders the footer with custom shortcuts
func (f *Footer) ViewWithCustomShortcuts(shortcuts []string) string {
	content := f.renderCustomShortcuts(shortcuts)

	return f.styles.Footer.Copy().
		Width(f.width).
		Render(content)
}

// renderCustomShortcuts renders custom shortcuts
func (f *Footer) renderCustomShortcuts(shortcuts []string) string {
	maxShortcuts := f.calculateMaxShortcuts()

	if len(shortcuts) > maxShortcuts {
		shortcuts = shortcuts[:maxShortcuts]
	}

	var parts []string
	for _, shortcut := range shortcuts {
		parts = append(parts, f.styles.Muted.Copy().Render(shortcut))
	}

	content := strings.Join(parts, "  ")
	return lipgloss.NewStyle().
		Width(f.width).
		Align(lipgloss.Center).
		Render(content)
}

// Helper functions
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func max(a, b int) int {
	if a > b {
		return a
	}
	return b
}
