// Package redteam provides the red team configuration screen for the TUI.
package redteam

import tea "github.com/charmbracelet/bubbletea/v2"

// OpenAPIKeyDialogMsg is sent to request opening the API key dialog
type OpenAPIKeyDialogMsg struct {
	CurrentKey string
}

// APIKeySetMsg is sent when the API key has been set
type APIKeySetMsg struct {
	APIKey string
}

// OpenAPIKeyDialogCmd returns a command to open the API key dialog
func OpenAPIKeyDialogCmd(currentKey string) tea.Cmd {
	return func() tea.Msg {
		return OpenAPIKeyDialogMsg{CurrentKey: currentKey}
	}
}

// ScanType represents the type of red team scan.
type ScanType string

const (
	ScanTypeBasic  ScanType = "basic"
	ScanTypeFull   ScanType = "full"
	ScanTypeCustom ScanType = "custom"
)

// VulnerabilityCategory represents a category of vulnerabilities.
type VulnerabilityCategory string

const (
	CategoryContentSafety      VulnerabilityCategory = "Content Safety"
	CategoryPIIProtection      VulnerabilityCategory = "PII Protection"
	CategoryTechnical          VulnerabilityCategory = "Technical"
	CategoryBiasFairness       VulnerabilityCategory = "Bias & Fairness"
	CategoryPromptSecurity     VulnerabilityCategory = "Prompt Security"
	CategoryAccessControl      VulnerabilityCategory = "Access Control"
	CategoryBusinessLogic      VulnerabilityCategory = "Business Logic"
	CategoryIP                 VulnerabilityCategory = "Intellectual Property"
	CategoryInfoQuality        VulnerabilityCategory = "Information Quality"
	CategoryCompliance         VulnerabilityCategory = "Compliance"
	CategorySpecializedThreats VulnerabilityCategory = "Specialized Threats"
	CategoryAgentSpecific      VulnerabilityCategory = "Agent-Specific"
	CategoryResourceAttacks    VulnerabilityCategory = "Resource Attacks"
)

// AttackCategory represents a category of attacks.
type AttackCategory string

const (
	AttackCategorySingleTurn AttackCategory = "Single-Turn"
	AttackCategoryMultiTurn  AttackCategory = "Multi-Turn"
	AttackCategoryAgentic    AttackCategory = "Agentic"
)

// Vulnerability represents a vulnerability definition.
type Vulnerability struct {
	ID             string
	Name           string
	Category       VulnerabilityCategory
	Description    string
	DefaultAttacks []string
	Premium        bool
}

// Attack represents an attack technique definition.
type Attack struct {
	ID          string
	Name        string
	Category    AttackCategory
	Description string
	Premium     bool
}

// Framework represents a compliance framework definition.
type Framework struct {
	ID              string
	Name            string
	Description     string
	Vulnerabilities []string
}

// RedTeamConfigState holds the state for the red team configuration screen.
type RedTeamConfigState struct {
	// UI state
	ActivePanel      int             // 0 = vulnerabilities, 1 = attacks
	FocusedCategory  int             // Index of focused category in active panel
	FocusedItem      int             // Index of focused item within category
	CategoryExpanded map[string]bool // Whether category is expanded
	ScrollOffset     int             // Scroll offset for list

	// Selection state
	SelectedVulnerabilities map[string]bool
	SelectedAttacks         map[string]bool
	SelectedFrameworks      map[string]bool

	// Configuration
	ScanType                ScanType
	AttacksPerVulnerability int
	QualifireAPIKey         string

	// Dialogs
	ShowFrameworkDialog bool
	ShowAPIKeyDialog    bool
	APIKeyInput         string
}

// NewRedTeamConfigState creates a new RedTeamConfigState with default values.
func NewRedTeamConfigState() *RedTeamConfigState {
	state := &RedTeamConfigState{
		ActivePanel:             0,
		FocusedCategory:         0,
		FocusedItem:             -1, // -1 means category header is focused
		CategoryExpanded:        make(map[string]bool),
		SelectedVulnerabilities: make(map[string]bool),
		SelectedAttacks:         make(map[string]bool),
		SelectedFrameworks:      make(map[string]bool),
		ScanType:                ScanTypeBasic,
		AttacksPerVulnerability: 3,
	}

	// Try to load saved configuration from .rogue/redteam.yaml
	if err := LoadRedTeamConfig(state); err != nil {
		// If loading fails, just use defaults (already set above)
		// We don't want to fail initialization if the config file has issues
	}

	return state
}

// GetSelectedVulnerabilityCount returns the number of selected vulnerabilities.
func (s *RedTeamConfigState) GetSelectedVulnerabilityCount() int {
	count := 0
	for _, selected := range s.SelectedVulnerabilities {
		if selected {
			count++
		}
	}
	return count
}

// GetSelectedAttackCount returns the number of selected attacks.
func (s *RedTeamConfigState) GetSelectedAttackCount() int {
	count := 0
	for _, selected := range s.SelectedAttacks {
		if selected {
			count++
		}
	}
	return count
}

// GetSelectedFrameworkCount returns the number of selected frameworks.
func (s *RedTeamConfigState) GetSelectedFrameworkCount() int {
	count := 0
	for _, selected := range s.SelectedFrameworks {
		if selected {
			count++
		}
	}
	return count
}

// HasPremiumSelections checks if any premium items are selected.
func (s *RedTeamConfigState) HasPremiumSelections() bool {
	for vulnID, selected := range s.SelectedVulnerabilities {
		if selected {
			vuln := GetVulnerability(vulnID)
			if vuln != nil && vuln.Premium {
				return true
			}
		}
	}
	for attackID, selected := range s.SelectedAttacks {
		if selected {
			attack := GetAttack(attackID)
			if attack != nil && attack.Premium {
				return true
			}
		}
	}
	return false
}

// ToAPIConfig converts the state to the API configuration format.
func (s *RedTeamConfigState) ToAPIConfig() map[string]interface{} {
	vulnerabilities := make([]string, 0)
	for id, selected := range s.SelectedVulnerabilities {
		if selected {
			vulnerabilities = append(vulnerabilities, id)
		}
	}

	attacks := make([]string, 0)
	for id, selected := range s.SelectedAttacks {
		if selected {
			attacks = append(attacks, id)
		}
	}

	frameworks := make([]string, 0)
	for id, selected := range s.SelectedFrameworks {
		if selected {
			frameworks = append(frameworks, id)
		}
	}

	return map[string]interface{}{
		"scan_type":                 string(s.ScanType),
		"vulnerabilities":           vulnerabilities,
		"attacks":                   attacks,
		"attacks_per_vulnerability": s.AttacksPerVulnerability,
		"frameworks":                frameworks,
	}
}
