package tui

import (
	"strings"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/theme"
)

// normalizeEvaluationRole maps evaluation-specific roles to MessageHistoryView roles
// MessageHistoryView expects: "user", "assistant", or "system"
// In evaluation context:
//   - "user" represents the evaluator/judge (Rogue)
//   - "assistant" represents the agent being tested
//   - "system" represents system messages
func normalizeEvaluationRole(role string) string {
	// Normalize role string (trim whitespace and lowercase for matching)
	roleLower := strings.ToLower(strings.TrimSpace(role))

	// Check if role contains agent-related keywords
	if strings.Contains(roleLower, "agent") {
		// Agent under test shown as "assistant" (will use assistantPrefix: "🤖 Agent: ")
		return "assistant"
	}

	// Check if role contains evaluator/rogue/judge keywords
	if strings.Contains(roleLower, "rogue") ||
		strings.Contains(roleLower, "judge") ||
		strings.Contains(roleLower, "evaluator") {
		// Evaluator/Judge messages shown as "user" (will use userPrefix: "🔍 Rogue: ")
		return "user"
	}

	// Check for system messages
	if strings.Contains(roleLower, "system") {
		return "system"
	}

	// Default: if role is empty or unknown, treat as evaluator
	// This ensures messages are visible even if role is malformed
	return "user"
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

// getDynamicModels returns cached dynamic models, or nil if unavailable.
func (m Model) getDynamicModels() map[string][]string {
	if m.modelCache == nil {
		return nil
	}
	return m.modelCache.GetAllProviderModels()
}
