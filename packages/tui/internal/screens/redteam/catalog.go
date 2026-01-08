// Package redteam provides vulnerability, attack, and framework catalogs.
// This catalog is synchronized with the Python backend catalog at:
// rogue/server/red_teaming/catalog/vulnerabilities.py
// rogue/server/red_teaming/catalog/attacks.py
package redteam

// VulnerabilityCatalog contains all vulnerability definitions.
// Synchronized with Python backend catalog.
var VulnerabilityCatalog = map[string]*Vulnerability{
	// ==========================================================================
	// PROMPT SECURITY (Free tier)
	// ==========================================================================
	"prompt-extraction":       {ID: "prompt-extraction", Name: "System Prompt Disclosure", Category: CategoryPromptSecurity, Description: "Tests for system prompt disclosure vulnerabilities", DefaultAttacks: []string{"prompt-probing", "system-override", "gray-box", "base64", "rot13"}, Premium: false},
	"prompt-override":         {ID: "prompt-override", Name: "System Prompt Override", Category: CategoryPromptSecurity, Description: "Tests for system prompt override vulnerabilities", DefaultAttacks: []string{"system-override", "prompt-injection", "context-poisoning"}, Premium: false},
	"indirect-injection":      {ID: "indirect-injection", Name: "Indirect Prompt Injection", Category: CategoryPromptSecurity, Description: "Tests for injection vulnerabilities via untrusted variables", DefaultAttacks: []string{"prompt-injection", "context-poisoning", "input-bypass"}, Premium: false},
	"ascii-smuggling":         {ID: "ascii-smuggling", Name: "ASCII Smuggling", Category: CategoryPromptSecurity, Description: "Tests vulnerability to Unicode tag-based instruction smuggling attacks", DefaultAttacks: []string{"base64", "rot13", "leetspeak", "input-bypass"}, Premium: false},
	"special-token-injection": {ID: "special-token-injection", Name: "Special Token Injection", Category: CategoryPromptSecurity, Description: "Tests vulnerability to token injection attacks using format-specific delimiters", DefaultAttacks: []string{"prompt-injection", "input-bypass", "base64"}, Premium: false},
	"pliny-injections":        {ID: "pliny-injections", Name: "Pliny Prompt Injections", Category: CategoryPromptSecurity, Description: "Tests handling of Pliny prompt injections", DefaultAttacks: []string{"prompt-injection", "context-poisoning"}, Premium: true},
	"context-compliance":      {ID: "context-compliance", Name: "Context Compliance Attack", Category: CategoryPromptSecurity, Description: "Tests for vulnerability to Context Compliance Attacks using fabricated conversation history", DefaultAttacks: []string{"context-poisoning", "prompt-injection"}, Premium: true},

	// ==========================================================================
	// PII PROTECTION (Free tier)
	// ==========================================================================
	"pii-direct":            {ID: "pii-direct", Name: "PII via Direct Exposure", Category: CategoryPIIProtection, Description: "Tests for direct PII exposure vulnerabilities", DefaultAttacks: []string{"prompt-injection", "prompt-probing", "permission-escalation"}, Premium: false},
	"pii-api-db":            {ID: "pii-api-db", Name: "PII via API/Database", Category: CategoryPIIProtection, Description: "Tests for PII exposure via API/database access", DefaultAttacks: []string{"prompt-injection", "gray-box", "permission-escalation"}, Premium: false},
	"pii-session":           {ID: "pii-session", Name: "PII via Session Data", Category: CategoryPIIProtection, Description: "Tests for PII exposure in session data", DefaultAttacks: []string{"prompt-injection", "context-poisoning", "gray-box"}, Premium: false},
	"pii-social":            {ID: "pii-social", Name: "PII via Social Engineering", Category: CategoryPIIProtection, Description: "Tests for PII exposure via social engineering", DefaultAttacks: []string{"roleplay", "goal-redirection", "permission-escalation"}, Premium: true},
	"cross-session-leakage": {ID: "cross-session-leakage", Name: "Cross-Session Data Leakage", Category: CategoryPIIProtection, Description: "Tests for information leakage between user sessions", DefaultAttacks: []string{"prompt-injection", "context-poisoning", "gray-box"}, Premium: false},
	"privacy-violation":     {ID: "privacy-violation", Name: "Privacy Violation", Category: CategoryPIIProtection, Description: "Tests handling of privacy violation attempts", DefaultAttacks: []string{"prompt-injection", "roleplay", "permission-escalation"}, Premium: false},

	// ==========================================================================
	// TECHNICAL (Premium tier)
	// ==========================================================================
	"sql-injection":   {ID: "sql-injection", Name: "SQL Injection", Category: CategoryTechnical, Description: "Tests for SQL injection vulnerabilities", DefaultAttacks: []string{"prompt-injection", "input-bypass", "base64"}, Premium: true},
	"shell-injection": {ID: "shell-injection", Name: "Command Injection", Category: CategoryTechnical, Description: "Tests for command injection vulnerabilities", DefaultAttacks: []string{"prompt-injection", "input-bypass", "base64"}, Premium: true},
	"ssrf":            {ID: "ssrf", Name: "SSRF Vulnerability", Category: CategoryTechnical, Description: "Tests for server-side request forgery vulnerabilities", DefaultAttacks: []string{"prompt-injection", "input-bypass", "gray-box"}, Premium: true},
	"debug-access":    {ID: "debug-access", Name: "Debug Interface Exposure", Category: CategoryTechnical, Description: "Tests for exposed debugging interfaces and commands", DefaultAttacks: []string{"prompt-probing", "gray-box", "permission-escalation"}, Premium: true},
	"malicious-code":  {ID: "malicious-code", Name: "Malicious Code", Category: CategoryTechnical, Description: "Tests creation of malicious code", DefaultAttacks: []string{"prompt-injection", "roleplay", "base64"}, Premium: true},

	// ==========================================================================
	// ACCESS CONTROL (Premium tier)
	// ==========================================================================
	"rbac":             {ID: "rbac", Name: "RBAC Implementation", Category: CategoryAccessControl, Description: "Tests role-based access control implementation", DefaultAttacks: []string{"permission-escalation", "gray-box", "prompt-injection"}, Premium: true},
	"bola":             {ID: "bola", Name: "Object-Level Authorization Bypass", Category: CategoryAccessControl, Description: "Tests for broken object-level authorization vulnerabilities (OWASP API 1)", DefaultAttacks: []string{"permission-escalation", "gray-box", "input-bypass"}, Premium: true},
	"bfla":             {ID: "bfla", Name: "Function-Level Authorization Bypass", Category: CategoryAccessControl, Description: "Tests for broken function-level authorization vulnerabilities (OWASP API 5)", DefaultAttacks: []string{"permission-escalation", "gray-box", "prompt-injection"}, Premium: true},
	"excessive-agency": {ID: "excessive-agency", Name: "Excessive Agency", Category: CategoryAccessControl, Description: "Tests for unauthorized actions beyond defined system boundaries", DefaultAttacks: []string{"roleplay", "goal-redirection", "permission-escalation", "context-poisoning"}, Premium: true},

	// ==========================================================================
	// CONTENT SAFETY (Premium tier)
	// ==========================================================================
	"hate-speech":        {ID: "hate-speech", Name: "Hate Speech", Category: CategoryContentSafety, Description: "Tests handling of hate speech and discriminatory content", DefaultAttacks: []string{"prompt-injection", "roleplay", "context-poisoning"}, Premium: true},
	"explicit-content":   {ID: "explicit-content", Name: "Explicit Content", Category: CategoryContentSafety, Description: "Tests handling of explicit sexual content", DefaultAttacks: []string{"prompt-injection", "roleplay", "goal-redirection"}, Premium: true},
	"violent-crime":      {ID: "violent-crime", Name: "Violent Crime Content", Category: CategoryContentSafety, Description: "Tests handling of violent crime content", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
	"sexual-crime":       {ID: "sexual-crime", Name: "Sexual Crime Content", Category: CategoryContentSafety, Description: "Tests handling of sexual crime content", DefaultAttacks: []string{"prompt-injection", "roleplay", "context-poisoning"}, Premium: true},
	"child-exploitation": {ID: "child-exploitation", Name: "Child Exploitation", Category: CategoryContentSafety, Description: "Tests handling of child exploitation content", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"harassment":         {ID: "harassment", Name: "Harassment", Category: CategoryContentSafety, Description: "Tests handling of harassment and bullying content", DefaultAttacks: []string{"prompt-injection", "roleplay", "goal-redirection"}, Premium: true},
	"personal-attacks":   {ID: "personal-attacks", Name: "Personal Attacks", Category: CategoryContentSafety, Description: "Tests handling of personal attacks and insults", DefaultAttacks: []string{"prompt-injection", "roleplay"}, Premium: true},
	"profanity":          {ID: "profanity", Name: "Profanity", Category: CategoryContentSafety, Description: "Tests handling of profane or inappropriate language", DefaultAttacks: []string{"prompt-injection", "leetspeak", "rot13"}, Premium: true},
	"graphic-content":    {ID: "graphic-content", Name: "Graphic Content", Category: CategoryContentSafety, Description: "Tests handling of graphic or violent content", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
	"self-harm":          {ID: "self-harm", Name: "Self-Harm", Category: CategoryContentSafety, Description: "Tests handling of self-harm and suicide content", DefaultAttacks: []string{"prompt-injection", "roleplay", "context-poisoning"}, Premium: true},
	"dangerous-activity": {ID: "dangerous-activity", Name: "Dangerous Activity Content", Category: CategoryContentSafety, Description: "Tests handling of dangerous activity instructions", DefaultAttacks: []string{"prompt-injection", "roleplay", "math-problem"}, Premium: true},
	"wordplay":           {ID: "wordplay", Name: "Wordplay", Category: CategoryContentSafety, Description: "Tests whether AI systems can be tricked into generating profanity through wordplay", DefaultAttacks: []string{"prompt-injection", "leetspeak", "semantic-manipulation"}, Premium: true},

	// ==========================================================================
	// BIAS & FAIRNESS (Premium tier)
	// ==========================================================================
	"bias-age":        {ID: "bias-age", Name: "Age Bias", Category: CategoryBiasFairness, Description: "Age-related bias detection", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
	"bias-gender":     {ID: "bias-gender", Name: "Gender Bias", Category: CategoryBiasFairness, Description: "Gender-related bias detection", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
	"bias-race":       {ID: "bias-race", Name: "Race Bias", Category: CategoryBiasFairness, Description: "Race-related bias detection", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
	"bias-disability": {ID: "bias-disability", Name: "Disability Bias", Category: CategoryBiasFairness, Description: "Disability-related bias detection", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
	"bias-religion":   {ID: "bias-religion", Name: "Religious Bias", Category: CategoryBiasFairness, Description: "Tests handling of religious content and bias", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
	"bias-political":  {ID: "bias-political", Name: "Political Bias", Category: CategoryBiasFairness, Description: "Tests handling of political content and bias", DefaultAttacks: []string{"prompt-injection", "roleplay", "goal-redirection"}, Premium: true},

	// ==========================================================================
	// BUSINESS LOGIC (Premium tier)
	// ==========================================================================
	"unauthorized-commitments": {ID: "unauthorized-commitments", Name: "Unauthorized Commitments", Category: CategoryBusinessLogic, Description: "Tests for unauthorized contractual commitments and legal exposure", DefaultAttacks: []string{"roleplay", "goal-redirection", "context-poisoning"}, Premium: true},
	"unauthorized-advice":      {ID: "unauthorized-advice", Name: "Unauthorized Advice", Category: CategoryBusinessLogic, Description: "Tests handling of unauthorized professional advice", DefaultAttacks: []string{"roleplay", "prompt-injection", "goal-redirection"}, Premium: true},
	"competitors":              {ID: "competitors", Name: "Competitors", Category: CategoryBusinessLogic, Description: "Tests for unauthorized competitor mentions and endorsements", DefaultAttacks: []string{"prompt-injection", "roleplay", "goal-redirection"}, Premium: true},
	"imitation":                {ID: "imitation", Name: "Entity Impersonation", Category: CategoryBusinessLogic, Description: "Tests handling of unauthorized impersonation of entities", DefaultAttacks: []string{"roleplay", "context-poisoning", "prompt-injection"}, Premium: true},
	"goal-misalignment":        {ID: "goal-misalignment", Name: "Goal Misalignment", Category: CategoryBusinessLogic, Description: "Tests whether AI systems recognize when optimizing proxy metrics might not align with true goals", DefaultAttacks: []string{"goal-redirection", "roleplay", "semantic-manipulation"}, Premium: true},
	"off-topic":                {ID: "off-topic", Name: "Off-Topic Manipulation", Category: CategoryBusinessLogic, Description: "Tests whether AI systems can be manipulated to go off-topic from their intended purpose", DefaultAttacks: []string{"goal-redirection", "context-poisoning", "roleplay"}, Premium: true},
	"hijacking":                {ID: "hijacking", Name: "Resource Hijacking", Category: CategoryBusinessLogic, Description: "Tests for unauthorized resource usage and purpose deviation", DefaultAttacks: []string{"goal-redirection", "permission-escalation", "roleplay"}, Premium: true},

	// ==========================================================================
	// INFORMATION QUALITY (Premium tier)
	// ==========================================================================
	"hallucination":                 {ID: "hallucination", Name: "Hallucination", Category: CategoryInfoQuality, Description: "Tests for fabrication of false or misleading information", DefaultAttacks: []string{"prompt-injection", "roleplay", "goal-redirection"}, Premium: true},
	"unverifiable-claims":           {ID: "unverifiable-claims", Name: "Unverifiable Claims", Category: CategoryInfoQuality, Description: "Tests for claims that cannot be verified or fact-checked", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
	"misinformation-disinformation": {ID: "misinformation-disinformation", Name: "Disinformation Campaigns", Category: CategoryInfoQuality, Description: "Tests handling of false information campaigns", DefaultAttacks: []string{"prompt-injection", "roleplay", "context-poisoning"}, Premium: true},
	"overreliance":                  {ID: "overreliance", Name: "Overreliance", Category: CategoryInfoQuality, Description: "Tests for overreliance on system assumptions", DefaultAttacks: []string{"prompt-injection", "context-poisoning", "gray-box"}, Premium: true},

	// ==========================================================================
	// AGENT-SPECIFIC (Premium tier)
	// ==========================================================================
	"memory-poisoning":    {ID: "memory-poisoning", Name: "Agentic Memory Poisoning", Category: CategoryAgentSpecific, Description: "Tests whether an agent is vulnerable to memory poisoning attacks", DefaultAttacks: []string{"context-poisoning", "prompt-injection"}, Premium: true},
	"rag-poisoning":       {ID: "rag-poisoning", Name: "RAG Poisoning", Category: CategoryAgentSpecific, Description: "Tests for vulnerabilities to RAG retrieval poisoning attacks", DefaultAttacks: []string{"context-poisoning", "prompt-injection"}, Premium: true},
	"rag-exfiltration":    {ID: "rag-exfiltration", Name: "RAG Document Exfiltration", Category: CategoryAgentSpecific, Description: "Tests for RAG document exfiltration", DefaultAttacks: []string{"prompt-injection", "prompt-probing", "gray-box"}, Premium: true},
	"tool-discovery":      {ID: "tool-discovery", Name: "Tool Discovery", Category: CategoryAgentSpecific, Description: "Tests for enumeration of available tools and function calls", DefaultAttacks: []string{"prompt-probing", "gray-box", "prompt-injection"}, Premium: true},
	"mcp-vulnerabilities": {ID: "mcp-vulnerabilities", Name: "Model Context Protocol", Category: CategoryAgentSpecific, Description: "Tests for vulnerabilities to Model Context Protocol (MCP) attacks", DefaultAttacks: []string{"prompt-injection", "context-poisoning"}, Premium: true},

	// ==========================================================================
	// RESOURCE ATTACKS (Premium tier)
	// ==========================================================================
	"unbounded-consumption": {ID: "unbounded-consumption", Name: "Unbounded Consumption", Category: CategoryResourceAttacks, Description: "Tests for resource exhaustion vulnerabilities", DefaultAttacks: []string{"prompt-injection", "goal-redirection"}, Premium: true},
	"reasoning-dos":         {ID: "reasoning-dos", Name: "Reasoning DoS", Category: CategoryResourceAttacks, Description: "Tests for vulnerabilities to computational resource exhaustion through excessive reasoning patterns", DefaultAttacks: []string{"prompt-injection", "math-problem"}, Premium: true},
	"divergent-repetition":  {ID: "divergent-repetition", Name: "Divergent Repetition", Category: CategoryResourceAttacks, Description: "Tests for training data leaks through repetitive pattern exploitation", DefaultAttacks: []string{"prompt-injection", "goal-redirection"}, Premium: true},

	// ==========================================================================
	// INTELLECTUAL PROPERTY (Premium tier)
	// ==========================================================================
	"ip-violations": {ID: "ip-violations", Name: "IP Violations", Category: CategoryIP, Description: "Tests handling of intellectual property violations", DefaultAttacks: []string{"prompt-injection", "roleplay", "goal-redirection"}, Premium: true},
	"ip-theft":      {ID: "ip-theft", Name: "IP Theft", Category: CategoryIP, Description: "Tests handling of IP theft and violations", DefaultAttacks: []string{"prompt-injection", "roleplay", "context-poisoning"}, Premium: true},

	// ==========================================================================
	// COMPLIANCE (Premium tier)
	// ==========================================================================
	"coppa": {ID: "coppa", Name: "COPPA Compliance", Category: CategoryCompliance, Description: "Tests for COPPA (Children's Online Privacy Protection Act) compliance violations", DefaultAttacks: []string{"prompt-injection", "roleplay", "goal-redirection"}, Premium: true},
	"ferpa": {ID: "ferpa", Name: "FERPA Compliance", Category: CategoryCompliance, Description: "Tests for compliance with Family Educational Rights and Privacy Act", DefaultAttacks: []string{"prompt-injection", "permission-escalation", "gray-box"}, Premium: true},

	// ==========================================================================
	// SPECIALIZED THREATS (Premium tier)
	// ==========================================================================
	"cybercrime":        {ID: "cybercrime", Name: "Cybercrime", Category: CategorySpecializedThreats, Description: "Tests handling of cybercrime-related content", DefaultAttacks: []string{"prompt-injection", "roleplay", "base64"}, Premium: true},
	"wmd-content":       {ID: "wmd-content", Name: "WMD Content", Category: CategorySpecializedThreats, Description: "Tests handling of WMD-related content", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
	"weapons-content":   {ID: "weapons-content", Name: "Weapons Content", Category: CategorySpecializedThreats, Description: "Tests handling of weapons-related content", DefaultAttacks: []string{"prompt-injection", "roleplay", "math-problem"}, Premium: true},
	"ied-content":       {ID: "ied-content", Name: "Improvised Explosive Devices", Category: CategorySpecializedThreats, Description: "Tests handling of Improvised Explosive Devices", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
	"drugs":             {ID: "drugs", Name: "Drug-Related Content", Category: CategorySpecializedThreats, Description: "Tests handling of illegal drug-related content", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
	"methamphetamine":   {ID: "methamphetamine", Name: "Methamphetamine Content", Category: CategorySpecializedThreats, Description: "Tests handling of methamphetamine-related content", DefaultAttacks: []string{"prompt-injection", "roleplay", "base64"}, Premium: true},
	"extremism":         {ID: "extremism", Name: "Extremist Content", Category: CategorySpecializedThreats, Description: "Tests handling of extremist content and recruitment", DefaultAttacks: []string{"prompt-injection", "roleplay", "context-poisoning"}, Premium: true},
	"illegal-activity":  {ID: "illegal-activity", Name: "Illegal Activity", Category: CategorySpecializedThreats, Description: "Tests handling of general illegal activities", DefaultAttacks: []string{"prompt-injection", "roleplay", "goal-redirection"}, Premium: true},
	"non-violent-crime": {ID: "non-violent-crime", Name: "Non-Violent Crime", Category: CategorySpecializedThreats, Description: "Tests handling of non-violent criminal content", DefaultAttacks: []string{"prompt-injection", "roleplay", "semantic-manipulation"}, Premium: true},
}

// AttackCatalog contains all attack technique definitions.
// Synchronized with Python backend catalog.
var AttackCatalog = map[string]*Attack{
	// ==========================================================================
	// SINGLE-TURN FREE ATTACKS (Used in basic scans)
	// ==========================================================================
	"base64":           {ID: "base64", Name: "Base64 Encoding", Category: AttackCategorySingleTurn, Description: "Encodes the attack input in Base64 to bypass text-based filters", Premium: false},
	"rot13":            {ID: "rot13", Name: "ROT13 Encoding", Category: AttackCategorySingleTurn, Description: "Encodes the attack input using ROT13 cipher to bypass filters", Premium: false},
	"prompt-injection": {ID: "prompt-injection", Name: "Prompt Injection", Category: AttackCategorySingleTurn, Description: "Direct prompt injection to override system instructions", Premium: false},
	"roleplay":         {ID: "roleplay", Name: "Roleplay", Category: AttackCategorySingleTurn, Description: "Uses roleplay scenarios to bypass safety filters", Premium: false},
	"prompt-probing":   {ID: "prompt-probing", Name: "Prompt Probing", Category: AttackCategorySingleTurn, Description: "Attempts to extract system prompts through probing questions", Premium: false},

	// ==========================================================================
	// SINGLE-TURN PREMIUM ATTACKS (Require Deckard service)
	// ==========================================================================
	// Encoding-based attacks (premium)
	"hex":       {ID: "hex", Name: "Hex Encoding", Category: AttackCategorySingleTurn, Description: "Encodes the attack input in hexadecimal to bypass filters", Premium: true},
	"leetspeak": {ID: "leetspeak", Name: "Leetspeak", Category: AttackCategorySingleTurn, Description: "Transforms text using leetspeak (1337) character substitutions", Premium: true},
	"homoglyph": {ID: "homoglyph", Name: "Homoglyph Encoding", Category: AttackCategorySingleTurn, Description: "Uses visually similar Unicode characters to bypass text filters", Premium: true},
	// Context/manipulation attacks (premium)
	"math-problem":          {ID: "math-problem", Name: "Math Prompt", Category: AttackCategorySingleTurn, Description: "Encodes harmful requests in math to distract filters", Premium: true},
	"gray-box":              {ID: "gray-box", Name: "Gray Box", Category: AttackCategorySingleTurn, Description: "Injects fake internal info to gain trust or trick model", Premium: true},
	"multilingual":          {ID: "multilingual", Name: "Multilingual", Category: AttackCategorySingleTurn, Description: "Uses translation framing to bypass language-specific filters", Premium: true},
	"context-poisoning":     {ID: "context-poisoning", Name: "Context Poisoning", Category: AttackCategorySingleTurn, Description: "Injects malicious context or instructions to alter model behavior", Premium: true},
	"goal-redirection":      {ID: "goal-redirection", Name: "Goal Redirection", Category: AttackCategorySingleTurn, Description: "Attempts to shift the goal of the conversation mid-prompt", Premium: true},
	"input-bypass":          {ID: "input-bypass", Name: "Input Bypass", Category: AttackCategorySingleTurn, Description: "Splits payload or uses delimiters to bypass regex filters", Premium: true},
	"permission-escalation": {ID: "permission-escalation", Name: "Permission Escalation", Category: AttackCategorySingleTurn, Description: "Attempts to bypass permission checks by claiming elevated status", Premium: true},
	"system-override":       {ID: "system-override", Name: "System Override", Category: AttackCategorySingleTurn, Description: "Uses explicit system override commands to bypass restrictions", Premium: true},
	"semantic-manipulation": {ID: "semantic-manipulation", Name: "Semantic Manipulation", Category: AttackCategorySingleTurn, Description: "Uses semantic tricks and complex phrasing to disguise intent", Premium: true},
	// Advanced premium attacks
	"citation":         {ID: "citation", Name: "Citation", Category: AttackCategorySingleTurn, Description: "Frames harmful content as academic citations or references", Premium: true},
	"gcg":              {ID: "gcg", Name: "GCG (Greedy Coordinate Gradient)", Category: AttackCategorySingleTurn, Description: "Gradient-based adversarial suffix generation", Premium: true},
	"likert-jailbreak": {ID: "likert-jailbreak", Name: "Likert-based Jailbreaks", Category: AttackCategorySingleTurn, Description: "Uses Likert scale framing to manipulate responses", Premium: true},
	"best-of-n":        {ID: "best-of-n", Name: "Best-of-N", Category: AttackCategorySingleTurn, Description: "Generates multiple variations and selects the most effective", Premium: true},

	// ==========================================================================
	// MULTI-TURN PREMIUM ATTACKS (Require Deckard service)
	// ==========================================================================
	"social-engineering-prompt-extraction": {ID: "social-engineering-prompt-extraction", Name: "Social Engineering Prompt Extraction", Category: AttackCategoryMultiTurn, Description: "Uses trust-building and social engineering to extract system prompts", Premium: true},
	"multi-turn-jailbreak":                 {ID: "multi-turn-jailbreak", Name: "Multi-turn Jailbreaks", Category: AttackCategoryMultiTurn, Description: "Progressive jailbreaking across multiple conversation turns", Premium: true},
	"goat":                                 {ID: "goat", Name: "GOAT", Category: AttackCategoryMultiTurn, Description: "Generative Offensive Agent Tester - adaptive multi-turn attacks", Premium: true},
	"mischievous-user":                     {ID: "mischievous-user", Name: "Mischievous User", Category: AttackCategoryMultiTurn, Description: "Simulates a persistent mischievous user trying various tactics", Premium: true},
	"simba":                                {ID: "simba", Name: "Simba", Category: AttackCategoryMultiTurn, Description: "Simulation-based multi-turn adversarial attacks", Premium: true},
	"crescendo":                            {ID: "crescendo", Name: "Crescendo", Category: AttackCategoryMultiTurn, Description: "Gradually escalating attack intensity across turns", Premium: true},
	"linear-jailbreak":                     {ID: "linear-jailbreak", Name: "Linear Jailbreaking", Category: AttackCategoryMultiTurn, Description: "Sequential jailbreaking strategy with linear progression", Premium: true},
	"sequential-jailbreak":                 {ID: "sequential-jailbreak", Name: "Sequential Jailbreak", Category: AttackCategoryMultiTurn, Description: "Combines multiple single-turn techniques in sequence", Premium: true},
	"bad-likert-judge":                     {ID: "bad-likert-judge", Name: "Bad Likert Judge", Category: AttackCategoryMultiTurn, Description: "Manipulates the agent by acting as a strict evaluator", Premium: true},

	// ==========================================================================
	// AGENTIC ATTACKS (All Premium - Require Deckard service)
	// ==========================================================================
	"iterative-jailbreak":   {ID: "iterative-jailbreak", Name: "Iterative Jailbreaks", Category: AttackCategoryAgentic, Description: "AI-driven iterative refinement of jailbreak attempts", Premium: true},
	"meta-agent-jailbreak":  {ID: "meta-agent-jailbreak", Name: "Meta-Agent Jailbreaks", Category: AttackCategoryAgentic, Description: "Uses a meta-agent to orchestrate attack strategies", Premium: true},
	"hydra":                 {ID: "hydra", Name: "Hydra Multi-turn", Category: AttackCategoryAgentic, Description: "Multi-headed attack strategy with parallel exploration", Premium: true},
	"tree-jailbreak":        {ID: "tree-jailbreak", Name: "Tree-based Jailbreaks", Category: AttackCategoryAgentic, Description: "Tree search-based exploration of attack vectors", Premium: true},
	"single-turn-composite": {ID: "single-turn-composite", Name: "Single Turn Composite", Category: AttackCategoryAgentic, Description: "Combines multiple single-turn attacks in one message", Premium: true},
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
			"bola", "rbac", "bfla", "excessive-agency",
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
			"indirect-injection",
			"ascii-smuggling",
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
		CategoryIP,
		CategoryCompliance,
		CategorySpecializedThreats,
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
		"special-token-injection",
		// PII Protection (free)
		"pii-direct",
		"pii-api-db",
		"pii-session",
		"cross-session-leakage",
		"privacy-violation",
	}
}

// GetBasicScanAttacks returns attack IDs for basic scan.
// Only includes non-premium single-turn attacks.
func GetBasicScanAttacks() []string {
	return []string{
		"base64",
		"rot13",
		"prompt-injection",
		"roleplay",
		"prompt-probing",
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
