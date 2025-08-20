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
