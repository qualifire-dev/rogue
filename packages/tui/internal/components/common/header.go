package common

import (
	"fmt"

	"github.com/charmbracelet/lipgloss"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/styles"
)

// Header represents the application header component
type Header struct {
	title       string
	subtitle    string
	version     string
	width       int
	showVersion bool
	styles      *styles.Styles
}

// NewHeader creates a new header component
func NewHeader(styles *styles.Styles) *Header {
	return &Header{
		title:       "rogue",
		subtitle:    "",
		version:     "v1.0.0",
		width:       80,
		showVersion: true,
		styles:      styles,
	}
}

// SetTitle sets the header title
func (h *Header) SetTitle(title string) {
	h.title = title
}

// SetSubtitle sets the header subtitle
func (h *Header) SetSubtitle(subtitle string) {
	h.subtitle = subtitle
}

// SetVersion sets the version string
func (h *Header) SetVersion(version string) {
	h.version = version
}

// SetWidth sets the header width
func (h *Header) SetWidth(width int) {
	h.width = width
}

// ShowVersion controls whether to show the version
func (h *Header) ShowVersion(show bool) {
	h.showVersion = show
}

// View renders the header
func (h *Header) View() string {
	// Create the main title
	titleStyle := h.styles.Title.Copy()
	title := titleStyle.Render(h.title)

	// Add version if enabled
	if h.showVersion && h.version != "" {
		versionStyle := h.styles.Muted.Copy()
		title += " " + versionStyle.Render(h.version)
	}

	// Add subtitle if present
	var content string
	if h.subtitle != "" {
		subtitleStyle := h.styles.Subtitle.Copy()
		subtitle := subtitleStyle.Render(h.subtitle)
		content = lipgloss.JoinVertical(lipgloss.Left, title, subtitle)
	} else {
		content = title
	}

	// Center the content
	centeredContent := lipgloss.NewStyle().
		Width(h.width).
		Align(lipgloss.Center).
		Render(content)

	// Apply header styling
	return h.styles.Header.Copy().
		Width(h.width).
		Render(centeredContent)
}

// ViewCompact renders a compact version of the header
func (h *Header) ViewCompact() string {
	title := h.title
	if h.showVersion && h.version != "" {
		title += " " + h.version
	}
	if h.subtitle != "" {
		title += " - " + h.subtitle
	}

	return h.styles.Header.Copy().
		Width(h.width).
		Render(title)
}

// SetContext updates the header based on current context
func (h *Header) SetContext(screen string, data map[string]interface{}) {
	switch screen {
	case "dashboard":
		h.SetTitle("rogue")
		h.SetSubtitle("")

	case "evaluations":
		h.SetTitle("rogue")
		h.SetSubtitle("evaluations")

	case "eval_detail":
		h.SetTitle("rogue")
		if evalID, ok := data["eval_id"].(string); ok {
			h.SetSubtitle(fmt.Sprintf("evaluation #%s", evalID))
		} else {
			h.SetSubtitle("evaluation details")
		}

	case "new_eval":
		h.SetTitle("rogue")
		h.SetSubtitle("new evaluation")

	case "interview":
		h.SetTitle("rogue")
		if sessionID, ok := data["session_id"].(string); ok {
			h.SetSubtitle(fmt.Sprintf("interview #%s", sessionID))
		} else {
			h.SetSubtitle("interview mode")
		}

	case "config":
		h.SetTitle("rogue")
		h.SetSubtitle("configuration")

	case "scenarios":
		h.SetTitle("rogue")
		h.SetSubtitle("scenarios")

	default:
		h.SetTitle("rogue")
		h.SetSubtitle("")
	}
}
