package util

import (
	"time"
)

// ParseDuration parses a duration string with extended support
func ParseDuration(s string) (time.Duration, error) {
	// Try standard Go duration parsing first
	if d, err := time.ParseDuration(s); err == nil {
		return d, nil
	}

	// TODO: Add custom duration parsing if needed
	// For now, just use standard parsing
	return time.ParseDuration(s)
}

// FormatDateTime formats a time in a consistent way for the TUI
func FormatDateTime(t time.Time) string {
	return t.Format("2006-01-02 15:04:05")
}

// FormatDate formats a date in a consistent way for the TUI
func FormatDate(t time.Time) string {
	return t.Format("2006-01-02")
}

// FormatTime formats a time in a consistent way for the TUI
func FormatTime(t time.Time) string {
	return t.Format("15:04:05")
}

// IsToday checks if a time is today
func IsToday(t time.Time) bool {
	now := time.Now()
	return t.Year() == now.Year() && t.Month() == now.Month() && t.Day() == now.Day()
}

// IsYesterday checks if a time is yesterday
func IsYesterday(t time.Time) bool {
	yesterday := time.Now().AddDate(0, 0, -1)
	return t.Year() == yesterday.Year() && t.Month() == yesterday.Month() && t.Day() == yesterday.Day()
}

// IsTomorrow checks if a time is tomorrow
func IsTomorrow(t time.Time) bool {
	tomorrow := time.Now().AddDate(0, 0, 1)
	return t.Year() == tomorrow.Year() && t.Month() == tomorrow.Month() && t.Day() == tomorrow.Day()
}

// StartOfDay returns the start of the day for the given time
func StartOfDay(t time.Time) time.Time {
	return time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, t.Location())
}

// EndOfDay returns the end of the day for the given time
func EndOfDay(t time.Time) time.Time {
	return time.Date(t.Year(), t.Month(), t.Day(), 23, 59, 59, 999999999, t.Location())
}

// GetHumanReadableTime returns a human-readable time representation
func GetHumanReadableTime(t time.Time) string {
	if IsToday(t) {
		return "Today " + t.Format("15:04")
	}
	if IsYesterday(t) {
		return "Yesterday " + t.Format("15:04")
	}
	if IsTomorrow(t) {
		return "Tomorrow " + t.Format("15:04")
	}

	// If it's within the last week
	now := time.Now()
	if now.Sub(t) <= 7*24*time.Hour && now.Sub(t) >= 0 {
		return t.Format("Monday 15:04")
	}

	// If it's within the current year
	if t.Year() == now.Year() {
		return t.Format("Jan 2 15:04")
	}

	// For older dates
	return t.Format("Jan 2, 2006")
}

// Sleep returns a Bubble Tea command that sleeps for the given duration
func Sleep(d time.Duration) func() time.Time {
	return func() time.Time {
		time.Sleep(d)
		return time.Now()
	}
}
