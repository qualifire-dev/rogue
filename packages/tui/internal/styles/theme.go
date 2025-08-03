package styles

import (
	"os"
	"strings"
)

// Theme represents a UI theme
type Theme struct {
	Name   string
	Colors ColorPalette
	IsDark bool
}

// ThemeManager manages themes for the TUI
type ThemeManager struct {
	current *Theme
	themes  map[string]*Theme
}

// NewThemeManager creates a new theme manager
func NewThemeManager() *ThemeManager {
	tm := &ThemeManager{
		themes: make(map[string]*Theme),
	}

	// Register built-in themes
	tm.registerBuiltinThemes()

	// Set default theme
	tm.current = tm.themes["dark"]

	return tm
}

// registerBuiltinThemes registers the built-in themes
func (tm *ThemeManager) registerBuiltinThemes() {
	// Dark theme
	tm.themes["dark"] = &Theme{
		Name:   "dark",
		Colors: DarkPalette(),
		IsDark: true,
	}

	// Light theme
	tm.themes["light"] = &Theme{
		Name:   "light",
		Colors: LightPalette(),
		IsDark: false,
	}
}

// SetTheme sets the current theme by name
func (tm *ThemeManager) SetTheme(name string) bool {
	if name == "auto" {
		tm.setAutoTheme()
		return true
	}

	if theme, exists := tm.themes[name]; exists {
		tm.current = theme
		return true
	}

	return false
}

// GetTheme returns the current theme
func (tm *ThemeManager) GetTheme() *Theme {
	return tm.current
}

// GetColors returns the current color palette
func (tm *ThemeManager) GetColors() ColorPalette {
	return tm.current.Colors
}

// GetAvailableThemes returns the names of all available themes
func (tm *ThemeManager) GetAvailableThemes() []string {
	themes := make([]string, 0, len(tm.themes)+1)
	themes = append(themes, "auto") // Add auto option

	for name := range tm.themes {
		themes = append(themes, name)
	}

	return themes
}

// setAutoTheme automatically selects a theme based on system preferences
func (tm *ThemeManager) setAutoTheme() {
	// Check if we can detect dark mode preference
	if isDarkMode := tm.detectDarkMode(); isDarkMode {
		tm.current = tm.themes["dark"]
	} else {
		tm.current = tm.themes["light"]
	}
}

// detectDarkMode attempts to detect if the system is in dark mode
func (tm *ThemeManager) detectDarkMode() bool {
	// Check environment variables that might indicate dark mode
	if term := os.Getenv("TERM"); term != "" {
		// Some terminals set specific TERM values for dark themes
		if strings.Contains(strings.ToLower(term), "dark") {
			return true
		}
	}

	// Check COLORFGBG environment variable (used by some terminals)
	if colorfgbg := os.Getenv("COLORFGBG"); colorfgbg != "" {
		// Format is usually "foreground;background"
		// Dark themes typically have light foreground on dark background
		parts := strings.Split(colorfgbg, ";")
		if len(parts) >= 2 {
			// If background color is low (dark), assume dark mode
			bg := parts[len(parts)-1]
			if bg == "0" || bg == "8" {
				return true
			}
		}
	}

	// Default to dark mode if we can't determine
	return true
}

// IsDark returns true if the current theme is dark
func (tm *ThemeManager) IsDark() bool {
	return tm.current.IsDark
}

// IsLight returns true if the current theme is light
func (tm *ThemeManager) IsLight() bool {
	return !tm.current.IsDark
}

// RegisterTheme registers a custom theme
func (tm *ThemeManager) RegisterTheme(theme *Theme) {
	tm.themes[theme.Name] = theme
}

// UnregisterTheme removes a theme (cannot remove built-in themes)
func (tm *ThemeManager) UnregisterTheme(name string) bool {
	if name == "dark" || name == "light" {
		return false // Cannot remove built-in themes
	}

	if _, exists := tm.themes[name]; exists {
		delete(tm.themes, name)

		// If we're removing the current theme, switch to dark
		if tm.current.Name == name {
			tm.current = tm.themes["dark"]
		}

		return true
	}

	return false
}
