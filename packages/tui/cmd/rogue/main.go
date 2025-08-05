package main

import (
	"fmt"
	"os"

	"github.com/rogue/tui/internal/commands"
	"github.com/spf13/cobra"
)

var (
	version = "dev"
	commit  = "none"
	date    = "unknown"
)

func main() {
	rootCmd := &cobra.Command{
		Use:   "rogue",
		Short: "Rogue Agent Evaluator TUI",
		Long:  `A modern terminal user interface for the Rogue Agent Evaluator, built with Go and Bubble Tea.`,
		Run: func(cmd *cobra.Command, args []string) {
			// Default to TUI mode
			commands.RunTUI()
		},
	}

	// Global flags
	rootCmd.PersistentFlags().String("server-url", "http://localhost:8000", "Rogue server URL")
	rootCmd.PersistentFlags().String("config", "", "Config file path (default: ~/.rogue/config.toml)")
	rootCmd.PersistentFlags().Bool("debug", false, "Enable debug mode")
	rootCmd.PersistentFlags().Bool("no-color", false, "Disable colors")
	rootCmd.PersistentFlags().String("model", "", "Default LLM model")
	rootCmd.PersistentFlags().String("theme", "auto", "UI theme (dark, light, auto)")

	// Add subcommands
	rootCmd.AddCommand(commands.NewTUICommand())
	rootCmd.AddCommand(commands.NewCICommand())
	rootCmd.AddCommand(commands.NewEvalCommand())
	rootCmd.AddCommand(commands.NewScenariosCommand())
	rootCmd.AddCommand(commands.NewInterviewCommand())
	rootCmd.AddCommand(commands.NewConfigCommand())
	rootCmd.AddCommand(commands.NewVersionCommand(version, commit, date))

	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
