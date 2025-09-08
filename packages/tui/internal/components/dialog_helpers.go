package components

// DialogHelpers provides utility functions for creating common dialogs

// ShowErrorDialog creates an error dialog
func ShowErrorDialog(title, message string) Dialog {
	return Dialog{
		Type:    InfoDialog,
		Title:   title,
		Message: message,
		Buttons: []DialogButton{
			{Label: "OK", Action: "ok", Style: DangerButton},
		},
		Width:       50,
		Height:      10,
		Focused:     true,
		SelectedBtn: 0,
	}
}

// ShowWarningDialog creates a warning dialog
func ShowWarningDialog(title, message string) Dialog {
	return Dialog{
		Type:    ConfirmationDialog,
		Title:   title,
		Message: message,
		Buttons: []DialogButton{
			{Label: "Cancel", Action: "cancel", Style: SecondaryButton},
			{Label: "Continue", Action: "ok", Style: PrimaryButton},
		},
		Width:       50,
		Height:      10,
		Focused:     true,
		SelectedBtn: 1,
	}
}

// ShowDeleteConfirmationDialog creates a delete confirmation dialog
func ShowDeleteConfirmationDialog(itemName string) Dialog {
	return Dialog{
		Type:    ConfirmationDialog,
		Title:   "Confirm Delete",
		Message: "Are you sure you want to delete \"" + itemName + "\"? This action cannot be undone.",
		Buttons: []DialogButton{
			{Label: "Cancel", Action: "cancel", Style: SecondaryButton},
			{Label: "Delete", Action: "delete", Style: DangerButton},
		},
		Width:       60,
		Height:      10,
		Focused:     true,
		SelectedBtn: 0, // Default to Cancel for safety
	}
}

// ShowProgressDialog creates a progress dialog (custom view)
func ShowProgressDialog(title string, progressFunc func() string) Dialog {
	return Dialog{
		Type:       CustomDialog,
		Title:      title,
		CustomView: progressFunc,
		Buttons:    []DialogButton{}, // No buttons for progress dialog
		Width:      50,
		Height:     8,
		Focused:    false, // Progress dialogs are typically not interactive
	}
}

// ShowAboutDialog creates an about dialog
func ShowAboutDialog(appName, version, description string) Dialog {
	aboutText := appName + " " + version + "\n\n" + description

	return Dialog{
		Type:    InfoDialog,
		Title:   "About " + appName,
		Message: aboutText,
		Buttons: []DialogButton{
			{Label: "OK", Action: "ok", Style: PrimaryButton},
		},
		Width:       60,
		Height:      12,
		Focused:     true,
		SelectedBtn: 0,
	}
}
