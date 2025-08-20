package tui

import (
	"github.com/charmbracelet/lipgloss/v2"
	"github.com/rogue/tui/internal/styles"
	"github.com/rogue/tui/internal/theme"
)

func (m Model) RenderLayout(t theme.Theme, screen string) string {
	var mainLayout string
	mainStyle := styles.NewStyle().Background(t.Background())

	mainLayout = styles.NewStyle().
		Background(t.Background()).
		Padding(0, 2).
		Render(screen)

	footer := styles.NewStyle().
		Background(t.Background()).
		Width(m.width).
		Background(t.BackgroundElement()).
		Foreground(t.Accent()).
		Render(" rogue " + m.version)

	mainLayout = lipgloss.JoinVertical(
		lipgloss.Top,
		mainLayout,
		footer,
	)

	mainLayout = lipgloss.Place(
		m.width,
		m.height,
		lipgloss.Left,
		lipgloss.Top,
		mainLayout,
		styles.WhitespaceStyle(t.Background()),
	)

	mainLayout = mainStyle.Render(mainLayout)

	return mainLayout
}
