/**
 * Mirror of `packages/tui/internal/screens/redteam/catalog.go`.
 * Categories, ids, names, and premium flags are kept in lockstep with the Go
 * source. When the Go catalog changes, this file must be regenerated.
 */

export interface CatalogItem {
  id: string;
  name: string;
  premium: boolean;
}
export interface Category {
  title: string;
  items: CatalogItem[];
}

export const VULNERABILITY_CATALOG: Category[] = [
  {
    title: "Prompt Security",
    items: [
      { id: "prompt-extraction", name: "System Prompt Disclosure", premium: false },
      { id: "prompt-override", name: "System Prompt Override", premium: false },
      { id: "indirect-injection", name: "Indirect Prompt Injection", premium: false },
      { id: "ascii-smuggling", name: "ASCII Smuggling", premium: false },
      { id: "special-token-injection", name: "Special Token Injection", premium: false },
      { id: "pliny-injections", name: "Pliny Prompt Injections", premium: true },
      { id: "context-compliance", name: "Context Compliance Attack", premium: true },
    ],
  },
  {
    title: "PII Protection",
    items: [
      { id: "pii-direct", name: "PII via Direct Exposure", premium: false },
      { id: "pii-api-db", name: "PII via API/Database", premium: false },
      { id: "pii-session", name: "PII via Session Data", premium: false },
      { id: "cross-session-leakage", name: "Cross-Session Data Leakage", premium: false },
      { id: "privacy-violation", name: "Privacy Violation", premium: false },
      { id: "pii-social", name: "PII via Social Engineering", premium: true },
    ],
  },
  {
    title: "Technical",
    items: [
      { id: "sql-injection", name: "SQL Injection", premium: true },
      { id: "shell-injection", name: "Command Injection", premium: true },
      { id: "ssrf", name: "SSRF Vulnerability", premium: true },
      { id: "debug-access", name: "Debug Interface Exposure", premium: true },
      { id: "malicious-code", name: "Malicious Code", premium: true },
    ],
  },
  {
    title: "Access Control",
    items: [
      { id: "rbac", name: "RBAC Implementation", premium: true },
      { id: "bola", name: "Object-Level Authorization Bypass", premium: true },
      { id: "bfla", name: "Function-Level Authorization Bypass", premium: true },
      { id: "excessive-agency", name: "Excessive Agency", premium: true },
    ],
  },
  {
    title: "Content Safety",
    items: [
      { id: "hate-speech", name: "Hate Speech", premium: true },
      { id: "explicit-content", name: "Explicit Content", premium: true },
      { id: "violent-crime", name: "Violent Crime Content", premium: true },
      { id: "sexual-crime", name: "Sexual Crime Content", premium: true },
      { id: "child-exploitation", name: "Child Exploitation", premium: true },
      { id: "harassment", name: "Harassment", premium: true },
      { id: "personal-attacks", name: "Personal Attacks", premium: true },
      { id: "profanity", name: "Profanity", premium: true },
      { id: "graphic-content", name: "Graphic Content", premium: true },
      { id: "self-harm", name: "Self-Harm", premium: true },
      { id: "dangerous-activity", name: "Dangerous Activity Content", premium: true },
      { id: "wordplay", name: "Wordplay", premium: true },
    ],
  },
  {
    title: "Bias & Fairness",
    items: [
      { id: "bias-age", name: "Age Bias", premium: true },
      { id: "bias-gender", name: "Gender Bias", premium: true },
      { id: "bias-race", name: "Race Bias", premium: true },
      { id: "bias-disability", name: "Disability Bias", premium: true },
      { id: "bias-religion", name: "Religious Bias", premium: true },
      { id: "bias-political", name: "Political Bias", premium: true },
    ],
  },
  {
    title: "Business Logic",
    items: [
      { id: "unauthorized-commitments", name: "Unauthorized Commitments", premium: true },
      { id: "unauthorized-advice", name: "Unauthorized Advice", premium: true },
      { id: "competitors", name: "Competitors", premium: true },
      { id: "imitation", name: "Entity Impersonation", premium: true },
      { id: "goal-misalignment", name: "Goal Misalignment", premium: true },
      { id: "off-topic", name: "Off-Topic Manipulation", premium: true },
      { id: "hijacking", name: "Resource Hijacking", premium: true },
    ],
  },
  {
    title: "Information Quality",
    items: [
      { id: "hallucination", name: "Hallucination", premium: true },
      { id: "unverifiable-claims", name: "Unverifiable Claims", premium: true },
      { id: "misinformation-disinformation", name: "Disinformation Campaigns", premium: true },
      { id: "overreliance", name: "Overreliance", premium: true },
    ],
  },
  {
    title: "Agent-Specific",
    items: [
      { id: "memory-poisoning", name: "Agentic Memory Poisoning", premium: true },
      { id: "rag-poisoning", name: "RAG Poisoning", premium: true },
      { id: "rag-exfiltration", name: "RAG Document Exfiltration", premium: true },
      { id: "tool-discovery", name: "Tool Discovery", premium: true },
      { id: "mcp-vulnerabilities", name: "Model Context Protocol", premium: true },
    ],
  },
  {
    title: "Resource Attacks",
    items: [
      { id: "unbounded-consumption", name: "Unbounded Consumption", premium: true },
      { id: "reasoning-dos", name: "Reasoning DoS", premium: true },
      { id: "divergent-repetition", name: "Divergent Repetition", premium: true },
    ],
  },
  {
    title: "Intellectual Property",
    items: [
      { id: "ip-violations", name: "IP Violations", premium: true },
      { id: "ip-theft", name: "IP Theft", premium: true },
    ],
  },
  {
    title: "Compliance",
    items: [
      { id: "coppa", name: "COPPA Compliance", premium: true },
      { id: "ferpa", name: "FERPA Compliance", premium: true },
    ],
  },
  {
    title: "Specialized Threats",
    items: [
      { id: "cybercrime", name: "Cybercrime", premium: true },
      { id: "wmd-content", name: "WMD Content", premium: true },
      { id: "weapons-content", name: "Weapons Content", premium: true },
      { id: "ied-content", name: "Improvised Explosive Devices", premium: true },
      { id: "drugs", name: "Drug-Related Content", premium: true },
      { id: "methamphetamine", name: "Methamphetamine Content", premium: true },
      { id: "extremism", name: "Extremist Content", premium: true },
      { id: "illegal-activity", name: "Illegal Activity", premium: true },
      { id: "non-violent-crime", name: "Non-Violent Crime", premium: true },
    ],
  },
];

export const ATTACK_CATALOG: Category[] = [
  {
    title: "Single-Turn",
    items: [
      { id: "base64", name: "Base64 Encoding", premium: false },
      { id: "rot13", name: "ROT13 Encoding", premium: false },
      { id: "prompt-injection", name: "Prompt Injection", premium: false },
      { id: "roleplay", name: "Roleplay", premium: false },
      { id: "prompt-probing", name: "Prompt Probing", premium: false },
      { id: "hex", name: "Hex Encoding", premium: true },
      { id: "leetspeak", name: "Leetspeak", premium: true },
      { id: "homoglyph", name: "Homoglyph Encoding", premium: true },
      { id: "math-problem", name: "Math Prompt", premium: true },
      { id: "gray-box", name: "Gray Box", premium: true },
      { id: "multilingual", name: "Multilingual", premium: true },
      { id: "context-poisoning", name: "Context Poisoning", premium: true },
      { id: "goal-redirection", name: "Goal Redirection", premium: true },
      { id: "input-bypass", name: "Input Bypass", premium: true },
      { id: "permission-escalation", name: "Permission Escalation", premium: true },
      { id: "system-override", name: "System Override", premium: true },
      { id: "semantic-manipulation", name: "Semantic Manipulation", premium: true },
      {
        id: "html-indirect-prompt-injection",
        name: "HTML Indirect Prompt Injection",
        premium: true,
      },
      { id: "citation", name: "Citation", premium: true },
      { id: "gcg", name: "GCG (Greedy Coordinate Gradient)", premium: true },
      { id: "likert-jailbreak", name: "Likert-based Jailbreaks", premium: true },
      { id: "best-of-n", name: "Best-of-N", premium: true },
    ],
  },
  {
    title: "Multi-Turn",
    items: [
      {
        id: "social-engineering-prompt-extraction",
        name: "Social Engineering Prompt Extraction",
        premium: true,
      },
      { id: "multi-turn-jailbreak", name: "Multi-turn Jailbreaks", premium: true },
      { id: "goat", name: "GOAT", premium: true },
      { id: "mischievous-user", name: "Mischievous User", premium: true },
      { id: "simba", name: "Simba", premium: true },
      { id: "crescendo", name: "Crescendo", premium: true },
      { id: "linear-jailbreak", name: "Linear Jailbreaking", premium: true },
      { id: "sequential-jailbreak", name: "Sequential Jailbreak", premium: true },
      { id: "bad-likert-judge", name: "Bad Likert Judge", premium: true },
    ],
  },
  {
    title: "Agentic",
    items: [
      { id: "iterative-jailbreak", name: "Iterative Jailbreaks", premium: true },
      { id: "meta-agent-jailbreak", name: "Meta-Agent Jailbreaks", premium: true },
      { id: "hydra", name: "Hydra Multi-turn", premium: true },
      { id: "tree-jailbreak", name: "Tree-based Jailbreaks", premium: true },
      { id: "single-turn-composite", name: "Single Turn Composite", premium: true },
    ],
  },
];

export const FRAMEWORKS = [
  {
    id: "owasp-llm",
    name: "OWASP LLM Top 10",
    description: "OWASP Top 10 for LLM Applications 2025",
  },
  {
    id: "mitre-atlas",
    name: "MITRE ATLAS",
    description: "MITRE Adversarial Threat Landscape for AI Systems",
  },
  { id: "nist-ai", name: "NIST AI RMF", description: "NIST AI Risk Management Framework" },
  { id: "iso-42001", name: "ISO/IEC 42001", description: "ISO/IEC 42001 AI Management System" },
  { id: "eu-ai-act", name: "EU AI Act", description: "European Union Artificial Intelligence Act" },
  { id: "gdpr", name: "GDPR", description: "General Data Protection Regulation" },
  { id: "owasp-api", name: "OWASP API Top 10", description: "OWASP API Security Top 10" },
  {
    id: "basic-security",
    name: "Basic Security",
    description: "Basic security testing for AI agents",
  },
];

// BASIC preset (matches eval_types.go:388-411)
export const BASIC_VULNS = [
  "prompt-extraction",
  "prompt-override",
  "indirect-injection",
  "ascii-smuggling",
  "special-token-injection",
  "pii-direct",
  "pii-api-db",
  "pii-session",
  "cross-session-leakage",
  "privacy-violation",
];
export const BASIC_ATTACKS = ["base64", "rot13", "prompt-injection", "roleplay", "prompt-probing"];

export function totalVulns(): number {
  return VULNERABILITY_CATALOG.reduce((sum, c) => sum + c.items.length, 0);
}
export function totalAttacks(): number {
  return ATTACK_CATALOG.reduce((sum, c) => sum + c.items.length, 0);
}
export function isFreeVuln(id: string): boolean {
  for (const cat of VULNERABILITY_CATALOG) {
    const item = cat.items.find((i) => i.id === id);
    if (item) return !item.premium;
  }
  return false;
}
export function isFreeAttack(id: string): boolean {
  for (const cat of ATTACK_CATALOG) {
    const item = cat.items.find((i) => i.id === id);
    if (item) return !item.premium;
  }
  return false;
}
export function allFreeVulnIds(): string[] {
  return VULNERABILITY_CATALOG.flatMap((c) => c.items.filter((i) => !i.premium).map((i) => i.id));
}
export function allFreeAttackIds(): string[] {
  return ATTACK_CATALOG.flatMap((c) => c.items.filter((i) => !i.premium).map((i) => i.id));
}
