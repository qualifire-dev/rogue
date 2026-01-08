package redteam_report

import (
	"strconv"
	"strings"

	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/components"
	"github.com/rogue/tui/internal/styles"
	"github.com/rogue/tui/internal/theme"
)

// ReportData contains the red team report data
type ReportData struct {
	Metadata           ReportMetadata          `json:"metadata"`
	Highlights         ReportHighlights        `json:"highlights"`
	KeyFindings        []KeyFinding            `json:"key_findings"`
	VulnerabilityTable []VulnerabilityTableRow `json:"vulnerability_table"`
	FrameworkCoverage  []FrameworkCoverageCard `json:"framework_coverage"`
	ExportPaths        ExportPaths             `json:"export_paths"`
}

// ReportMetadata contains metadata about the scan
type ReportMetadata struct {
	ScanDate         string   `json:"scan_date"`
	ScanType         string   `json:"scan_type"`
	FrameworksTested []string `json:"frameworks_tested"`
	AttacksUsed      []string `json:"attacks_used"`
	RandomSeed       *int     `json:"random_seed"`
}

// ReportHighlights contains summary statistics
type ReportHighlights struct {
	CriticalCount              int               `json:"critical_count"`
	HighCount                  int               `json:"high_count"`
	MediumCount                int               `json:"medium_count"`
	LowCount                   int               `json:"low_count"`
	TotalVulnerabilitiesTested int               `json:"total_vulnerabilities_tested"`
	TotalVulnerabilitiesFound  int               `json:"total_vulnerabilities_found"`
	OverallScore               float64           `json:"overall_score"`
	SeverityColors             map[string]string `json:"severity_colors"`
}

// KeyFinding represents a top critical vulnerability
type KeyFinding struct {
	VulnerabilityID   string   `json:"vulnerability_id"`
	VulnerabilityName string   `json:"vulnerability_name"`
	CVSSScore         float64  `json:"cvss_score"`
	Severity          string   `json:"severity"`
	Summary           string   `json:"summary"`
	AttackIDs         []string `json:"attack_ids"`
	SuccessRate       float64  `json:"success_rate"`
	Color             string   `json:"color"`
}

// VulnerabilityTableRow represents a row in the vulnerability table
type VulnerabilityTableRow struct {
	VulnerabilityID   string   `json:"vulnerability_id"`
	VulnerabilityName string   `json:"vulnerability_name"`
	Severity          *string  `json:"severity"`
	AttacksUsed       []string `json:"attacks_used"`
	AttacksAttempted  int      `json:"attacks_attempted"`
	AttacksSuccessful int      `json:"attacks_successful"`
	SuccessRate       float64  `json:"success_rate"`
	Passed            bool     `json:"passed"`
	Color             string   `json:"color"`
	StatusIcon        string   `json:"status_icon"`
}

// FrameworkCoverageCard represents framework compliance status
type FrameworkCoverageCard struct {
	FrameworkID     string  `json:"framework_id"`
	FrameworkName   string  `json:"framework_name"`
	ComplianceScore float64 `json:"compliance_score"`
	TestedCount     int     `json:"tested_count"`
	TotalCount      int     `json:"total_count"`
	PassedCount     int     `json:"passed_count"`
	Status          string  `json:"status"`
	Color           string  `json:"color"`
	Icon            string  `json:"icon"`
}

// ExportPaths contains paths to CSV exports
type ExportPaths struct {
	ConversationsCSV *string `json:"conversations_csv"`
	SummaryCSV       *string `json:"summary_csv"`
}

// Render renders the red team report screen with scrolling support
// Note: Content should be initialized via initializeRedTeamReportViewport() before rendering
func Render(width, height int, viewport *components.Viewport) string {
	t := theme.CurrentTheme()

	// Check if viewport has content
	if viewport.GetContent() == "" {
		return renderNoReport(width, height, t)
	}

	// Main container style
	mainStyle := lipgloss.NewStyle().
		Width(width).
		Height(height).
		Background(t.Background())

	// Just render the viewport - size is set during initialization
	// Do NOT call SetSize here as it can interfere with scrolling
	viewportContent := viewport.View()

	// Calculate content area height (leave room for footer)
	contentHeight := height - 2

	// Place viewport content with proper whitespace styling
	placedContent := lipgloss.Place(
		width,
		contentHeight,
		lipgloss.Left,
		lipgloss.Top,
		viewportContent,
		styles.WhitespaceStyle(t.Background()),
	)

	// Footer with help text
	footerStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(width).
		Align(lipgloss.Center)

	footer := footerStyle.Render("↑↓ Scroll | PgUp/PgDn Page | e Export CSV | b Back | Esc Exit")

	// Combine viewport and footer
	fullLayout := lipgloss.JoinVertical(
		lipgloss.Left,
		placedContent,
		footer,
	)

	return mainStyle.Render(fullLayout)
}

func renderNoReport(width, height int, t theme.Theme) string {
	mainStyle := lipgloss.NewStyle().
		Width(width).
		Height(height).
		Background(t.Background())

	message := "No red team report available. Run a red team scan first."

	placedMessage := lipgloss.Place(
		width,
		height,
		lipgloss.Center,
		lipgloss.Center,
		message,
		styles.WhitespaceStyle(t.Background()),
	)

	return mainStyle.Render(placedMessage)
}

// BuildReportContent builds the complete report content string (exported for initialization)
func BuildReportContent(width int, report *ReportData) string {
	t := theme.CurrentTheme()
	return buildReportContentInternal(width, report, t)
}

func buildReportContentInternal(width int, report *ReportData, t theme.Theme) string {
	var sections []string

	// Header
	sections = append(sections, renderHeader(width, report, t))

	// Highlights Section
	sections = append(sections, renderHighlights(width, report, t))

	// Key Findings Section
	if len(report.KeyFindings) > 0 {
		sections = append(sections, renderKeyFindings(width, report, t))
	}

	// Vulnerability Table Section
	sections = append(sections, renderVulnerabilityTable(width, report, t))

	// Framework Coverage Section (always shown)
	sections = append(sections, renderFrameworkCoverage(width, report, t))

	// Export info
	if report.ExportPaths.SummaryCSV != nil {
		sections = append(sections, renderExportInfo(width, report, t))
	}

	return strings.Join(sections, "\n\n")
}

func renderHeader(width int, report *ReportData, t theme.Theme) string {
	titleStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(width).
		Align(lipgloss.Center).
		Padding(1, 0)

	dateStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background()).
		Width(width).
		Align(lipgloss.Center)

	// Extract date (just the date part)
	scanDate := report.Metadata.ScanDate
	if len(scanDate) > 10 {
		scanDate = scanDate[:10]
	}

	title := titleStyle.Render("🛡️  Red Team Security Report")

	dateText := lipgloss.JoinHorizontal(
		lipgloss.Left,
		"Scan Date: ",
		scanDate,
		" | Type: ",
		strings.ToUpper(report.Metadata.ScanType),
	)
	date := dateStyle.Render(dateText)

	return title + "\n" + date
}

func renderHighlights(width int, report *ReportData, t theme.Theme) string {
	sectionTitle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(width).
		Padding(0, 0, 1, 0).
		Render("📊 HIGHLIGHTS")

	// Create severity cards
	cardWidth := (width - 6) / 4 // 4 cards with spacing
	if cardWidth < 10 {
		cardWidth = 10
	}

	criticalCard := renderSeverityCard("CRITICAL", report.Highlights.CriticalCount, "#DC2626", cardWidth, t)
	highCard := renderSeverityCard("HIGH", report.Highlights.HighCount, "#EA580C", cardWidth, t)
	mediumCard := renderSeverityCard("MEDIUM", report.Highlights.MediumCount, "#CA8A04", cardWidth, t)
	lowCard := renderSeverityCard("LOW", report.Highlights.LowCount, "#16A34A", cardWidth, t)

	cardsContent := lipgloss.JoinHorizontal(
		lipgloss.Top,
		criticalCard,
		" ",
		highCard,
		" ",
		mediumCard,
		" ",
		lowCard,
	)

	cardsStyle := lipgloss.NewStyle().
		Width(width).
		Background(t.Background())

	cards := cardsStyle.Render(cardsContent)

	// Overall score
	scoreStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.Background()).
		Width(width).
		Padding(1, 0, 0, 0)

	scoreText := lipgloss.JoinHorizontal(
		lipgloss.Left,
		"Overall Security Score: ",
		strconv.FormatFloat(report.Highlights.OverallScore, 'f', 1, 64),
		"/100 | Vulnerabilities: ",
		strconv.Itoa(report.Highlights.TotalVulnerabilitiesFound),
		"/",
		strconv.Itoa(report.Highlights.TotalVulnerabilitiesTested),
		" found",
	)
	score := scoreStyle.Render(scoreText)

	return sectionTitle + "\n" + cards + "\n" + score
}

func renderSeverityCard(label string, count int, color string, width int, t theme.Theme) string {
	cardStyle := lipgloss.NewStyle().
		Width(width).
		Padding(1).
		Align(lipgloss.Center).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color(color)).
		BorderBackground(t.Background()).
		Background(t.Background())

	icon := ""
	switch label {
	case "CRITICAL":
		icon = "🔴"
	case "HIGH":
		icon = "🟠"
	case "MEDIUM":
		icon = "🟡"
	case "LOW":
		icon = "🟢"
	}

	line1 := lipgloss.JoinHorizontal(lipgloss.Left, icon, " ", strconv.Itoa(count))
	content := lipgloss.JoinVertical(lipgloss.Center, line1, label)
	return cardStyle.Render(content)
}

func renderKeyFindings(width int, report *ReportData, t theme.Theme) string {
	sectionTitle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(width).
		Padding(0, 0, 1, 0).
		Render("🔍 KEY FINDINGS (Top 5 Critical Vulnerabilities)")

	var findings []string
	for i, finding := range report.KeyFindings {
		if i >= 5 {
			break
		}

		findingStyle := lipgloss.NewStyle().
			Background(t.Background()).
			Padding(0, 0, 1, 0).
			Width(width)

		severityIcon := getSeverityIcon(finding.Severity)
		headerStyle := lipgloss.NewStyle().
			Foreground(lipgloss.Color(finding.Color)).
			Background(t.Background()).
			Width(width).
			Bold(true)

		headerText := lipgloss.JoinHorizontal(
			lipgloss.Left,
			strconv.Itoa(i+1),
			". ",
			severityIcon,
			" ",
			finding.VulnerabilityName,
			" [CVSS: ",
			strconv.FormatFloat(finding.CVSSScore, 'f', 1, 64),
			" / ",
			strings.ToUpper(finding.Severity),
			"]",
		)
		header := headerStyle.Render(headerText)

		summary := lipgloss.NewStyle().
			Foreground(t.Text()).
			Background(t.Background()).
			Width(width).
			Padding(0, 0, 0, 3).
			Render(finding.Summary)

		attacksStyle := lipgloss.NewStyle().
			Foreground(t.TextMuted()).
			Background(t.Background()).
			Width(width).
			Padding(0, 0, 0, 3)

		attacksText := lipgloss.JoinHorizontal(
			lipgloss.Left,
			"Attacks: ",
			strings.Join(finding.AttackIDs, ", "),
			" | Success Rate: ",
			strconv.FormatFloat(finding.SuccessRate*100, 'f', 1, 64),
			"%",
		)
		attacks := attacksStyle.Render(attacksText)

		findingText := lipgloss.JoinVertical(lipgloss.Left, header, summary, attacks)
		findings = append(findings, findingStyle.Render(findingText))
	}

	return sectionTitle + "\n" + strings.Join(findings, "\n")
}

func renderVulnerabilityTable(width int, report *ReportData, t theme.Theme) string {
	sectionTitle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(width).
		Padding(0, 0, 1, 0).
		Render("📋 VULNERABILITY BREAKDOWN")

	// Table header
	headerStyle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true)

	// Column widths (with spacing)
	nameWidth := 30
	statusWidth := 8
	severityWidth := 10
	rateWidth := 12
	spacing := 2 // Space between columns
	attacksWidth := width - nameWidth - statusWidth - severityWidth - rateWidth - (spacing * 4) - 10

	// Ensure minimum width to avoid negative values
	if attacksWidth < 5 {
		attacksWidth = 5
	}

	spacer := lipgloss.NewStyle().Width(spacing).Render("")

	headerContent := lipgloss.JoinHorizontal(
		lipgloss.Top,
		headerStyle.Width(nameWidth).Render("Vulnerability"),
		spacer,
		headerStyle.Width(statusWidth).Render("Status"),
		spacer,
		headerStyle.Width(severityWidth).Render("Severity"),
		spacer,
		headerStyle.Width(rateWidth).Render("Success Rate"),
		spacer,
		headerStyle.Width(attacksWidth).Render("Attacks"),
	)

	fullHeaderStyle := lipgloss.NewStyle().
		Width(width).
		Background(t.Background())

	header := fullHeaderStyle.Render(headerContent)

	// Table rows
	var rows []string
	for _, row := range report.VulnerabilityTable {
		rowStyle := lipgloss.NewStyle().
			Foreground(t.Text()).
			Background(t.Background())

		name := rowStyle.Width(nameWidth).Render(truncate(row.VulnerabilityName, nameWidth-2))
		status := rowStyle.Width(statusWidth).Render(row.StatusIcon)

		severity := "-"
		if row.Severity != nil {
			severity = strings.ToUpper(*row.Severity)
		}
		severityCell := rowStyle.Width(severityWidth).Render(severity)

		rateText := lipgloss.JoinHorizontal(lipgloss.Left, strconv.FormatFloat(row.SuccessRate, 'f', 0, 64), "%")
		rate := rowStyle.Width(rateWidth).Render(rateText)

		attacks := strings.Join(row.AttacksUsed, ", ")
		if attacksWidth > 5 && len(attacks) > attacksWidth-2 {
			attacks = attacks[:attacksWidth-5] + "..."
		} else if attacksWidth <= 5 && len(attacks) > 0 {
			attacks = "..."
		}
		attacksCell := rowStyle.Width(attacksWidth).Render(attacks)

		rowContent := lipgloss.JoinHorizontal(
			lipgloss.Top,
			name,
			spacer,
			status,
			spacer,
			severityCell,
			spacer,
			rate,
			spacer,
			attacksCell,
		)

		fullRowStyle := lipgloss.NewStyle().
			Width(width).
			Background(t.Background())

		rowText := fullRowStyle.Render(rowContent)
		rows = append(rows, rowText)
	}

	return sectionTitle + "\n" + header + "\n" + strings.Join(rows, "\n")
}

func renderFrameworkCoverage(width int, report *ReportData, t theme.Theme) string {
	sectionTitle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(width).
		Padding(0, 0, 1, 0).
		Render("🎯 FRAMEWORK COMPLIANCE")

	cardWidth := (width - 8) / 3 // 3 cards per row
	if cardWidth < 20 {
		cardWidth = 20
	}

	var cards []string
	var currentRow []string

	rowStyle := lipgloss.NewStyle().
		Width(width).
		Background(t.Background())

	for i, card := range report.FrameworkCoverage {
		cardContent := renderFrameworkCard(card, cardWidth, t)
		currentRow = append(currentRow, cardContent)

		// Join every 3 cards or at the end
		if (i+1)%3 == 0 || i == len(report.FrameworkCoverage)-1 {
			rowContent := lipgloss.JoinHorizontal(lipgloss.Top, currentRow...)
			row := rowStyle.Render(rowContent)
			cards = append(cards, row)
			currentRow = []string{}
		}
	}

	return sectionTitle + "\n" + strings.Join(cards, "\n")
}

func renderFrameworkCard(card FrameworkCoverageCard, width int, t theme.Theme) string {
	cardStyle := lipgloss.NewStyle().
		Width(width).
		Padding(1).
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color(card.Color)).
		BorderBackground(t.Background()).
		Background(t.Background()).
		Align(lipgloss.Center)

	nameStyle := lipgloss.NewStyle().
		Bold(true).
		Foreground(lipgloss.Color(card.Color)).
		Background(t.Background())

	nameText := lipgloss.JoinHorizontal(lipgloss.Center, card.Icon, " ", card.FrameworkName)
	name := nameStyle.Render(nameText)

	var score string
	var coverage string

	scoreStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.Background())

	coverageStyle := lipgloss.NewStyle().
		Foreground(t.TextMuted()).
		Background(t.Background())

	if card.Status == "not_tested" {
		// Show "Not Tested" for untested frameworks
		score = scoreStyle.Foreground(t.TextMuted()).Render("Not Tested")

		coverageText := lipgloss.JoinHorizontal(
			lipgloss.Left,
			"0/",
			strconv.Itoa(card.TotalCount),
			" tested",
		)
		coverage = coverageStyle.Render(coverageText)
	} else {
		// Show score and coverage for tested frameworks
		failedCount := card.TestedCount - card.PassedCount

		scoreText := lipgloss.JoinHorizontal(
			lipgloss.Left,
			strconv.FormatFloat(card.ComplianceScore, 'f', 0, 64),
			"%",
		)
		score = scoreStyle.Render(scoreText)

		coverageText := lipgloss.JoinHorizontal(
			lipgloss.Left,
			strconv.Itoa(card.TestedCount),
			"/",
			strconv.Itoa(card.TotalCount),
			" tested ✓",
			strconv.Itoa(card.PassedCount),
			" ✗",
			strconv.Itoa(failedCount),
		)
		coverage = coverageStyle.Render(coverageText)
	}

	content := lipgloss.JoinVertical(lipgloss.Center, name, score, coverage)
	return cardStyle.Render(content)
}

func renderExportInfo(width int, report *ReportData, t theme.Theme) string {
	sectionTitle := lipgloss.NewStyle().
		Foreground(t.Primary()).
		Background(t.Background()).
		Bold(true).
		Width(width).
		Padding(0, 0, 1, 0).
		Render("📁 EXPORTS")

	infoStyle := lipgloss.NewStyle().
		Foreground(t.Text()).
		Background(t.Background()).
		Width(width)

	var infoParts []string
	infoParts = append(infoParts, "Results have been exported to .rogue folder:")

	if report.ExportPaths.SummaryCSV != nil {
		summaryLine := lipgloss.JoinHorizontal(lipgloss.Left, "- Summary: ", *report.ExportPaths.SummaryCSV)
		infoParts = append(infoParts, summaryLine)
	}
	if report.ExportPaths.ConversationsCSV != nil {
		conversationsLine := lipgloss.JoinHorizontal(lipgloss.Left, "- Conversations: ", *report.ExportPaths.ConversationsCSV)
		infoParts = append(infoParts, conversationsLine)
	}

	info := strings.Join(infoParts, "\n")
	return sectionTitle + "\n" + infoStyle.Render(info)
}

func getSeverityIcon(severity string) string {
	switch strings.ToLower(severity) {
	case "critical":
		return "🔴"
	case "high":
		return "🟠"
	case "medium":
		return "🟡"
	case "low":
		return "🟢"
	default:
		return "⚪"
	}
}

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	if maxLen <= 3 {
		return "..."
	}
	return s[:maxLen-3] + "..."
}
