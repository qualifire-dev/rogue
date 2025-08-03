package commands

import (
	"fmt"
	"strings"
)

// Command represents a slash command that can be executed in the TUI
type Command struct {
	Name        string
	Aliases     []string
	Description string
	Usage       string
	Handler     CommandHandler
	Context     []CommandContext // Which screens this command is available in
}

// CommandHandler is a function that handles command execution
type CommandHandler func(args []string) (CommandResult, error)

// CommandResult represents the result of executing a command
type CommandResult struct {
	Action  CommandAction
	Message string
	Data    map[string]interface{}
}

// CommandAction defines what action should be taken after command execution
type CommandAction string

const (
	ActionNone            CommandAction = "none"
	ActionSwitchScreen    CommandAction = "switch_screen"
	ActionRefresh         CommandAction = "refresh"
	ActionShowModal       CommandAction = "show_modal"
	ActionHideModal       CommandAction = "hide_modal"
	ActionStartEvaluation CommandAction = "start_evaluation"
	ActionStartInterview  CommandAction = "start_interview"
	ActionQuit            CommandAction = "quit"
	ActionClear           CommandAction = "clear"
	ActionExport          CommandAction = "export"
	ActionImport          CommandAction = "import"
)

// CommandContext defines where a command can be used
type CommandContext string

const (
	ContextGlobal      CommandContext = "global"
	ContextDashboard   CommandContext = "dashboard"
	ContextEvaluations CommandContext = "evaluations"
	ContextEvalDetail  CommandContext = "eval_detail"
	ContextInterview   CommandContext = "interview"
	ContextConfig      CommandContext = "config"
	ContextScenarios   CommandContext = "scenarios"
	ContextNewEval     CommandContext = "new_eval"
)

// CommandRegistry manages all available commands
type CommandRegistry struct {
	commands map[string]*Command
	aliases  map[string]string
}

// NewCommandRegistry creates a new command registry with built-in commands
func NewCommandRegistry() *CommandRegistry {
	registry := &CommandRegistry{
		commands: make(map[string]*Command),
		aliases:  make(map[string]string),
	}

	// Register built-in commands
	registry.registerBuiltinCommands()

	return registry
}

// registerBuiltinCommands registers all the built-in slash commands
func (r *CommandRegistry) registerBuiltinCommands() {
	// Navigation commands
	r.Register(&Command{
		Name:        "new",
		Aliases:     []string{"n"},
		Description: "Start new evaluation wizard",
		Usage:       "/new",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			return CommandResult{
				Action:  ActionSwitchScreen,
				Message: "Starting new evaluation wizard",
				Data:    map[string]interface{}{"screen": "new_eval"},
			}, nil
		},
	})

	r.Register(&Command{
		Name:        "eval",
		Aliases:     []string{"evaluations", "e"},
		Description: "List evaluations",
		Usage:       "/eval",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			return CommandResult{
				Action:  ActionSwitchScreen,
				Message: "Switching to evaluations",
				Data:    map[string]interface{}{"screen": "evaluations"},
			}, nil
		},
	})

	r.Register(&Command{
		Name:        "interview",
		Aliases:     []string{"i"},
		Description: "Start interview mode",
		Usage:       "/interview [agent-url]",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			var agentURL string
			if len(args) > 0 {
				agentURL = args[0]
			}
			return CommandResult{
				Action:  ActionStartInterview,
				Message: "Starting interview mode",
				Data:    map[string]interface{}{"agent_url": agentURL},
			}, nil
		},
	})

	r.Register(&Command{
		Name:        "configure",
		Aliases:     []string{"config", "settings", "c"},
		Description: "Open configuration settings",
		Usage:       "/configure",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			return CommandResult{
				Action:  ActionSwitchScreen,
				Message: "Opening configuration",
				Data:    map[string]interface{}{"screen": "config"},
			}, nil
		},
	})

	r.Register(&Command{
		Name:        "scenarios",
		Aliases:     []string{"s"},
		Description: "Manage scenarios",
		Usage:       "/scenarios",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			return CommandResult{
				Action:  ActionSwitchScreen,
				Message: "Switching to scenarios",
				Data:    map[string]interface{}{"screen": "scenarios"},
			}, nil
		},
	})

	// Utility commands
	r.Register(&Command{
		Name:        "help",
		Aliases:     []string{"h", "?"},
		Description: "Show help and commands",
		Usage:       "/help [command]",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			var helpText string
			if len(args) > 0 {
				// Show help for specific command
				if cmd := r.GetCommand(args[0]); cmd != nil {
					helpText = fmt.Sprintf("Command: %s\nUsage: %s\nDescription: %s",
						cmd.Name, cmd.Usage, cmd.Description)
				} else {
					helpText = fmt.Sprintf("Unknown command: %s", args[0])
				}
			} else {
				// Show general help
				helpText = r.GenerateHelpText(ContextGlobal)
			}

			return CommandResult{
				Action:  ActionShowModal,
				Message: helpText,
				Data:    map[string]interface{}{"modal_type": "help"},
			}, nil
		},
	})

	r.Register(&Command{
		Name:        "quit",
		Aliases:     []string{"q", "exit"},
		Description: "Exit application",
		Usage:       "/quit",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			return CommandResult{
				Action:  ActionQuit,
				Message: "Goodbye!",
			}, nil
		},
	})

	r.Register(&Command{
		Name:        "clear",
		Description: "Clear current screen",
		Usage:       "/clear",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			return CommandResult{
				Action:  ActionClear,
				Message: "Screen cleared",
			}, nil
		},
	})

	r.Register(&Command{
		Name:        "refresh",
		Aliases:     []string{"r"},
		Description: "Refresh current view",
		Usage:       "/refresh",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			return CommandResult{
				Action:  ActionRefresh,
				Message: "Refreshing view",
			}, nil
		},
	})

	r.Register(&Command{
		Name:        "export",
		Description: "Export current data",
		Usage:       "/export [format]",
		Context:     []CommandContext{ContextEvaluations, ContextEvalDetail, ContextInterview},
		Handler: func(args []string) (CommandResult, error) {
			format := "json"
			if len(args) > 0 {
				format = args[0]
			}
			return CommandResult{
				Action:  ActionExport,
				Message: fmt.Sprintf("Exporting data as %s", format),
				Data:    map[string]interface{}{"format": format},
			}, nil
		},
	})

	r.Register(&Command{
		Name:        "import",
		Description: "Import configuration or scenarios",
		Usage:       "/import [file]",
		Context:     []CommandContext{ContextConfig, ContextScenarios},
		Handler: func(args []string) (CommandResult, error) {
			var file string
			if len(args) > 0 {
				file = args[0]
			}
			return CommandResult{
				Action:  ActionImport,
				Message: "Importing data",
				Data:    map[string]interface{}{"file": file},
			}, nil
		},
	})

	// Theme commands
	r.Register(&Command{
		Name:        "themes",
		Aliases:     []string{"theme"},
		Description: "Switch between themes",
		Usage:       "/themes [dark|light|auto]",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			var theme string
			if len(args) > 0 {
				theme = args[0]
			}
			return CommandResult{
				Action:  ActionShowModal,
				Message: "Theme selection",
				Data:    map[string]interface{}{"modal_type": "theme", "theme": theme},
			}, nil
		},
	})

	r.Register(&Command{
		Name:        "models",
		Description: "List and select LLM models",
		Usage:       "/models",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			return CommandResult{
				Action:  ActionShowModal,
				Message: "Model selection",
				Data:    map[string]interface{}{"modal_type": "models"},
			}, nil
		},
	})

	// Server commands
	r.Register(&Command{
		Name:        "server",
		Description: "Configure server connection",
		Usage:       "/server [url]",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			var url string
			if len(args) > 0 {
				url = args[0]
			}
			return CommandResult{
				Action:  ActionShowModal,
				Message: "Server configuration",
				Data:    map[string]interface{}{"modal_type": "server", "url": url},
			}, nil
		},
	})

	r.Register(&Command{
		Name:        "auth",
		Description: "Manage API keys and authentication",
		Usage:       "/auth",
		Context:     []CommandContext{ContextGlobal},
		Handler: func(args []string) (CommandResult, error) {
			return CommandResult{
				Action:  ActionShowModal,
				Message: "Authentication management",
				Data:    map[string]interface{}{"modal_type": "auth"},
			}, nil
		},
	})
}

// Register registers a new command
func (r *CommandRegistry) Register(cmd *Command) {
	r.commands[cmd.Name] = cmd

	// Register aliases
	for _, alias := range cmd.Aliases {
		r.aliases[alias] = cmd.Name
	}
}

// GetCommand returns a command by name or alias
func (r *CommandRegistry) GetCommand(name string) *Command {
	// Try direct lookup first
	if cmd, exists := r.commands[name]; exists {
		return cmd
	}

	// Try alias lookup
	if realName, exists := r.aliases[name]; exists {
		return r.commands[realName]
	}

	return nil
}

// GetAvailableCommands returns all commands available in the given context
func (r *CommandRegistry) GetAvailableCommands(context CommandContext) []*Command {
	var commands []*Command

	for _, cmd := range r.commands {
		// Check if command is available in this context
		for _, cmdContext := range cmd.Context {
			if cmdContext == ContextGlobal || cmdContext == context {
				commands = append(commands, cmd)
				break
			}
		}
	}

	return commands
}

// GenerateHelpText generates help text for the given context
func (r *CommandRegistry) GenerateHelpText(context CommandContext) string {
	commands := r.GetAvailableCommands(context)

	var help strings.Builder
	help.WriteString("Available commands:\n\n")

	for _, cmd := range commands {
		aliases := ""
		if len(cmd.Aliases) > 0 {
			aliases = " (" + strings.Join(cmd.Aliases, ", ") + ")"
		}

		help.WriteString(fmt.Sprintf("  %-15s%s - %s\n",
			cmd.Usage, aliases, cmd.Description))
	}

	return help.String()
}

// GetCommandSuggestions returns command suggestions for autocomplete
func (r *CommandRegistry) GetCommandSuggestions(prefix string, context CommandContext) []string {
	var suggestions []string
	commands := r.GetAvailableCommands(context)

	for _, cmd := range commands {
		// Check command name
		if strings.HasPrefix(cmd.Name, prefix) {
			suggestions = append(suggestions, cmd.Name)
		}

		// Check aliases
		for _, alias := range cmd.Aliases {
			if strings.HasPrefix(alias, prefix) {
				suggestions = append(suggestions, alias)
			}
		}
	}

	return suggestions
}
