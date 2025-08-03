package styles

import (
	"github.com/charmbracelet/lipgloss"
)

// Color palette for the TUI
type ColorPalette struct {
	// Primary colors
	Primary   lipgloss.Color
	Secondary lipgloss.Color
	Accent    lipgloss.Color

	// State colors
	Success lipgloss.Color
	Warning lipgloss.Color
	Error   lipgloss.Color
	Info    lipgloss.Color

	// Text colors
	TextPrimary   lipgloss.Color
	TextSecondary lipgloss.Color
	TextMuted     lipgloss.Color
	TextInverse   lipgloss.Color

	// Background colors
	Background lipgloss.Color
	Surface    lipgloss.Color
	Border     lipgloss.Color

	// Special colors
	Highlight lipgloss.Color
	Selection lipgloss.Color
	Disabled  lipgloss.Color
}

// DarkPalette returns the dark theme color palette
func DarkPalette() ColorPalette {
	return ColorPalette{
		// Primary colors
		Primary:   lipgloss.Color("#7C3AED"), // Purple
		Secondary: lipgloss.Color("#3B82F6"), // Blue
		Accent:    lipgloss.Color("#10B981"), // Green

		// State colors
		Success: lipgloss.Color("#10B981"), // Green
		Warning: lipgloss.Color("#F59E0B"), // Amber
		Error:   lipgloss.Color("#EF4444"), // Red
		Info:    lipgloss.Color("#3B82F6"), // Blue

		// Text colors
		TextPrimary:   lipgloss.Color("#F9FAFB"), // Almost white
		TextSecondary: lipgloss.Color("#D1D5DB"), // Light gray
		TextMuted:     lipgloss.Color("#9CA3AF"), // Gray
		TextInverse:   lipgloss.Color("#111827"), // Dark gray

		// Background colors
		Background: lipgloss.Color("#111827"), // Dark gray
		Surface:    lipgloss.Color("#1F2937"), // Slightly lighter gray
		Border:     lipgloss.Color("#374151"), // Medium gray

		// Special colors
		Highlight: lipgloss.Color("#7C3AED"), // Purple
		Selection: lipgloss.Color("#3B82F6"), // Blue
		Disabled:  lipgloss.Color("#6B7280"), // Muted gray
	}
}

// LightPalette returns the light theme color palette
func LightPalette() ColorPalette {
	return ColorPalette{
		// Primary colors
		Primary:   lipgloss.Color("#7C3AED"), // Purple
		Secondary: lipgloss.Color("#3B82F6"), // Blue
		Accent:    lipgloss.Color("#10B981"), // Green

		// State colors
		Success: lipgloss.Color("#10B981"), // Green
		Warning: lipgloss.Color("#F59E0B"), // Amber
		Error:   lipgloss.Color("#EF4444"), // Red
		Info:    lipgloss.Color("#3B82F6"), // Blue

		// Text colors
		TextPrimary:   lipgloss.Color("#111827"), // Dark gray
		TextSecondary: lipgloss.Color("#374151"), // Medium gray
		TextMuted:     lipgloss.Color("#6B7280"), // Gray
		TextInverse:   lipgloss.Color("#F9FAFB"), // Almost white

		// Background colors
		Background: lipgloss.Color("#F9FAFB"), // Almost white
		Surface:    lipgloss.Color("#FFFFFF"), // White
		Border:     lipgloss.Color("#E5E7EB"), // Light gray

		// Special colors
		Highlight: lipgloss.Color("#7C3AED"), // Purple
		Selection: lipgloss.Color("#3B82F6"), // Blue
		Disabled:  lipgloss.Color("#9CA3AF"), // Muted gray
	}
}

// StatusColors returns colors for different evaluation statuses
func StatusColors() map[string]lipgloss.Color {
	return map[string]lipgloss.Color{
		"pending":   lipgloss.Color("#F59E0B"), // Amber
		"running":   lipgloss.Color("#3B82F6"), // Blue
		"completed": lipgloss.Color("#10B981"), // Green
		"failed":    lipgloss.Color("#EF4444"), // Red
		"cancelled": lipgloss.Color("#6B7280"), // Gray
		"paused":    lipgloss.Color("#F59E0B"), // Amber
		"queued":    lipgloss.Color("#9CA3AF"), // Muted gray
	}
}

// StatusIcons returns emoji icons for different evaluation statuses
func StatusIcons() map[string]string {
	return map[string]string{
		"pending":   "⏳",
		"running":   "🔄",
		"completed": "✅",
		"failed":    "❌",
		"cancelled": "🚫",
		"paused":    "⏸️",
		"queued":    "⏳",
	}
}

// RoleIcons returns emoji icons for different chat roles
func RoleIcons() map[string]string {
	return map[string]string{
		"user":      "👤",
		"agent":     "🤖",
		"evaluator": "🎯",
		"system":    "⚙️",
	}
}

// PriorityColors returns colors for different priority levels
func PriorityColors() map[string]lipgloss.Color {
	return map[string]lipgloss.Color{
		"low":      lipgloss.Color("#10B981"), // Green
		"medium":   lipgloss.Color("#F59E0B"), // Amber
		"high":     lipgloss.Color("#EF4444"), // Red
		"critical": lipgloss.Color("#DC2626"), // Dark red
	}
}

// CategoryColors returns colors for different scenario categories
func CategoryColors() map[string]lipgloss.Color {
	return map[string]lipgloss.Color{
		"security":    lipgloss.Color("#EF4444"), // Red
		"compliance":  lipgloss.Color("#3B82F6"), // Blue
		"performance": lipgloss.Color("#10B981"), // Green
		"safety":      lipgloss.Color("#F59E0B"), // Amber
		"custom":      lipgloss.Color("#7C3AED"), // Purple
		"general":     lipgloss.Color("#6B7280"), // Gray
	}
}
