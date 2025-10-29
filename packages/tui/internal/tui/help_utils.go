package tui

import (
	"log"
	"strings"

	"github.com/rogue/tui/internal/screens/help"
	"github.com/rogue/tui/internal/shared"
	"github.com/rogue/tui/internal/theme"
)

// initializeHelpViewport sets up the help viewport with content on first access
func (m *Model) initializeHelpViewport() {
	// Only initialize if content is empty
	if m.helpViewport.GetContent() != "" {
		log.Printf("[TUI] Help viewport already initialized, resetting to top")
		m.helpViewport.GotoTop()
		return
	}

	log.Printf("[TUI] Initializing help viewport content")

	// Calculate viewport dimensions
	viewportWidth := m.width - 11
	viewportHeight := m.height - 9
	contentWidth := viewportWidth - 6
	actualViewportHeight := viewportHeight - 4 // Account for padding and border

	// Load and render help content
	t := theme.CurrentTheme()
	renderer := shared.GetMarkdownRenderer(contentWidth, t.Background())

	// Get help content from the help package
	helpContent := help.GetHelpContent()
	contentStr := strings.ReplaceAll(helpContent, "\r\n", "\n")
	renderedContent, err := renderer.Render(contentStr)
	if err != nil {
		log.Printf("[TUI] Error rendering help markdown: %v", err)
		renderedContent = helpContent
	}

	// Set up viewport
	m.helpViewport.SetSize(contentWidth, actualViewportHeight)
	m.helpViewport.SetContent(renderedContent)
	m.helpViewport.GotoTop()

	log.Printf("[TUI] Help viewport initialized: %dx%d, content lines: %d",
		contentWidth, actualViewportHeight, len(strings.Split(renderedContent, "\n")))
}
