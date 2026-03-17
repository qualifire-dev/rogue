package tui

import (
	"fmt"
	"os"
	"strings"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/screens/redteam_report"
	"github.com/rogue/tui/internal/theme"
)

// initializeRedTeamReportViewport sets up the red team report viewport with content
func (m *Model) initializeRedTeamReportViewport() {
	if m.redTeamReportData == nil {
		return
	}

	// Calculate viewport dimensions
	viewportHeight := m.height - 2 // -2 for footer

	// Set viewport size
	m.redTeamReportViewport.SetSize(m.width, viewportHeight)

	// Build report content
	content := redteam_report.BuildReportContent(m.width, m.redTeamReportData)

	// Prepend Rogue Security link if available
	if m.redTeamScanID != "" {
		t := theme.CurrentTheme()
		linkStyle := lipgloss.NewStyle().
			Foreground(t.Success()).
			Background(t.Background()).
			Bold(true).
			Width(m.width).
			Align(lipgloss.Center).
			Padding(1, 0)

		rogueSecurityBase := os.Getenv("ROGUE_SECURITY_URL")
		if rogueSecurityBase == "" {
			rogueSecurityBase = "https://app.rogue.security"
		}
		reportURL := fmt.Sprintf("%s/red-team/%s", rogueSecurityBase, m.redTeamScanID)
		linkText := linkStyle.Render(
			strings.Join([]string{"✅ Report saved to Rogue Security: ", reportURL}, ""),
		)
		content = linkText + "\n\n" + content
	}

	// Set content and go to top
	m.redTeamReportViewport.SetContent(content)
	m.redTeamReportViewport.GotoTop()
}
