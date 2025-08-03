package util

import (
	"fmt"
	"strings"
	"time"
	"unicode/utf8"
)

// TruncateString truncates a string to the specified length with ellipsis
func TruncateString(s string, maxLen int) string {
	if utf8.RuneCountInString(s) <= maxLen {
		return s
	}

	if maxLen <= 3 {
		return strings.Repeat(".", maxLen)
	}

	runes := []rune(s)
	return string(runes[:maxLen-3]) + "..."
}

// PadString pads a string to the specified width
func PadString(s string, width int, padChar rune) string {
	strLen := utf8.RuneCountInString(s)
	if strLen >= width {
		return s
	}

	padding := strings.Repeat(string(padChar), width-strLen)
	return s + padding
}

// CenterString centers a string within the specified width
func CenterString(s string, width int) string {
	strLen := utf8.RuneCountInString(s)
	if strLen >= width {
		return s
	}

	leftPad := (width - strLen) / 2
	rightPad := width - strLen - leftPad

	return strings.Repeat(" ", leftPad) + s + strings.Repeat(" ", rightPad)
}

// FormatDuration formats a duration in a human-readable way
func FormatDuration(d time.Duration) string {
	if d < time.Minute {
		return fmt.Sprintf("%.0fs", d.Seconds())
	}
	if d < time.Hour {
		return fmt.Sprintf("%.0fm", d.Minutes())
	}
	if d < 24*time.Hour {
		return fmt.Sprintf("%.1fh", d.Hours())
	}
	return fmt.Sprintf("%.1fd", d.Hours()/24)
}

// FormatTimeAgo formats a time as "time ago" (e.g., "2 minutes ago")
func FormatTimeAgo(t time.Time) string {
	now := time.Now()
	diff := now.Sub(t)

	if diff < time.Minute {
		return "just now"
	}
	if diff < time.Hour {
		minutes := int(diff.Minutes())
		if minutes == 1 {
			return "1 minute ago"
		}
		return fmt.Sprintf("%d minutes ago", minutes)
	}
	if diff < 24*time.Hour {
		hours := int(diff.Hours())
		if hours == 1 {
			return "1 hour ago"
		}
		return fmt.Sprintf("%d hours ago", hours)
	}
	if diff < 7*24*time.Hour {
		days := int(diff.Hours() / 24)
		if days == 1 {
			return "1 day ago"
		}
		return fmt.Sprintf("%d days ago", days)
	}
	if diff < 30*24*time.Hour {
		weeks := int(diff.Hours() / (24 * 7))
		if weeks == 1 {
			return "1 week ago"
		}
		return fmt.Sprintf("%d weeks ago", weeks)
	}

	return t.Format("Jan 2, 2006")
}

// FormatProgress formats a progress value (0.0-1.0) as a percentage
func FormatProgress(progress float64) string {
	if progress < 0 {
		progress = 0
	}
	if progress > 1 {
		progress = 1
	}
	return fmt.Sprintf("%.0f%%", progress*100)
}

// FormatSize formats a byte size in human-readable format
func FormatSize(bytes int64) string {
	const unit = 1024
	if bytes < unit {
		return fmt.Sprintf("%d B", bytes)
	}

	div, exp := int64(unit), 0
	for n := bytes / unit; n >= unit; n /= unit {
		div *= unit
		exp++
	}

	units := []string{"KB", "MB", "GB", "TB", "PB"}
	return fmt.Sprintf("%.1f %s", float64(bytes)/float64(div), units[exp])
}

// WrapText wraps text to the specified width
func WrapText(text string, width int) []string {
	if width <= 0 {
		return []string{text}
	}

	words := strings.Fields(text)
	if len(words) == 0 {
		return []string{}
	}

	var lines []string
	var currentLine strings.Builder

	for _, word := range words {
		// If adding this word would exceed the width, start a new line
		if currentLine.Len() > 0 && currentLine.Len()+1+len(word) > width {
			lines = append(lines, currentLine.String())
			currentLine.Reset()
		}

		// Add word to current line
		if currentLine.Len() > 0 {
			currentLine.WriteString(" ")
		}
		currentLine.WriteString(word)
	}

	// Add the last line if it has content
	if currentLine.Len() > 0 {
		lines = append(lines, currentLine.String())
	}

	return lines
}

// JoinWithCommaAnd joins a slice of strings with commas and "and"
func JoinWithCommaAnd(items []string) string {
	switch len(items) {
	case 0:
		return ""
	case 1:
		return items[0]
	case 2:
		return items[0] + " and " + items[1]
	default:
		return strings.Join(items[:len(items)-1], ", ") + ", and " + items[len(items)-1]
	}
}

// PluralizeWord adds an "s" to a word if count is not 1
func PluralizeWord(word string, count int) string {
	if count == 1 {
		return word
	}

	// Simple pluralization rules
	if strings.HasSuffix(word, "y") && len(word) > 1 {
		// Check if the letter before 'y' is a consonant
		beforeY := word[len(word)-2]
		if !isVowel(beforeY) {
			return word[:len(word)-1] + "ies"
		}
	}

	if strings.HasSuffix(word, "s") || strings.HasSuffix(word, "sh") ||
		strings.HasSuffix(word, "ch") || strings.HasSuffix(word, "x") ||
		strings.HasSuffix(word, "z") {
		return word + "es"
	}

	return word + "s"
}

// isVowel checks if a character is a vowel
func isVowel(c byte) bool {
	vowels := "aeiouAEIOU"
	return strings.ContainsRune(vowels, rune(c))
}

// FormatList formats a list of items with bullets
func FormatList(items []string, bullet string) string {
	if bullet == "" {
		bullet = "•"
	}

	var formatted strings.Builder
	for _, item := range items {
		formatted.WriteString(bullet + " " + item + "\n")
	}

	return strings.TrimRight(formatted.String(), "\n")
}

// FormatTable formats data as a simple table
func FormatTable(headers []string, rows [][]string, padding int) string {
	if len(headers) == 0 || len(rows) == 0 {
		return ""
	}

	// Calculate column widths
	colWidths := make([]int, len(headers))
	for i, header := range headers {
		colWidths[i] = utf8.RuneCountInString(header)
	}

	for _, row := range rows {
		for i, cell := range row {
			if i < len(colWidths) {
				cellLen := utf8.RuneCountInString(cell)
				if cellLen > colWidths[i] {
					colWidths[i] = cellLen
				}
			}
		}
	}

	// Add padding
	for i := range colWidths {
		colWidths[i] += padding
	}

	var table strings.Builder

	// Format headers
	for i, header := range headers {
		table.WriteString(PadString(header, colWidths[i], ' '))
	}
	table.WriteString("\n")

	// Format separator
	for _, width := range colWidths {
		table.WriteString(strings.Repeat("-", width))
	}
	table.WriteString("\n")

	// Format rows
	for _, row := range rows {
		for i, cell := range row {
			if i < len(colWidths) {
				table.WriteString(PadString(cell, colWidths[i], ' '))
			}
		}
		table.WriteString("\n")
	}

	return table.String()
}

// RemoveANSI removes ANSI escape sequences from a string
func RemoveANSI(s string) string {
	// Simple ANSI escape sequence removal
	// This is a basic implementation - for production, consider using a proper library
	inEscape := false
	var result strings.Builder

	for _, r := range s {
		if r == '\x1b' { // ESC character
			inEscape = true
			continue
		}

		if inEscape {
			if r == 'm' || r == 'K' || r == 'J' { // End of escape sequence
				inEscape = false
			}
			continue
		}

		result.WriteRune(r)
	}

	return result.String()
}
