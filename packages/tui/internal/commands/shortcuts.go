package commands

import (
	"fmt"
	"strings"

	tea "github.com/charmbracelet/bubbletea"
)

// KeyBinding represents a keyboard shortcut
type KeyBinding struct {
	Key         string
	Description string
	Handler     KeyHandler
	Context     []CommandContext
}

// KeyHandler is a function that handles key press events
type KeyHandler func() tea.Cmd

// KeyMap contains all keyboard shortcuts
type KeyMap struct {
	bindings map[string]*KeyBinding
}

// NewKeyMap creates a new keyboard shortcut map
func NewKeyMap() *KeyMap {
	km := &KeyMap{
		bindings: make(map[string]*KeyBinding),
	}

	// Register default key bindings
	km.registerDefaultBindings()

	return km
}

// registerDefaultBindings registers the default keyboard shortcuts
func (km *KeyMap) registerDefaultBindings() {
	// Global navigation shortcuts
	km.Register(&KeyBinding{
		Key:         "ctrl+n",
		Description: "New evaluation",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ShortcutExecutedMsg{
					Action: ActionSwitchScreen,
					Data:   map[string]interface{}{"screen": "new_eval"},
				}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "ctrl+e",
		Description: "Evaluations list",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ShortcutExecutedMsg{
					Action: ActionSwitchScreen,
					Data:   map[string]interface{}{"screen": "evaluations"},
				}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "ctrl+i",
		Description: "Interview mode",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ShortcutExecutedMsg{
					Action: ActionStartInterview,
					Data:   map[string]interface{}{},
				}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "ctrl+c",
		Description: "Configuration",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ShortcutExecutedMsg{
					Action: ActionSwitchScreen,
					Data:   map[string]interface{}{"screen": "config"},
				}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "ctrl+s",
		Description: "Scenarios",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ShortcutExecutedMsg{
					Action: ActionSwitchScreen,
					Data:   map[string]interface{}{"screen": "scenarios"},
				}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "ctrl+h",
		Description: "Help",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ShortcutExecutedMsg{
					Action: ActionShowModal,
					Data:   map[string]interface{}{"modal_type": "help"},
				}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "ctrl+q",
		Description: "Quit application",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return tea.Quit
		},
	})

	// Utility shortcuts
	km.Register(&KeyBinding{
		Key:         "ctrl+r",
		Description: "Refresh",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ShortcutExecutedMsg{
					Action: ActionRefresh,
					Data:   map[string]interface{}{},
				}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "ctrl+l",
		Description: "Clear screen",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ShortcutExecutedMsg{
					Action: ActionClear,
					Data:   map[string]interface{}{},
				}
			}
		},
	})

	// Navigation shortcuts
	km.Register(&KeyBinding{
		Key:         "up",
		Description: "Move up",
		Context:     []CommandContext{ContextEvaluations, ContextScenarios},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return NavigationMsg{Direction: "up"}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "down",
		Description: "Move down",
		Context:     []CommandContext{ContextEvaluations, ContextScenarios},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return NavigationMsg{Direction: "down"}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "left",
		Description: "Move left",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return NavigationMsg{Direction: "left"}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "right",
		Description: "Move right",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return NavigationMsg{Direction: "right"}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "enter",
		Description: "Select/Confirm",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ActionMsg{Action: "select"}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "esc",
		Description: "Back/Cancel",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ActionMsg{Action: "back"}
			}
		},
	})

	// Tab navigation
	km.Register(&KeyBinding{
		Key:         "tab",
		Description: "Next field",
		Context:     []CommandContext{ContextNewEval, ContextConfig},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return NavigationMsg{Direction: "next"}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "shift+tab",
		Description: "Previous field",
		Context:     []CommandContext{ContextNewEval, ContextConfig},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return NavigationMsg{Direction: "prev"}
			}
		},
	})

	// Function keys
	km.Register(&KeyBinding{
		Key:         "f1",
		Description: "Help",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ShortcutExecutedMsg{
					Action: ActionShowModal,
					Data:   map[string]interface{}{"modal_type": "help"},
				}
			}
		},
	})

	km.Register(&KeyBinding{
		Key:         "f5",
		Description: "Refresh",
		Context:     []CommandContext{ContextGlobal},
		Handler: func() tea.Cmd {
			return func() tea.Msg {
				return ShortcutExecutedMsg{
					Action: ActionRefresh,
					Data:   map[string]interface{}{},
				}
			}
		},
	})
}

// Register registers a new key binding
func (km *KeyMap) Register(binding *KeyBinding) {
	km.bindings[binding.Key] = binding
}

// GetBinding returns a key binding for the given key
func (km *KeyMap) GetBinding(key string) *KeyBinding {
	return km.bindings[key]
}

// HandleKey handles a key press and returns the appropriate command
func (km *KeyMap) HandleKey(key string, context CommandContext) tea.Cmd {
	binding := km.GetBinding(key)
	if binding == nil {
		return nil
	}

	// Check if binding is available in current context
	for _, bindingContext := range binding.Context {
		if bindingContext == ContextGlobal || bindingContext == context {
			return binding.Handler()
		}
	}

	return nil
}

// GetAvailableBindings returns all key bindings available in the given context
func (km *KeyMap) GetAvailableBindings(context CommandContext) []*KeyBinding {
	var bindings []*KeyBinding

	for _, binding := range km.bindings {
		// Check if binding is available in this context
		for _, bindingContext := range binding.Context {
			if bindingContext == ContextGlobal || bindingContext == context {
				bindings = append(bindings, binding)
				break
			}
		}
	}

	return bindings
}

// GenerateShortcutHelp generates help text for keyboard shortcuts
func (km *KeyMap) GenerateShortcutHelp(context CommandContext) string {
	bindings := km.GetAvailableBindings(context)

	if len(bindings) == 0 {
		return "No keyboard shortcuts available in this context."
	}

	var help []string
	help = append(help, "Keyboard Shortcuts:")
	help = append(help, "")

	for _, binding := range bindings {
		help = append(help, fmt.Sprintf("  %-15s - %s", binding.Key, binding.Description))
	}

	return strings.Join(help, "\n")
}

// Bubble Tea message types for keyboard shortcuts
type (
	ShortcutExecutedMsg struct {
		Action CommandAction
		Data   map[string]interface{}
	}

	NavigationMsg struct {
		Direction string
	}

	ActionMsg struct {
		Action string
	}
)
