package tui

import (
	"github.com/rogue/tui/internal/screens/redteam_report"
)

// initializeRedTeamReportViewport sets up the red team report viewport with content
func (m *Model) initializeRedTeamReportViewport() {
	if m.redTeamReportData == nil {
		return
	}

	// Convert data to ReportData struct
	reportData := m.convertToReportData(m.redTeamReportData)
	if reportData == nil {
		return
	}

	// Calculate viewport dimensions
	viewportHeight := m.height - 2 // -2 for footer

	// Set viewport size
	m.redTeamReportViewport.SetSize(m.width, viewportHeight)

	// Build report content
	content := redteam_report.BuildReportContent(m.width, reportData)

	// Set content and go to top
	m.redTeamReportViewport.SetContent(content)
	m.redTeamReportViewport.GotoTop()
}
