package main

import (
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/config"
	"github.com/qualifire-dev/rogue-private/packages/tui/internal/tui"
	"github.com/spf13/cobra"
)

var (
	// Global flags
	serverURL  string
	configFile string
	debug      bool
	noColor    bool
	model      string
	theme      string
)

// rootCmd represents the base command when called without any subcommands
var rootCmd = &cobra.Command{
	Use:   "rogue",
	Short: "Rogue Agent Evaluator TUI",
	Long: `Rogue is a terminal user interface for the Rogue Agent Evaluator.
	
It provides an interactive way to:
- Create and manage agent evaluations
- Run live interviews with agents
- Configure scenarios and settings
- Monitor evaluation progress in real-time`,
	RunE: runTUI,
}

// tuiCmd explicitly runs the TUI (same as root)
var tuiCmd = &cobra.Command{
	Use:   "tui",
	Short: "Launch TUI (same as default)",
	Long:  "Launch the terminal user interface for Rogue Agent Evaluator.",
	RunE:  runTUI,
}

// ciCmd runs evaluations in CI/CD mode
var ciCmd = &cobra.Command{
	Use:   "ci",
	Short: "Run evaluation in CI mode",
	Long:  "Run evaluations in continuous integration mode without interactive UI.",
	RunE:  runCI,
}

// evalCmd handles evaluation operations
var evalCmd = &cobra.Command{
	Use:   "eval",
	Short: "Evaluation operations",
	Long:  "Create, list, and manage evaluations.",
}

// scenariosCmd handles scenario operations
var scenariosCmd = &cobra.Command{
	Use:   "scenarios",
	Short: "Scenario management",
	Long:  "Generate, edit, and manage test scenarios.",
}

// interviewCmd starts interview mode
var interviewCmd = &cobra.Command{
	Use:   "interview",
	Short: "Start interview mode",
	Long:  "Start an interactive interview session with an agent.",
	RunE:  runInterview,
}

// configCmd handles configuration
var configCmd = &cobra.Command{
	Use:   "config",
	Short: "Configuration management",
	Long:  "Manage Rogue configuration settings.",
}

// versionCmd shows version information
var versionCmd = &cobra.Command{
	Use:   "version",
	Short: "Show version",
	Long:  "Display version information for Rogue TUI.",
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("rogue v1.0.0")
	},
}

func init() {
	// Global flags
	rootCmd.PersistentFlags().StringVar(&serverURL, "server-url", "http://localhost:8000", "Rogue server URL")
	rootCmd.PersistentFlags().StringVar(&configFile, "config", "", "Config file path (default: ~/.rogue/config.toml)")
	rootCmd.PersistentFlags().BoolVar(&debug, "debug", false, "Enable debug mode")
	rootCmd.PersistentFlags().BoolVar(&noColor, "no-color", false, "Disable colors")
	rootCmd.PersistentFlags().StringVar(&model, "model", "", "Default LLM model")
	rootCmd.PersistentFlags().StringVar(&theme, "theme", "", "UI theme (dark, light, auto)")

	// Add subcommands
	rootCmd.AddCommand(tuiCmd)
	rootCmd.AddCommand(ciCmd)
	rootCmd.AddCommand(evalCmd)
	rootCmd.AddCommand(scenariosCmd)
	rootCmd.AddCommand(interviewCmd)
	rootCmd.AddCommand(configCmd)
	rootCmd.AddCommand(versionCmd)

	// CI command flags
	ciCmd.Flags().String("agent-url", "", "Agent URL to evaluate")
	ciCmd.Flags().String("scenarios", "", "Scenarios file path")
	ciCmd.Flags().String("config-file", "", "Configuration file")
	ciCmd.Flags().String("business-context", "", "Business context for evaluation")
	ciCmd.Flags().String("output", "", "Output file for results")

	// Interview command flags
	interviewCmd.Flags().String("agent-url", "", "Agent URL for interview")

	// Eval subcommands
	evalCmd.AddCommand(&cobra.Command{
		Use:   "list",
		Short: "List all evaluations",
		RunE:  runEvalList,
	})

	evalCmd.AddCommand(&cobra.Command{
		Use:   "show <eval-id>",
		Short: "Show evaluation details",
		Args:  cobra.ExactArgs(1),
		RunE:  runEvalShow,
	})

	evalCmd.AddCommand(&cobra.Command{
		Use:   "cancel <eval-id>",
		Short: "Cancel running evaluation",
		Args:  cobra.ExactArgs(1),
		RunE:  runEvalCancel,
	})

	// Scenarios subcommands
	scenariosCmd.AddCommand(&cobra.Command{
		Use:   "generate",
		Short: "Generate scenarios wizard",
		RunE:  runScenariosGenerate,
	})

	scenariosCmd.AddCommand(&cobra.Command{
		Use:   "list",
		Short: "List all scenarios",
		RunE:  runScenariosList,
	})

	scenariosCmd.AddCommand(&cobra.Command{
		Use:   "edit <scenario-id>",
		Short: "Edit scenario",
		Args:  cobra.ExactArgs(1),
		RunE:  runScenariosEdit,
	})

	// Config subcommands
	configCmd.AddCommand(&cobra.Command{
		Use:   "server",
		Short: "Set server URL",
		RunE:  runConfigServer,
	})

	configCmd.AddCommand(&cobra.Command{
		Use:   "auth",
		Short: "Authentication setup",
		RunE:  runConfigAuth,
	})
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}

// runTUI starts the terminal user interface
func runTUI(cmd *cobra.Command, args []string) error {
	// Load configuration
	cfg, err := loadConfig()
	if err != nil {
		return fmt.Errorf("failed to load configuration: %w", err)
	}

	// Apply command line overrides
	if serverURL != "" {
		cfg.Server.URL = serverURL
	}
	if theme != "" {
		cfg.UI.Theme = theme
	}
	if model != "" {
		cfg.Defaults.JudgeLLM = model
	}

	// Create and run TUI
	model := tui.New(cfg)

	var options []tea.ProgramOption
	options = append(options, tea.WithAltScreen())

	if !noColor {
		options = append(options, tea.WithOutput(os.Stdout))
	}

	if cfg.UI.MouseEnabled {
		options = append(options, tea.WithMouseCellMotion())
	}

	program := tea.NewProgram(model, options...)

	if _, err := program.Run(); err != nil {
		return fmt.Errorf("TUI error: %w", err)
	}

	return nil
}

// runCI runs evaluation in CI mode
func runCI(cmd *cobra.Command, args []string) error {
	fmt.Println("CI mode not yet implemented")
	return nil
}

// runInterview starts interview mode directly
func runInterview(cmd *cobra.Command, args []string) error {
	// Load configuration
	cfg, err := loadConfig()
	if err != nil {
		return fmt.Errorf("failed to load configuration: %w", err)
	}

	// Get agent URL from flag or config
	agentURL, _ := cmd.Flags().GetString("agent-url")
	if agentURL == "" {
		agentURL = cfg.Agent.DefaultURL
	}

	if agentURL == "" {
		return fmt.Errorf("agent URL required (use --agent-url flag or set in config)")
	}

	// Create TUI and start in interview mode
	model := tui.New(cfg)
	// TODO: Set initial screen to interview mode

	program := tea.NewProgram(model, tea.WithAltScreen())

	if _, err := program.Run(); err != nil {
		return fmt.Errorf("interview error: %w", err)
	}

	return nil
}

// runEvalList lists all evaluations
func runEvalList(cmd *cobra.Command, args []string) error {
	fmt.Println("Eval list not yet implemented")
	return nil
}

// runEvalShow shows evaluation details
func runEvalShow(cmd *cobra.Command, args []string) error {
	evalID := args[0]
	fmt.Printf("Showing evaluation %s (not yet implemented)\n", evalID)
	return nil
}

// runEvalCancel cancels an evaluation
func runEvalCancel(cmd *cobra.Command, args []string) error {
	evalID := args[0]
	fmt.Printf("Cancelling evaluation %s (not yet implemented)\n", evalID)
	return nil
}

// runScenariosGenerate runs scenario generation wizard
func runScenariosGenerate(cmd *cobra.Command, args []string) error {
	fmt.Println("Scenarios generate not yet implemented")
	return nil
}

// runScenariosList lists all scenarios
func runScenariosList(cmd *cobra.Command, args []string) error {
	fmt.Println("Scenarios list not yet implemented")
	return nil
}

// runScenariosEdit edits a scenario
func runScenariosEdit(cmd *cobra.Command, args []string) error {
	scenarioID := args[0]
	fmt.Printf("Editing scenario %s (not yet implemented)\n", scenarioID)
	return nil
}

// runConfigServer configures server settings
func runConfigServer(cmd *cobra.Command, args []string) error {
	fmt.Println("Config server not yet implemented")
	return nil
}

// runConfigAuth configures authentication
func runConfigAuth(cmd *cobra.Command, args []string) error {
	fmt.Println("Config auth not yet implemented")
	return nil
}

// loadConfig loads the configuration from file
func loadConfig() (*config.Config, error) {
	if configFile != "" {
		// TODO: Load from specified file
		return config.Load()
	}

	return config.Load()
}
