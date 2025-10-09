package components

import "strings"

// wrapText wraps text to the specified width
func wrapText(text string, width int) string {
	if width <= 0 {
		return text
	}

	words := strings.Fields(text)
	if len(words) == 0 {
		return text
	}

	var lines []string
	var currentLine strings.Builder

	for _, word := range words {
		if currentLine.Len() == 0 {
			currentLine.WriteString(word)
		} else if currentLine.Len()+1+len(word) <= width {
			currentLine.WriteString(" ")
			currentLine.WriteString(word)
		} else {
			lines = append(lines, currentLine.String())
			currentLine.Reset()
			currentLine.WriteString(word)
		}
	}

	if currentLine.Len() > 0 {
		lines = append(lines, currentLine.String())
	}

	return strings.Join(lines, "\n")
}

// wrapTextWithStarts wraps text to the given width and returns lines and rune index starts for each line
func wrapTextWithStarts(text string, width int) ([]string, []int) {
	if width <= 0 {
		if text == "" {
			return []string{""}, []int{0}
		}
		return []string{text}, []int{0}
	}

	runes := []rune(text)
	if len(runes) == 0 {
		return []string{""}, []int{0}
	}

	var (
		lines  []string
		starts []int
		start  int
		col    int
	)

	for i, r := range runes {
		if r == '\n' {
			lines = append(lines, string(runes[start:i]))
			starts = append(starts, start)
			start = i + 1
			col = 0
			continue
		}

		col++
		if col == width {
			lines = append(lines, string(runes[start:i+1]))
			starts = append(starts, start)
			start = i + 1
			col = 0
		}
	}

	lines = append(lines, string(runes[start:]))
	starts = append(starts, start)

	return lines, starts
}

func rowColForIndex(lineStarts []int, text string, width int, index int) (int, int) {
	runes := []rune(text)
	if index < 0 {
		index = 0
	}
	if index > len(runes) {
		index = len(runes)
	}
	// Find the line where index falls
	row := 0
	for i := 0; i < len(lineStarts); i++ {
		if index >= lineStarts[i] {
			row = i
		} else {
			break
		}
	}
	col := index - lineStarts[row]
	// Clamp col to wrapped width
	if col > width {
		col = width
	}
	return row, col
}

func indexForRowCol(lineStarts []int, text string, width int, row, col int) int {
	if row < 0 {
		row = 0
	}
	if row >= len(lineStarts) {
		row = len(lineStarts) - 1
	}
	lineStart := lineStarts[row]
	lineLen := 0
	runes := []rune(text)
	// Determine line length by next start or end
	if row+1 < len(lineStarts) {
		lineLen = lineStarts[row+1] - lineStart
	} else {
		lineLen = len(runes) - lineStart
	}
	if col > lineLen {
		col = lineLen
	}
	if col < 0 {
		col = 0
	}
	return lineStart + col
}

func insertAtRune(s string, idx int, insert string) string {
	r := []rune(s)
	if idx < 0 {
		idx = 0
	}
	if idx > len(r) {
		idx = len(r)
	}
	out := make([]rune, 0, len(r)+len([]rune(insert)))
	out = append(out, r[:idx]...)
	out = append(out, []rune(insert)...)
	out = append(out, r[idx:]...)
	return string(out)
}

func ellipsis(s string, max int) string {
    if max <= 0 {
        return ""
    }
    runes := []rune(s)
    if len(runes) <= max {
        return s
    }
    if max <= 3 {
        return string(runes[:max])
    }
    return string(runes[:max-3]) + "..."
}
