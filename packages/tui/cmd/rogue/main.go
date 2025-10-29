package main

import (
	"fmt"
	"os"

	"github.com/rogue/tui/internal/commands"
	"github.com/rogue/tui/internal/shared"
	"github.com/spf13/cobra"
)

func main() {
	rootCmd := &cobra.Command{
		Use:   "rogue",
		Short: "Rogue Agent Evaluator TUI",
		Long:  "A modern terminal user interface for the Rogue Agent Evaluator, built with Go and Bubble Tea.",
		Run: func(cmd *cobra.Command, args []string) {
			// Default to TUI mode
			commands.RunTUI()
		},
	}

	// Global flags
	rootCmd.PersistentFlags().String("server-url", "http://localhost:8000", "Rogue server URL")
	rootCmd.PersistentFlags().Bool("debug", false, "Enable debug mode")
	rootCmd.PersistentFlags().Bool("no-color", false, "Disable colors")
	rootCmd.PersistentFlags().String("model", "", "Default LLM model")
	rootCmd.PersistentFlags().String("theme", "aura", "UI theme")

	// Add version flag to root command
	var showVersion bool
	rootCmd.Flags().BoolVarP(&showVersion, "version", "v", false, "Show version information")

	// Add version command
	versionCmd := &cobra.Command{
		Use:   "version",
		Short: "Show version information",
		Long:  "Display the current version of rogue-tui",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Printf("rogue-tui %s\n", shared.Version)
		},
	}
	rootCmd.AddCommand(versionCmd)

	// Add existing subcommands
	rootCmd.AddCommand(commands.NewTUICommand())

	// Handle version flag on root command before execution
	rootCmd.PreRun = func(cmd *cobra.Command, args []string) {
		if showVersion {
			fmt.Printf("rogue-tui %s\n", shared.Version)
			os.Exit(0)
		}
	}

	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
}
