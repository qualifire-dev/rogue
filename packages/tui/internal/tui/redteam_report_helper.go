package tui

import (
	"encoding/json"

	"github.com/rogue/tui/internal/screens/redteam_report"
)

// convertToReportData converts interface{} report data to *redteam_report.ReportData
func (m *Model) convertToReportData(data interface{}) *redteam_report.ReportData {
	if data == nil {
		return nil
	}

	// Convert to JSON bytes first, then unmarshal to proper struct
	// This handles both map[string]interface{} and already-structured data
	jsonBytes, err := json.Marshal(data)
	if err != nil {
		return nil
	}

	var reportData redteam_report.ReportData
	if err := json.Unmarshal(jsonBytes, &reportData); err != nil {
		return nil
	}

	return &reportData
}
