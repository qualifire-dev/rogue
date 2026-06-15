package resilience

import (
	"fmt"
	"strings"

	"github.com/charmbracelet/lipgloss"
)

var (
	titleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(lipgloss.Color("#A78BFA")).
			MarginBottom(1)

	itemStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#D8DEE9"))

	premiumStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#EBCB8B"))

	helpStyle = lipgloss.NewStyle().
			Foreground(lipgloss.Color("#616E88")).
			MarginTop(1)
)

// RenderCatalog renders the resilience injector and architecture reference screen.
func RenderCatalog(width, height int) string {
	var b strings.Builder
	b.WriteString(titleStyle.Render("⚡ Resilience — Chaos Experiment Reference"))
	b.WriteString("\n\n")
	b.WriteString(itemStyle.Render("Fault injectors (use in web UI or API):"))
	b.WriteString("\n")
	for _, inj := range BuiltInInjectors {
		line := fmt.Sprintf("  • %s — %s", inj.Name, inj.ID)
		if inj.Premium {
			line += " ★ premium"
			b.WriteString(premiumStyle.Render(line))
		} else {
			b.WriteString(itemStyle.Render(line))
		}
		b.WriteString("\n")
	}
	b.WriteString("\n")
	b.WriteString(itemStyle.Render("Architecture profiles:"))
	b.WriteString("\n")
	for _, arch := range Architectures {
		b.WriteString(itemStyle.Render(fmt.Sprintf("  • %s (%s)", arch.Name, arch.ID)))
		b.WriteString("\n")
	}
	b.WriteString("\n")
	b.WriteString(helpStyle.Render(
		"Run experiments via web: http://localhost:8000/resilience/configure\n" +
			"CLI: rogue-ai cli --evaluation-mode resilience --protocol python ...\n" +
			"Press Esc or q to return.",
	))
	return b.String()
}
