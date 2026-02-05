package modelcache

import (
	"encoding/json"
	"os"
	"path/filepath"
	"slices"
	"testing"
	"time"
)

func TestFilterAndSortModels(t *testing.T) {
	models := map[string]ModelEntry{
		"new-text": {
			ID:          "new-text",
			Name:        "New Text Model",
			ReleaseDate: "2025-06-01",
			Modalities:  Modalities{Input: []string{"text"}, Output: []string{"text"}},
		},
		"old-text": {
			ID:          "old-text",
			Name:        "Old Text Model",
			ReleaseDate: "2024-01-01",
			Modalities:  Modalities{Input: []string{"text"}, Output: []string{"text"}},
		},
		"image-only": {
			ID:          "image-only",
			Name:        "Image Only Model",
			ReleaseDate: "2025-07-01",
			Modalities:  Modalities{Input: []string{"text"}, Output: []string{"image"}},
		},
		"multi-output": {
			ID:          "multi-output",
			Name:        "Multi Output Model",
			ReleaseDate: "2025-06-01",
			Modalities:  Modalities{Input: []string{"text"}, Output: []string{"text", "image"}},
		},
	}

	result := filterAndSortModels(models)

	// image-only should be excluded
	for _, id := range result {
		if id == "image-only" {
			t.Error("image-only model should have been filtered out")
		}
	}

	// Should have 3 models
	if len(result) != 3 {
		t.Fatalf("expected 3 models, got %d: %v", len(result), result)
	}

	// First two should be from 2025-06-01 (newest), sorted by ID asc
	if result[0] != "multi-output" {
		t.Errorf("expected first model to be multi-output, got %s", result[0])
	}
	if result[1] != "new-text" {
		t.Errorf("expected second model to be new-text, got %s", result[1])
	}
	// Last should be old-text (2024-01-01)
	if result[2] != "old-text" {
		t.Errorf("expected third model to be old-text, got %s", result[2])
	}
}

func TestFilterAndSortModelsEmpty(t *testing.T) {
	models := map[string]ModelEntry{
		"image-only": {
			ID:         "image-only",
			Modalities: Modalities{Output: []string{"image"}},
		},
	}

	result := filterAndSortModels(models)
	if len(result) != 0 {
		t.Errorf("expected 0 models, got %d", len(result))
	}
}

func TestExcludeEmbeddingModels(t *testing.T) {
	models := map[string]ModelEntry{
		"text-embedding-3-large": {
			ID:         "text-embedding-3-large",
			Family:     "text-embedding",
			Modalities: Modalities{Output: []string{"text"}},
		},
		"gpt-4o": {
			ID:         "gpt-4o",
			Family:     "gpt",
			Modalities: Modalities{Output: []string{"text"}},
		},
	}

	result := filterAndSortModels(models)
	if slices.Contains(result, "text-embedding-3-large") {
		t.Error("embedding model should be excluded")
	}
	if !slices.Contains(result, "gpt-4o") {
		t.Error("gpt-4o should be kept")
	}
}

func TestExcludeCodexModels(t *testing.T) {
	models := map[string]ModelEntry{
		"gpt-5": {
			ID:          "gpt-5",
			Family:      "gpt",
			ReleaseDate: "2025-05-05",
			Modalities:  Modalities{Output: []string{"text"}},
		},
		"gpt-5-codex": {
			ID:          "gpt-5-codex",
			Family:      "gpt-codex",
			ReleaseDate: "2025-05-05",
			Modalities:  Modalities{Output: []string{"text"}},
		},
		"gpt-5-chat-latest": {
			ID:          "gpt-5-chat-latest",
			Family:      "gpt-codex",
			ReleaseDate: "2025-05-05",
			Modalities:  Modalities{Output: []string{"text"}},
		},
		"codex-mini-latest": {
			ID:          "codex-mini-latest",
			Family:      "gpt-codex-mini",
			ReleaseDate: "2025-04-01",
			Modalities:  Modalities{Output: []string{"text"}},
		},
	}

	result := filterAndSortModels(models)
	if slices.Contains(result, "gpt-5-codex") {
		t.Error("codex model should be excluded")
	}
	if slices.Contains(result, "gpt-5-chat-latest") {
		t.Error("chat-latest model should be excluded")
	}
	if slices.Contains(result, "codex-mini-latest") {
		t.Error("codex-mini model should be excluded")
	}
	if !slices.Contains(result, "gpt-5") {
		t.Error("gpt-5 should be kept")
	}
}

func TestExcludeDeepResearch(t *testing.T) {
	models := map[string]ModelEntry{
		"o3": {
			ID:         "o3",
			Family:     "o",
			Modalities: Modalities{Output: []string{"text"}},
		},
		"o3-deep-research": {
			ID:         "o3-deep-research",
			Family:     "o",
			Modalities: Modalities{Output: []string{"text"}},
		},
	}

	result := filterAndSortModels(models)
	if slices.Contains(result, "o3-deep-research") {
		t.Error("deep-research model should be excluded")
	}
	if !slices.Contains(result, "o3") {
		t.Error("o3 should be kept")
	}
}

func TestExcludeEmbeddingByName(t *testing.T) {
	models := map[string]ModelEntry{
		"gemini-embedding-001": {
			ID:         "gemini-embedding-001",
			Family:     "gemini",
			Modalities: Modalities{Output: []string{"text"}},
		},
		"gemini-2.5-pro": {
			ID:         "gemini-2.5-pro",
			Family:     "gemini",
			Modalities: Modalities{Output: []string{"text"}},
		},
	}

	result := filterAndSortModels(models)
	if slices.Contains(result, "gemini-embedding-001") {
		t.Error("embedding model should be excluded by name")
	}
	if !slices.Contains(result, "gemini-2.5-pro") {
		t.Error("gemini-2.5-pro should be kept")
	}
}

func TestIsStale(t *testing.T) {
	c := New()

	// Empty cache is stale
	if !c.IsStale() {
		t.Error("empty cache should be stale")
	}

	// Fresh cache is not stale
	c.data = &CachedModels{
		FetchedAt: time.Now(),
		Providers: map[string][]string{"openai": {"gpt-4"}},
	}
	if c.IsStale() {
		t.Error("fresh cache should not be stale")
	}

	// Expired cache is stale
	c.data = &CachedModels{
		FetchedAt: time.Now().Add(-25 * time.Hour),
		Providers: map[string][]string{"openai": {"gpt-4"}},
	}
	if !c.IsStale() {
		t.Error("expired cache should be stale")
	}
}

func TestLoadAndSaveRoundTrip(t *testing.T) {
	// Use a temp directory for the cache file
	tmpDir := t.TempDir()
	cacheDir := filepath.Join(tmpDir, ".config", "rogue")
	if err := os.MkdirAll(cacheDir, 0o755); err != nil {
		t.Fatal(err)
	}

	cachePath := filepath.Join(cacheDir, cacheFile)

	// Write test data
	cached := &CachedModels{
		FetchedAt: time.Date(2025, 6, 1, 12, 0, 0, 0, time.UTC),
		Providers: map[string][]string{
			"openai":    {"gpt-4o", "gpt-4o-mini"},
			"anthropic": {"claude-sonnet-4-5"},
		},
	}

	raw, err := json.MarshalIndent(cached, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(cachePath, raw, 0o644); err != nil {
		t.Fatal(err)
	}

	// Load it back
	c := New()

	// Read the file directly to simulate LoadFromDisk
	data, err := os.ReadFile(cachePath)
	if err != nil {
		t.Fatal(err)
	}
	var loaded CachedModels
	if err := json.Unmarshal(data, &loaded); err != nil {
		t.Fatal(err)
	}
	c.data = &loaded

	// Verify data
	models := c.GetAllProviderModels()
	if models == nil {
		t.Fatal("expected non-nil models")
	}

	openai := models["openai"]
	if len(openai) != 2 || openai[0] != "gpt-4o" || openai[1] != "gpt-4o-mini" {
		t.Errorf("unexpected openai models: %v", openai)
	}

	anthropic := models["anthropic"]
	if len(anthropic) != 1 || anthropic[0] != "claude-sonnet-4-5" {
		t.Errorf("unexpected anthropic models: %v", anthropic)
	}
}

func TestGetAllProviderModelsReturnsCopy(t *testing.T) {
	c := New()
	c.data = &CachedModels{
		FetchedAt: time.Now(),
		Providers: map[string][]string{
			"openai": {"gpt-4o"},
		},
	}

	models := c.GetAllProviderModels()
	// Mutating the copy should not affect the original
	models["openai"][0] = "modified"

	original := c.GetAllProviderModels()
	if original["openai"][0] != "gpt-4o" {
		t.Error("GetAllProviderModels should return a copy, not a reference")
	}
}

func TestHasTextOutput(t *testing.T) {
	tests := []struct {
		name     string
		model    ModelEntry
		expected bool
	}{
		{
			name:     "text output",
			model:    ModelEntry{Modalities: Modalities{Output: []string{"text"}}},
			expected: true,
		},
		{
			name:     "multi output with text",
			model:    ModelEntry{Modalities: Modalities{Output: []string{"image", "text"}}},
			expected: true,
		},
		{
			name:     "image only",
			model:    ModelEntry{Modalities: Modalities{Output: []string{"image"}}},
			expected: false,
		},
		{
			name:     "empty output",
			model:    ModelEntry{Modalities: Modalities{Output: []string{}}},
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := hasTextOutput(tt.model); got != tt.expected {
				t.Errorf("hasTextOutput() = %v, want %v", got, tt.expected)
			}
		})
	}
}
