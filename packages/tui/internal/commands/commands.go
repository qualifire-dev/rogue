package commands

import (
	"fmt"

	"github.com/rogue/tui/internal/tui"
	"github.com/spf13/cobra"
)

// RunTUI starts the TUI application
func RunTUI() {
	app := tui.NewApp()
	if err := app.Run(); err != nil {
		fmt.Printf("Error running TUI: %v\n", err)
	}
}

// NewTUICommand creates the tui subcommand
func NewTUICommand() *cobra.Command {
	return &cobra.Command{
		Use:   "tui",
		Short: "Launch the terminal user interface",
		Run: func(cmd *cobra.Command, args []string) {
			RunTUI()
		},
	}
}

// NewCICommand creates the ci subcommand
func NewCICommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "ci",
		Short: "Run in CI/CD mode",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("CI mode not implemented yet")
		},
	}
	cmd.Flags().String("agent-url", "", "Agent URL")
	cmd.Flags().String("scenarios", "", "Scenarios file")
	return cmd
}

// NewEvalCommand creates the eval subcommand
func NewEvalCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "eval",
		Short: "Evaluation management",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "list",
		Short: "List all evaluations",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Listing evaluations...")
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "show [eval-id]",
		Short: "Show evaluation details",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Printf("Showing evaluation: %s\n", args[0])
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "cancel [eval-id]",
		Short: "Cancel running evaluation",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Printf("Cancelling evaluation: %s\n", args[0])
		},
	})

	return cmd
}

// NewScenariosCommand creates the scenarios subcommand
func NewScenariosCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "scenarios",
		Short: "Scenario management",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "list",
		Short: "List all scenarios",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Listing scenarios...")
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "generate",
		Short: "Generate scenarios wizard",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Starting scenario generation wizard...")
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "edit [scenario-id]",
		Short: "Edit scenario",
		Args:  cobra.ExactArgs(1),
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Printf("Editing scenario: %s\n", args[0])
		},
	})

	return cmd
}

// NewInterviewCommand creates the interview subcommand
func NewInterviewCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "interview",
		Short: "Start interview mode",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Starting interview mode...")
		},
	}
	cmd.Flags().String("agent-url", "", "Agent URL")
	return cmd
}

// NewConfigCommand creates the config subcommand
func NewConfigCommand() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "config",
		Short: "Configuration management",
	}

	cmd.AddCommand(&cobra.Command{
		Use:   "server",
		Short: "Set server URL",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Configuring server...")
		},
	})

	cmd.AddCommand(&cobra.Command{
		Use:   "auth",
		Short: "Authentication setup",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Println("Setting up authentication...")
		},
	})

	return cmd
}

// NewVersionCommand creates the version subcommand
func NewVersionCommand(version, commit, date string) *cobra.Command {
	return &cobra.Command{
		Use:   "version",
		Short: "Show version information",
		Run: func(cmd *cobra.Command, args []string) {
			fmt.Printf("Rogue TUI %s\n", version)
			fmt.Printf("Commit: %s\n", commit)
			fmt.Printf("Built: %s\n", date)
		},
	}
}
