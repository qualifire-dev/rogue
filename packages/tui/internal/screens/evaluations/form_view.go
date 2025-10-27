package evaluations

import (
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/theme"
)

// RenderForm renders the new evaluation form screen
// Note: This is a placeholder function kept for potential future refactoring.
// Currently, the actual rendering is done in internal/tui/eval_form_view.go
// as the evaluation screens are tightly coupled with the Model type.
func RenderForm(width, height int, evalState interface{}, spinner *components.Spinner) string {
	t := theme.CurrentTheme()

	// Placeholder implementation
	// The real implementation is in internal/tui/eval_form_view.go
	// This function exists to maintain the package structure for future refactoring

	message := `🧪 Evaluation Form

This is a placeholder. The actual evaluation form is rendered
through the main TUI model due to tight coupling with application state.

See: internal/tui/eval_form_view.go for the active implementation.`

	return lipgloss.NewStyle().
		Width(width).
		Height(height).
		Background(t.Background()).
		Foreground(t.Text()).
		Align(lipgloss.Center, lipgloss.Center).
		Render(message)
}
