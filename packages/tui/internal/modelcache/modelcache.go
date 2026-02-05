package modelcache

import (
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"slices"
	"sort"
	"strings"
	"sync"
	"time"
)

const (
	apiURL       = "https://models.dev/api.json"
	cacheTTL     = 24 * time.Hour
	fetchTimeout = 15 * time.Second
	cacheFile    = "models_cache.json"
)

// targetProviders lists the provider IDs we care about.
var targetProviders = []string{"openai", "anthropic", "google", "openrouter"}

// ModelCacheRefreshedMsg is a Bubble Tea message sent when the background fetch completes.
type ModelCacheRefreshedMsg struct {
	Err    error
	Manual bool // true when triggered by user (Ctrl+R), false on startup
}

// Cache holds the in-memory model cache with thread-safe access.
type Cache struct {
	mu   sync.RWMutex
	data *CachedModels
}

// New creates a new empty Cache.
func New() *Cache {
	return &Cache{}
}

// LoadFromDisk reads the cache file from the config directory.
// It is a no-op if the file does not exist.
func (c *Cache) LoadFromDisk() error {
	path, err := cacheFilePath()
	if err != nil {
		return err
	}

	raw, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}

	var cached CachedModels
	if err := json.Unmarshal(raw, &cached); err != nil {
		return err
	}

	c.mu.Lock()
	c.data = &cached
	c.mu.Unlock()
	return nil
}

// IsStale returns true if the cache is empty or older than cacheTTL.
func (c *Cache) IsStale() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	if c.data == nil {
		return true
	}
	return time.Since(c.data.FetchedAt) > cacheTTL
}

// GetAllProviderModels returns a copy of all cached provider models.
func (c *Cache) GetAllProviderModels() map[string][]string {
	c.mu.RLock()
	defer c.mu.RUnlock()
	if c.data == nil {
		return nil
	}
	result := make(map[string][]string, len(c.data.Providers))
	for k, v := range c.data.Providers {
		cp := make([]string, len(v))
		copy(cp, v)
		result[k] = cp
	}
	return result
}

// Refresh fetches models from the API, filters/sorts them, updates memory, and persists to disk.
func (c *Cache) Refresh() error {
	client := &http.Client{Timeout: fetchTimeout}
	resp, err := client.Get(apiURL)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	var apiResp ModelsDevResponse
	if err := json.NewDecoder(resp.Body).Decode(&apiResp); err != nil {
		return err
	}

	providers := make(map[string][]string, len(targetProviders))
	for _, pid := range targetProviders {
		entry, ok := apiResp[pid]
		if !ok {
			continue
		}
		var models []string
		if pid == "openrouter" {
			models = filterAndSortOpenRouterModels(entry.Models)
		} else {
			models = filterAndSortModels(entry.Models)
		}
		if len(models) > 0 {
			providers[pid] = models
		}
	}

	cached := &CachedModels{
		FetchedAt: time.Now(),
		Providers: providers,
	}

	c.mu.Lock()
	c.data = cached
	c.mu.Unlock()

	return c.saveToDisk(cached)
}

// excludedFamilies are model families that are not useful for chat/evaluation.
var excludedFamilies = map[string]bool{
	"text-embedding": true,
}

// filterAndSortModels filters to chat-capable text models and sorts by release_date desc.
func filterAndSortModels(models map[string]ModelEntry) []string {
	var filtered []ModelEntry
	for _, m := range models {
		if !isChatModel(m) {
			continue
		}
		filtered = append(filtered, m)
	}

	sort.Slice(filtered, func(i, j int) bool {
		if filtered[i].ReleaseDate != filtered[j].ReleaseDate {
			return filtered[i].ReleaseDate > filtered[j].ReleaseDate
		}
		return filtered[i].ID < filtered[j].ID
	})

	ids := make([]string, len(filtered))
	for i, m := range filtered {
		ids[i] = m.ID
	}
	return ids
}

// isChatModel returns true if a model should appear in the LLM picker.
func isChatModel(m ModelEntry) bool {
	// Must produce text output.
	if !hasTextOutput(m) {
		return false
	}

	// Exclude non-chat families (embeddings).
	if excludedFamilies[m.Family] {
		return false
	}

	// Exclude embedding models by name (some have generic family like "gemini").
	if strings.Contains(m.ID, "embedding") {
		return false
	}

	// Exclude codex (code-completion) models — keep the base model only.
	if strings.Contains(m.Family, "codex") {
		return false
	}

	// Exclude deep-research variants.
	if strings.HasSuffix(m.ID, "-deep-research") {
		return false
	}

	// Exclude "-chat-latest" aliases (these are codex pointers).
	if strings.HasSuffix(m.ID, "-chat-latest") {
		return false
	}

	return true
}

// hasTextOutput returns true if the model's output modalities include "text".
func hasTextOutput(m ModelEntry) bool {
	return slices.Contains(m.Modalities.Output, "text")
}

// filterAndSortOpenRouterModels filters openrouter models to text-capable and sorts by release_date desc.
func filterAndSortOpenRouterModels(models map[string]ModelEntry) []string {
	var filtered []ModelEntry
	for _, m := range models {
		if !hasTextOutput(m) {
			continue
		}

		filtered = append(filtered, m)
	}

	sort.Slice(filtered, func(i, j int) bool {
		if filtered[i].ReleaseDate != filtered[j].ReleaseDate {
			return filtered[i].ReleaseDate > filtered[j].ReleaseDate
		}
		return filtered[i].ID < filtered[j].ID
	})

	ids := make([]string, len(filtered))
	for i, m := range filtered {
		ids[i] = m.ID
	}
	return ids
}

// saveToDisk writes the cached data to the config directory.
func (c *Cache) saveToDisk(cached *CachedModels) error {
	path, err := cacheFilePath()
	if err != nil {
		return err
	}

	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}

	raw, err := json.MarshalIndent(cached, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(path, raw, 0o644)
}

// cacheFilePath returns ~/.config/rogue/models_cache.json.
func cacheFilePath() (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(home, ".config", "rogue", cacheFile), nil
}
