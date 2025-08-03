package commands

import (
	"fmt"
	"strings"
)

// Parser handles parsing of slash commands
type Parser struct {
	registry *CommandRegistry
}

// NewParser creates a new command parser
func NewParser(registry *CommandRegistry) *Parser {
	return &Parser{
		registry: registry,
	}
}

// ParsedCommand represents a parsed command
type ParsedCommand struct {
	Command *Command
	Args    []string
	Raw     string
}

// ParseError represents a command parsing error
type ParseError struct {
	Type    ParseErrorType
	Message string
	Command string
}

func (e ParseError) Error() string {
	return fmt.Sprintf("parse error: %s", e.Message)
}

// ParseErrorType defines the types of parsing errors
type ParseErrorType string

const (
	ErrorNotCommand     ParseErrorType = "not_command"
	ErrorUnknownCommand ParseErrorType = "unknown_command"
	ErrorInvalidSyntax  ParseErrorType = "invalid_syntax"
)

// Parse parses a command string and returns a ParsedCommand or error
func (p *Parser) Parse(input string) (*ParsedCommand, error) {
	// Trim whitespace
	input = strings.TrimSpace(input)

	// Check if it's a command (starts with /)
	if !strings.HasPrefix(input, "/") {
		return nil, ParseError{
			Type:    ErrorNotCommand,
			Message: "input does not start with /",
		}
	}

	// Remove the leading slash
	input = input[1:]

	// Split into command and arguments
	parts := strings.Fields(input)
	if len(parts) == 0 {
		return nil, ParseError{
			Type:    ErrorInvalidSyntax,
			Message: "empty command",
		}
	}

	commandName := parts[0]
	args := parts[1:]

	// Look up the command
	command := p.registry.GetCommand(commandName)
	if command == nil {
		return nil, ParseError{
			Type:    ErrorUnknownCommand,
			Message: fmt.Sprintf("unknown command: %s", commandName),
			Command: commandName,
		}
	}

	return &ParsedCommand{
		Command: command,
		Args:    args,
		Raw:     "/" + strings.Join(parts, " "),
	}, nil
}

// IsCommand checks if the input string is a slash command
func (p *Parser) IsCommand(input string) bool {
	return strings.HasPrefix(strings.TrimSpace(input), "/")
}

// GetSuggestions returns command suggestions for autocomplete
func (p *Parser) GetSuggestions(input string, context CommandContext) []string {
	// Trim whitespace
	input = strings.TrimSpace(input)

	// Check if it starts with /
	if !strings.HasPrefix(input, "/") {
		return nil
	}

	// Remove the leading slash
	input = input[1:]

	// Split into parts
	parts := strings.Fields(input)

	if len(parts) == 0 {
		// Show all available commands
		commands := p.registry.GetAvailableCommands(context)
		suggestions := make([]string, len(commands))
		for i, cmd := range commands {
			suggestions[i] = "/" + cmd.Name
		}
		return suggestions
	}

	if len(parts) == 1 {
		// Complete command name
		prefix := parts[0]
		commandSuggestions := p.registry.GetCommandSuggestions(prefix, context)

		suggestions := make([]string, len(commandSuggestions))
		for i, cmd := range commandSuggestions {
			suggestions[i] = "/" + cmd
		}
		return suggestions
	}

	// For now, we don't provide argument completion
	return nil
}

// Execute executes a parsed command
func (p *Parser) Execute(parsed *ParsedCommand) (CommandResult, error) {
	return parsed.Command.Handler(parsed.Args)
}

// QuickExecute parses and executes a command in one call
func (p *Parser) QuickExecute(input string, context CommandContext) (CommandResult, error) {
	parsed, err := p.Parse(input)
	if err != nil {
		return CommandResult{}, err
	}

	// Check if command is available in current context
	available := false
	for _, cmdContext := range parsed.Command.Context {
		if cmdContext == ContextGlobal || cmdContext == context {
			available = true
			break
		}
	}

	if !available {
		return CommandResult{}, ParseError{
			Type:    ErrorInvalidSyntax,
			Message: fmt.Sprintf("command '%s' not available in current context", parsed.Command.Name),
			Command: parsed.Command.Name,
		}
	}

	return p.Execute(parsed)
}

// ValidateCommand checks if a command is valid in the given context
func (p *Parser) ValidateCommand(commandName string, context CommandContext) error {
	command := p.registry.GetCommand(commandName)
	if command == nil {
		return ParseError{
			Type:    ErrorUnknownCommand,
			Message: fmt.Sprintf("unknown command: %s", commandName),
			Command: commandName,
		}
	}

	// Check if command is available in current context
	for _, cmdContext := range command.Context {
		if cmdContext == ContextGlobal || cmdContext == context {
			return nil
		}
	}

	return ParseError{
		Type:    ErrorInvalidSyntax,
		Message: fmt.Sprintf("command '%s' not available in current context", commandName),
		Command: commandName,
	}
}

// GetCommandHelp returns help text for a specific command
func (p *Parser) GetCommandHelp(commandName string) (string, error) {
	command := p.registry.GetCommand(commandName)
	if command == nil {
		return "", ParseError{
			Type:    ErrorUnknownCommand,
			Message: fmt.Sprintf("unknown command: %s", commandName),
			Command: commandName,
		}
	}

	var help strings.Builder
	help.WriteString(fmt.Sprintf("Command: %s\n", command.Name))

	if len(command.Aliases) > 0 {
		help.WriteString(fmt.Sprintf("Aliases: %s\n", strings.Join(command.Aliases, ", ")))
	}

	help.WriteString(fmt.Sprintf("Usage: %s\n", command.Usage))
	help.WriteString(fmt.Sprintf("Description: %s\n", command.Description))

	// Show contexts
	contexts := make([]string, len(command.Context))
	for i, ctx := range command.Context {
		contexts[i] = string(ctx)
	}
	help.WriteString(fmt.Sprintf("Available in: %s\n", strings.Join(contexts, ", ")))

	return help.String(), nil
}
