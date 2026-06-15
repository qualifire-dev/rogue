// Package resilience provides TUI views for Rogue Resilience chaos experiments.
package resilience

// InjectorEntry describes a fault injection strategy in the TUI catalog.
type InjectorEntry struct {
	ID          string
	Name        string
	Description string
	Premium     bool
}

// BuiltInInjectors mirrors packages/web/src/lib/resilience-catalog.ts.
var BuiltInInjectors = []InjectorEntry{
	{ID: "tool_misuse", Name: "Tool misuse", Description: "Unauthorized or malformed tool calls"},
	{ID: "hallucination_spamming", Name: "Hallucination spamming", Description: "High-volume fabricated output"},
	{ID: "goal_conflict", Name: "Goal conflict", Description: "Adversarial sub-goals"},
	{ID: "policy_violation", Name: "Policy violation", Description: "Deliberate business-rule breaches"},
	{ID: "action_spam", Name: "Action spam", Description: "Rapid-fire messages and actions"},
	{ID: "gradual_goal_drift", Name: "Gradual goal drift", Description: "Multi-turn sub-goal escalation", Premium: true},
}

// ArchitectureEntry describes a multi-agent topology profile.
type ArchitectureEntry struct {
	ID          string
	Name        string
	Description string
}

// Architectures lists supported resilience architecture profiles.
var Architectures = []ArchitectureEntry{
	{ID: "single_agent", Name: "Single agent", Description: "One agent under test"},
	{ID: "hierarchical", Name: "Hierarchical", Description: "Supervisor + workers"},
	{ID: "peer_to_peer", Name: "Peer to peer", Description: "Fully connected peers"},
	{ID: "supervisor_worker", Name: "Supervisor worker", Description: "Sequential pipeline"},
}
