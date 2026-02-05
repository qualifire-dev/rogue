package modelcache

import "time"

// ModelsDevResponse is the top-level response from models.dev/api.json.
// Keys are provider IDs (e.g. "openai", "anthropic").
type ModelsDevResponse map[string]ProviderEntry

// ProviderEntry represents a single provider in the API response.
type ProviderEntry struct {
	ID     string                `json:"id"`
	Name   string                `json:"name"`
	Models map[string]ModelEntry `json:"models"`
}

// ModelEntry represents a single model in the API response.
type ModelEntry struct {
	ID          string     `json:"id"`
	Name        string     `json:"name"`
	Family      string     `json:"family"`
	ReleaseDate string     `json:"release_date"`
	Modalities  Modalities `json:"modalities"`
}

// Modalities describes a model's input/output capabilities.
type Modalities struct {
	Input  []string `json:"input"`
	Output []string `json:"output"`
}

// CachedModels is persisted to disk and kept in memory.
type CachedModels struct {
	FetchedAt time.Time           `json:"fetched_at"`
	Providers map[string][]string `json:"providers"` // provider ID -> sorted model IDs
}
