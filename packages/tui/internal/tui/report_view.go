package tui

import (
	"strings"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// renderReport renders the evaluation report screen with summary
func (m Model) renderReport() string {
	t := theme.CurrentTheme()

	if m.evalState == nil {
		return lipgloss.NewStyle().
			Width(m.width).
			Height(m.height).
			Background(t.Background()).
			Foreground(t.Text()).
			Align(lipgloss.Center, lipgloss.Center).
			Render("No evaluation report available")
	}

	// Main container style with full width and height background
	mainStyle := lipgloss.NewStyle().
		Width(m.width).
		Height(m.height - 1). // -1 for footer
		Background(t.Background())

	// Title style
	titleStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(m.width).
		Align(lipgloss.Center).
		Padding(1, 0)

	header := titleStyle.Render("📊 Evaluation Report")

	// Report container
	reportStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.BackgroundPanel()).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(t.Border()).
		Padding(1, 2).
		Width(m.width - 4).
		Height(m.height - 8) // Leave space for header and help

	var reportContent string
	if m.evalState.Summary == "" {
		if m.evalState.Completed {
			// Evaluation completed but no summary yet
			reportContent = lipgloss.NewStyle().
				Foreground(t.TextMuted()).
				Italic(true).
				Render("Generating summary, please wait...")
		} else {
			// Evaluation not completed
			reportContent = lipgloss.NewStyle().
				Foreground(t.TextMuted()).
				Italic(true).
				Render("Evaluation not completed yet. Complete an evaluation to see the report.")
		}
	} else {
		// Show the actual summary
		reportContent = renderMarkdownSummary(t, m.evalState.Summary)
	}

	// Note: spacing handled by content area placement

	// Help text style
	helpStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(m.width).
		Align(lipgloss.Center).
		Padding(0, 1)

	helpText := helpStyle.Render("r Refresh   b Back to Dashboard   Esc Exit")

	// Calculate content area height
	contentHeight := m.height - 6 // title(3) + help(1) + margins(2)

	// Create content area
	contentArea := lipgloss.NewStyle().
		Width(m.width).
		Height(contentHeight).
		Background(t.Background())

	// Place report in the content area
	mainContent := contentArea.Render(
		lipgloss.Place(
			m.width,
			contentHeight,
			lipgloss.Center,
			lipgloss.Top,
			reportStyle.Render(reportContent),
			lipgloss.WithWhitespaceStyle(lipgloss.NewStyle().Background(t.Background())),
		),
	)

	// Combine all sections
	fullLayout := lipgloss.JoinVertical(lipgloss.Left,
		header,
		mainContent,
		helpText,
	)

	return mainStyle.Render(fullLayout)
}

// renderMarkdownSummary renders the markdown summary with basic styling
func renderMarkdownSummary(t theme.Theme, summary string) string {
	lines := strings.Split(summary, "\n")
	var styledLines []string

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			styledLines = append(styledLines, "")
			continue
		}

		// Basic markdown styling
		if strings.HasPrefix(line, "# ") {
			// H1 - Main title
			title := strings.TrimPrefix(line, "# ")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Primary()).
				Bold(true).
				Render("🔷 "+title))
		} else if strings.HasPrefix(line, "## ") {
			// H2 - Section headers
			title := strings.TrimPrefix(line, "## ")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Accent()).
				Bold(true).
				Render("▪ "+title))
		} else if strings.HasPrefix(line, "### ") {
			// H3 - Subsection headers
			title := strings.TrimPrefix(line, "### ")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Text()).
				Bold(true).
				Render("  • "+title))
		} else if strings.HasPrefix(line, "- ") || strings.HasPrefix(line, "* ") {
			// Bullet points
			content := strings.TrimPrefix(strings.TrimPrefix(line, "- "), "* ")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Text()).
				Render("    • "+content))
		} else if strings.HasPrefix(line, "**") && strings.HasSuffix(line, "**") {
			// Bold text
			content := strings.TrimSuffix(strings.TrimPrefix(line, "**"), "**")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Text()).
				Bold(true).
				Render(content))
		} else if strings.Contains(line, "`") {
			// Inline code (basic support)
			styled := strings.ReplaceAll(line, "`", "")
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Success()).
				Render(styled))
		} else {
			// Regular text
			styledLines = append(styledLines, lipgloss.NewStyle().
				Foreground(t.Text()).
				Render(line))
		}
	}

	return strings.Join(styledLines, "\n")
}
