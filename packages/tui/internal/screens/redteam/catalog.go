// Package redteam provides vulnerability, attack, and framework catalogs.
package redteam

// VulnerabilityCatalog contains all vulnerability definitions.
var VulnerabilityCatalog = map[string]*Vulnerability{
	// Content Safety (Premium)
	"hate-speech":      {ID: "hate-speech", Name: "Hate Speech", Category: CategoryContentSafety, Description: "Tests handling of hate speech content", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"explicit-content": {ID: "explicit-content", Name: "Explicit Content", Category: CategoryContentSafety, Description: "Tests handling of explicit content", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"violent-crime":    {ID: "violent-crime", Name: "Violent Crime Content", Category: CategoryContentSafety, Description: "Tests handling of violent crime content", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"harassment":       {ID: "harassment", Name: "Harassment", Category: CategoryContentSafety, Description: "Tests handling of harassment content", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"self-harm":        {ID: "self-harm", Name: "Self-Harm", Category: CategoryContentSafety, Description: "Tests handling of self-harm content", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"profanity":        {ID: "profanity", Name: "Profanity", Category: CategoryContentSafety, Description: "Tests handling of profane language", DefaultAttacks: []string{"prompt-injection", "leetspeak"}, Premium: true},

	// PII Protection
	"pii-direct":            {ID: "pii-direct", Name: "PII via Direct Exposure", Category: CategoryPIIProtection, Description: "Tests for direct PII exposure", DefaultAttacks: []string{"prompt-injection", "prompt-probing"}, Premium: false},
	"pii-api-db":            {ID: "pii-api-db", Name: "PII via API/Database", Category: CategoryPIIProtection, Description: "Tests for PII exposure via API/database", DefaultAttacks: []string{"prompt-injection", "gray-box"}, Premium: false},
	"pii-session":           {ID: "pii-session", Name: "PII via Session Data", Category: CategoryPIIProtection, Description: "Tests for PII exposure in session data", DefaultAttacks: []string{"prompt-injection", "context-poisoning"}, Premium: false},
	"pii-social":            {ID: "pii-social", Name: "PII via Social Engineering", Category: CategoryPIIProtection, Description: "Tests for PII exposure via social engineering", DefaultAttacks: []string{"roleplay", "goal-redirection"}, Premium: true},
	"cross-session-leakage": {ID: "cross-session-leakage", Name: "Cross-Session Data Leakage", Category: CategoryPIIProtection, Description: "Tests for data leakage between sessions", DefaultAttacks: []string{"prompt-injection", "context-poisoning"}, Premium: false},

	// Technical (Premium)
	"sql-injection":   {ID: "sql-injection", Name: "SQL Injection", Category: CategoryTechnical, Description: "Tests for SQL injection vulnerabilities", DefaultAttacks: []string{"prompt-injection", "input-bypass"}, Premium: true},
	"shell-injection": {ID: "shell-injection", Name: "Command Injection", Category: CategoryTechnical, Description: "Tests for command injection vulnerabilities", DefaultAttacks: []string{"prompt-injection", "input-bypass"}, Premium: true},
	"ssrf":            {ID: "ssrf", Name: "SSRF Vulnerability", Category: CategoryTechnical, Description: "Tests for SSRF vulnerabilities", DefaultAttacks: []string{"prompt-injection", "gray-box"}, Premium: true},
	"debug-access":    {ID: "debug-access", Name: "Debug Interface Exposure", Category: CategoryTechnical, Description: "Tests for exposed debug interfaces", DefaultAttacks: []string{"prompt-probing", "gray-box"}, Premium: true},
	"malicious-code":  {ID: "malicious-code", Name: "Malicious Code", Category: CategoryTechnical, Description: "Tests creation of malicious code", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},

	// Bias & Fairness (Premium)
	"bias-age":      {ID: "bias-age", Name: "Age Bias", Category: CategoryBiasFairness, Description: "Age-related bias detection", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"bias-gender":   {ID: "bias-gender", Name: "Gender Bias", Category: CategoryBiasFairness, Description: "Gender-related bias detection", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"bias-race":     {ID: "bias-race", Name: "Race Bias", Category: CategoryBiasFairness, Description: "Race-related bias detection", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"bias-religion": {ID: "bias-religion", Name: "Religious Bias", Category: CategoryBiasFairness, Description: "Religious bias detection", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},

	// Prompt Security
	"prompt-extraction":  {ID: "prompt-extraction", Name: "System Prompt Disclosure", Category: CategoryPromptSecurity, Description: "Tests for system prompt disclosure", DefaultAttacks: []string{"prompt-probing", "system-override", "social-engineering-prompt-extraction"}, Premium: false},
	"prompt-override":    {ID: "prompt-override", Name: "System Prompt Override", Category: CategoryPromptSecurity, Description: "Tests for system prompt override", DefaultAttacks: []string{"system-override", "prompt-injection"}, Premium: false},
	"indirect-injection": {ID: "indirect-injection", Name: "Indirect Prompt Injection", Category: CategoryPromptSecurity, Description: "Tests for indirect injection via variables", DefaultAttacks: []string{"prompt-injection", "context-poisoning"}, Premium: false},
	"ascii-smuggling":    {ID: "ascii-smuggling", Name: "ASCII Smuggling", Category: CategoryPromptSecurity, Description: "Tests for Unicode tag-based attacks", DefaultAttacks: []string{"base64", "rot13"}, Premium: false},

	// Access Control (Premium)
	"rbac":             {ID: "rbac", Name: "RBAC Implementation", Category: CategoryAccessControl, Description: "Tests RBAC implementation", DefaultAttacks: []string{"permission-escalation", "gray-box"}, Premium: true},
	"bola":             {ID: "bola", Name: "Object-Level Authorization Bypass", Category: CategoryAccessControl, Description: "Tests for BOLA vulnerabilities", DefaultAttacks: []string{"permission-escalation", "gray-box"}, Premium: true},
	"excessive-agency": {ID: "excessive-agency", Name: "Excessive Agency", Category: CategoryAccessControl, Description: "Tests for unauthorized actions", DefaultAttacks: []string{"roleplay", "goal-redirection"}, Premium: true},

	// Business Logic (Premium)
	"unauthorized-commitments": {ID: "unauthorized-commitments", Name: "Unauthorized Commitments", Category: CategoryBusinessLogic, Description: "Tests for unauthorized contractual commitments", DefaultAttacks: []string{"roleplay", "goal-redirection"}, Premium: true},
	"unauthorized-advice":      {ID: "unauthorized-advice", Name: "Unauthorized Advice", Category: CategoryBusinessLogic, Description: "Tests handling of unauthorized advice", DefaultAttacks: []string{"roleplay", "prompt-injection"}, Premium: true},
	"competitors":              {ID: "competitors", Name: "Competitors", Category: CategoryBusinessLogic, Description: "Tests for competitor mentions", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"off-topic":                {ID: "off-topic", Name: "Off-Topic Manipulation", Category: CategoryBusinessLogic, Description: "Tests for off-topic manipulation", DefaultAttacks: []string{"goal-redirection", "context-poisoning"}, Premium: true},

	// Information Quality (Premium)
	"hallucination":                 {ID: "hallucination", Name: "Hallucination", Category: CategoryInfoQuality, Description: "Tests for fabrication of false information", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"misinformation-disinformation": {ID: "misinformation-disinformation", Name: "Disinformation Campaigns", Category: CategoryInfoQuality, Description: "Tests handling of false information", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},

	// Agent-Specific (Premium)
	"memory-poisoning": {ID: "memory-poisoning", Name: "Agentic Memory Poisoning", Category: CategoryAgentSpecific, Description: "Tests for memory poisoning attacks", DefaultAttacks: []string{"context-poisoning", "prompt-injection"}, Premium: true},
	"rag-poisoning":    {ID: "rag-poisoning", Name: "RAG Poisoning", Category: CategoryAgentSpecific, Description: "Tests for RAG retrieval poisoning", DefaultAttacks: []string{"context-poisoning", "prompt-injection"}, Premium: true},
	"tool-discovery":   {ID: "tool-discovery", Name: "Tool Discovery", Category: CategoryAgentSpecific, Description: "Tests for tool enumeration", DefaultAttacks: []string{"prompt-probing", "gray-box"}, Premium: true},

	// Resource Attacks (Premium)
	"unbounded-consumption": {ID: "unbounded-consumption", Name: "Unbounded Consumption", Category: CategoryResourceAttacks, Description: "Tests for resource exhaustion", DefaultAttacks: []string{"prompt-injection", "goal-redirection"}, Premium: true},
	"reasoning-dos":         {ID: "reasoning-dos", Name: "Reasoning DoS", Category: CategoryResourceAttacks, Description: "Tests for computational exhaustion", DefaultAttacks: []string{"prompt-injection", "math-problem"}, Premium: true},
}

// AttackCatalog contains all attack technique definitions.
var AttackCatalog = map[string]*Attack{
	// Single-Turn (Free)
	"base64":                {ID: "base64", Name: "Base64 Encoding", Category: AttackCategorySingleTurn, Description: "Encodes attack in Base64", Premium: false},
	"rot13":                 {ID: "rot13", Name: "ROT13 Encoding", Category: AttackCategorySingleTurn, Description: "Encodes attack using ROT13", Premium: false},
	"leetspeak":             {ID: "leetspeak", Name: "Leetspeak", Category: AttackCategorySingleTurn, Description: "Uses leetspeak character substitutions", Premium: false},
	"prompt-injection":      {ID: "prompt-injection", Name: "Prompt Injection", Category: AttackCategorySingleTurn, Description: "Direct prompt injection", Premium: false},
	"roleplay":              {ID: "roleplay", Name: "Roleplay", Category: AttackCategorySingleTurn, Description: "Uses roleplay scenarios", Premium: false},
	"prompt-probing":        {ID: "prompt-probing", Name: "Prompt Probing", Category: AttackCategorySingleTurn, Description: "Attempts to extract system prompts", Premium: false},
	"gray-box":              {ID: "gray-box", Name: "Gray Box", Category: AttackCategorySingleTurn, Description: "Injects fake internal information", Premium: false},
	"multilingual":          {ID: "multilingual", Name: "Multilingual", Category: AttackCategorySingleTurn, Description: "Uses translation to bypass filters", Premium: false},
	"context-poisoning":     {ID: "context-poisoning", Name: "Context Poisoning", Category: AttackCategorySingleTurn, Description: "Injects malicious context", Premium: false},
	"goal-redirection":      {ID: "goal-redirection", Name: "Goal Redirection", Category: AttackCategorySingleTurn, Description: "Attempts to shift conversation goal", Premium: false},
	"input-bypass":          {ID: "input-bypass", Name: "Input Bypass", Category: AttackCategorySingleTurn, Description: "Splits payload to bypass filters", Premium: false},
	"permission-escalation": {ID: "permission-escalation", Name: "Permission Escalation", Category: AttackCategorySingleTurn, Description: "Claims elevated permissions", Premium: false},
	"system-override":       {ID: "system-override", Name: "System Override", Category: AttackCategorySingleTurn, Description: "Uses explicit override commands", Premium: false},
	"semantic-manipulation": {ID: "semantic-manipulation", Name: "Semantic Manipulation", Category: AttackCategorySingleTurn, Description: "Uses semantic tricks", Premium: false},
	"math-problem":          {ID: "math-problem", Name: "Math Prompt", Category: AttackCategorySingleTurn, Description: "Encodes in math problems", Premium: false},

	// Multi-Turn (Premium)
	"social-engineering-prompt-extraction": {ID: "social-engineering-prompt-extraction", Name: "Social Engineering Prompt Extraction", Category: AttackCategoryMultiTurn, Description: "Uses trust-building and social engineering to extract system prompts", Premium: true},

	// Single-Turn (Premium)
	"homoglyph":        {ID: "homoglyph", Name: "Homoglyph Encoding", Category: AttackCategorySingleTurn, Description: "Uses similar Unicode characters", Premium: true},
	"citation":         {ID: "citation", Name: "Citation", Category: AttackCategorySingleTurn, Description: "Frames as academic citations", Premium: true},
	"gcg":              {ID: "gcg", Name: "GCG", Category: AttackCategorySingleTurn, Description: "Gradient-based adversarial suffix", Premium: true},
	"likert-jailbreak": {ID: "likert-jailbreak", Name: "Likert-based Jailbreaks", Category: AttackCategorySingleTurn, Description: "Uses Likert scale framing", Premium: true},
	"best-of-n":        {ID: "best-of-n", Name: "Best-of-N", Category: AttackCategorySingleTurn, Description: "Generates multiple variations", Premium: true},

	// Multi-Turn (Premium)
	"goat":                 {ID: "goat", Name: "GOAT", Category: AttackCategoryMultiTurn, Description: "Generative Offensive Agent Tester", Premium: true},
	"mischievous-user":     {ID: "mischievous-user", Name: "Mischievous User", Category: AttackCategoryMultiTurn, Description: "Simulates persistent attacker", Premium: true},
	"simba":                {ID: "simba", Name: "Simba", Category: AttackCategoryMultiTurn, Description: "Simulation-based multi-turn attacks", Premium: true},
	"crescendo":            {ID: "crescendo", Name: "Crescendo", Category: AttackCategoryMultiTurn, Description: "Gradually escalating attacks", Premium: true},
	"linear-jailbreak":     {ID: "linear-jailbreak", Name: "Linear Jailbreaking", Category: AttackCategoryMultiTurn, Description: "Sequential jailbreaking", Premium: true},
	"sequential-jailbreak": {ID: "sequential-jailbreak", Name: "Sequential Jailbreak", Category: AttackCategoryMultiTurn, Description: "Combines techniques in sequence", Premium: true},

	// Agentic (Premium)
	"hydra":                {ID: "hydra", Name: "Hydra Multi-turn", Category: AttackCategoryAgentic, Description: "Multi-headed attack strategy", Premium: true},
	"tree-jailbreak":       {ID: "tree-jailbreak", Name: "Tree-based Jailbreaks", Category: AttackCategoryAgentic, Description: "Tree search-based exploration", Premium: true},
	"meta-agent-jailbreak": {ID: "meta-agent-jailbreak", Name: "Meta-Agent Jailbreaks", Category: AttackCategoryAgentic, Description: "Uses meta-agent to orchestrate", Premium: true},
	"iterative-jailbreak":  {ID: "iterative-jailbreak", Name: "Iterative Jailbreaks", Category: AttackCategoryAgentic, Description: "AI-driven iterative refinement", Premium: true},
}

// FrameworkCatalog contains all framework definitions with vulnerability mappings.
var FrameworkCatalog = map[string]*Framework{
	"owasp-llm": {
		ID:          "owasp-llm",
		Name:        "OWASP LLM Top 10",
		Description: "OWASP Top 10 for LLM Applications 2025",
		Vulnerabilities: []string{
			"prompt-extraction", "prompt-override", "indirect-injection",
			"pii-direct", "pii-api-db", "pii-session",
			"sql-injection", "shell-injection", "malicious-code",
			"excessive-agency", "rbac", "bola",
			"hallucination", "misinformation-disinformation",
			"unbounded-consumption", "reasoning-dos",
			"hate-speech", "explicit-content", "violent-crime",
			"bias-age", "bias-gender", "bias-race",
		},
	},
	"mitre-atlas": {
		ID:          "mitre-atlas",
		Name:        "MITRE ATLAS",
		Description: "MITRE Adversarial Threat Landscape for AI Systems",
		Vulnerabilities: []string{
			"ascii-smuggling", "prompt-extraction", "prompt-override",
			"pii-direct", "pii-api-db", "pii-session",
			"excessive-agency", "hallucination",
			"hate-speech", "harassment", "explicit-content",
			"sql-injection", "shell-injection", "malicious-code",
		},
	},
	"nist-ai": {
		ID:          "nist-ai",
		Name:        "NIST AI RMF",
		Description: "NIST AI Risk Management Framework",
		Vulnerabilities: []string{
			"excessive-agency", "misinformation-disinformation",
			"pii-direct", "pii-api-db", "pii-session",
			"sql-injection", "shell-injection",
			"harassment", "hate-speech",
		},
	},
	"iso-42001": {
		ID:          "iso-42001",
		Name:        "ISO/IEC 42001",
		Description: "ISO/IEC 42001 AI Management System",
		Vulnerabilities: []string{
			"excessive-agency",
			"bias-age", "bias-gender", "bias-race", "bias-religion",
			"hate-speech",
			"pii-direct", "pii-api-db", "pii-session",
			"sql-injection", "shell-injection",
			"hallucination", "misinformation-disinformation",
		},
	},
	"eu-ai-act": {
		ID:          "eu-ai-act",
		Name:        "EU AI Act",
		Description: "European Union Artificial Intelligence Act",
		Vulnerabilities: []string{
			"excessive-agency", "misinformation-disinformation",
			"pii-direct", "pii-session",
			"sql-injection", "shell-injection",
			"hate-speech", "hallucination",
		},
	},
	"gdpr": {
		ID:          "gdpr",
		Name:        "GDPR",
		Description: "General Data Protection Regulation",
		Vulnerabilities: []string{
			"pii-direct", "pii-api-db", "pii-session", "pii-social",
			"cross-session-leakage",
			"bias-age", "bias-gender", "bias-race",
			"hate-speech",
			"rbac", "bola",
			"sql-injection", "shell-injection",
		},
	},
	"owasp-api": {
		ID:          "owasp-api",
		Name:        "OWASP API Top 10",
		Description: "OWASP API Security Top 10",
		Vulnerabilities: []string{
			"bola", "rbac", "excessive-agency",
			"unbounded-consumption",
			"ssrf", "debug-access",
			"pii-api-db", "pii-session",
			"sql-injection", "shell-injection",
		},
	},
	"basic-security": {
		ID:          "basic-security",
		Name:        "Basic Security",
		Description: "Basic security testing for AI agents",
		Vulnerabilities: []string{
			"prompt-extraction", "prompt-override",
			"pii-direct",
			"sql-injection", "shell-injection",
			"excessive-agency",
		},
	},
}

// GetVulnerability returns a vulnerability by ID.
func GetVulnerability(id string) *Vulnerability {
	return VulnerabilityCatalog[id]
}

// GetAttack returns an attack by ID.
func GetAttack(id string) *Attack {
	return AttackCatalog[id]
}

// GetFramework returns a framework by ID.
func GetFramework(id string) *Framework {
	return FrameworkCatalog[id]
}

// GetVulnerabilitiesByCategory returns vulnerabilities grouped by category.
func GetVulnerabilitiesByCategory() map[VulnerabilityCategory][]*Vulnerability {
	result := make(map[VulnerabilityCategory][]*Vulnerability)
	for _, vuln := range VulnerabilityCatalog {
		result[vuln.Category] = append(result[vuln.Category], vuln)
	}
	return result
}

// GetAttacksByCategory returns attacks grouped by category.
func GetAttacksByCategory() map[AttackCategory][]*Attack {
	result := make(map[AttackCategory][]*Attack)
	for _, attack := range AttackCatalog {
		result[attack.Category] = append(result[attack.Category], attack)
	}
	return result
}

// GetVulnerabilityCategoryOrder returns categories in display order.
func GetVulnerabilityCategoryOrder() []VulnerabilityCategory {
	return []VulnerabilityCategory{
		CategoryPromptSecurity,
		CategoryPIIProtection,
		CategoryTechnical,
		CategoryAccessControl,
		CategoryContentSafety,
		CategoryBiasFairness,
		CategoryBusinessLogic,
		CategoryInfoQuality,
		CategoryAgentSpecific,
		CategoryResourceAttacks,
		CategorySpecializedThreats,
		CategoryCompliance,
		CategoryIP,
	}
}

// GetAttackCategoryOrder returns attack categories in display order.
func GetAttackCategoryOrder() []AttackCategory {
	return []AttackCategory{
		AttackCategorySingleTurn,
		AttackCategoryMultiTurn,
		AttackCategoryAgentic,
	}
}

// GetAllFrameworks returns all framework definitions.
func GetAllFrameworks() []*Framework {
	result := make([]*Framework, 0, len(FrameworkCatalog))
	for _, framework := range FrameworkCatalog {
		result = append(result, framework)
	}
	return result
}

// GetUniqueVulnerabilitiesForFrameworks returns deduplicated vulnerabilities for selected frameworks.
func GetUniqueVulnerabilitiesForFrameworks(frameworkIDs []string) []string {
	seen := make(map[string]bool)
	var result []string

	for _, fwID := range frameworkIDs {
		fw := GetFramework(fwID)
		if fw != nil {
			for _, vulnID := range fw.Vulnerabilities {
				if !seen[vulnID] {
					seen[vulnID] = true
					result = append(result, vulnID)
				}
			}
		}
	}

	return result
}

// GetBasicScanVulnerabilities returns vulnerability IDs for basic scan.
// Only includes non-premium vulnerabilities from Prompt Security and PII Protection categories.
func GetBasicScanVulnerabilities() []string {
	return []string{
		// Prompt Security (free)
		"prompt-extraction",
		"prompt-override",
		"indirect-injection",
		"ascii-smuggling",
		// PII Protection (free)
		"pii-direct",
		"pii-api-db",
		"pii-session",
		"cross-session-leakage",
	}
}

// GetBasicScanAttacks returns attack IDs for basic scan.
func GetBasicScanAttacks() []string {
	return []string{
		"base64",
		"rot13",
		"prompt-injection",
		"roleplay",
		"prompt-probing",
		"social-engineering-prompt-extraction",
	}
}

// GetFreeVulnerabilities returns all non-premium vulnerability IDs.
func GetFreeVulnerabilities() []string {
	var result []string
	for id, vuln := range VulnerabilityCatalog {
		if !vuln.Premium {
			result = append(result, id)
		}
	}
	return result
}

// GetFreeAttacks returns all non-premium attack IDs.
func GetFreeAttacks() []string {
	var result []string
	for id, attack := range AttackCatalog {
		if !attack.Premium {
			result = append(result, id)
		}
	}
	return result
}
