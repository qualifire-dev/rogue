# Red Team Configuration Persistence

## Overview

The TUI now automatically saves and loads red team configuration from a `.rogue/redteam.yaml` file in your project directory. This allows you to:

- Persist your vulnerability and attack selections between sessions
- Version control your red team testing configuration
- Share configurations across team members
- Maintain consistent testing setups

## Configuration File Location

The configuration file is located at:
```
<project-root>/.rogue/redteam.yaml
```

The TUI will automatically:
1. Search upward from the current working directory to find an existing `.rogue/` folder
2. Fall back to creating `.rogue/redteam.yaml` in the current working directory

## Configuration Format

The configuration is stored in YAML format:

```yaml
scan_type: custom                        # "basic", "full", or "custom"
vulnerabilities:                         # List of selected vulnerability IDs
  - prompt-extraction
  - sql-injection
  - excessive-agency
attacks:                                 # List of selected attack IDs
  - base64
  - prompt-probing
  - social-engineering-prompt-extraction
frameworks:                              # Optional: selected frameworks
  - owasp-llm
attacks_per_vulnerability: 5             # Number of attacks per vulnerability (1-10)
qualifire_api_key: your-api-key-here    # Optional: Qualifire API key
category_expanded:                       # UI state: which categories are expanded
  Content Safety: true
  Prompt Security: true
```

## Automatic Save Behavior

The configuration is **automatically saved** whenever you:

- Toggle vulnerability or attack selection (space bar)
- Change scan type (keys 1, 2, or 3)
- Select/deselect all items in a category (keys 'a' or 'n')
- Apply a framework selection (key 'f' then Enter)
- Change attacks per vulnerability (keys + or -)
- Set or update the Qualifire API key (key 'q')

No manual save action is required!

## Automatic Load Behavior

The configuration is **automatically loaded** when:

- You navigate to the Red Team Configuration screen
- The TUI initializes the red team config state

If no configuration file exists, default values are used:
- Scan type: `basic`
- Attacks per vulnerability: `3`
- No vulnerabilities or attacks selected (basic preset will be empty initially)

## Usage Examples

### Scenario 1: First-time Setup

1. Navigate to Red Team Configuration screen
2. Select your vulnerabilities and attacks
3. Configuration is auto-saved to `.rogue/redteam.yaml`
4. Next time you open the TUI, your selections are restored

### Scenario 2: Version Control

Add `.rogue/redteam.yaml` to your repository:

```bash
git add .rogue/redteam.yaml
git commit -m "Add red team testing configuration"
```

Now team members will have the same testing configuration.

### Scenario 3: Multiple Projects

Each project directory can have its own `.rogue/redteam.yaml`:

```
project-a/.rogue/redteam.yaml  # Configuration for project A
project-b/.rogue/redteam.yaml  # Configuration for project B
```

Navigate to different project directories, and the TUI will use the appropriate configuration.

### Scenario 4: Manual Editing

You can manually edit `.rogue/redteam.yaml`:

```yaml
scan_type: custom
vulnerabilities:
  - prompt-extraction
  - pii-direct
attacks:
  - social-engineering-prompt-extraction
  - prompt-probing
attacks_per_vulnerability: 3
```

Save the file, and the TUI will load these settings next time.

## API Reference

### Functions

#### `SaveRedTeamConfig(state *RedTeamConfigState) error`
Saves the current red team configuration to `.rogue/redteam.yaml`.

#### `LoadRedTeamConfig(state *RedTeamConfigState) error`
Loads the red team configuration from `.rogue/redteam.yaml` into the provided state.

#### `GetRedTeamConfigPath() string`
Returns the path where the configuration file is (or will be) saved.

### Called Automatically By

- `NewRedTeamConfigState()` - Loads config on initialization
- `autoSave()` - Called after any state-changing operation in the controller

## Notes

- The `.rogue/` directory is automatically created if it doesn't exist
- Errors during save are silently ignored (won't crash the TUI)
- If a config file is malformed, defaults are used instead
- The API key is stored in plain text - use environment variables for sensitive deployments
- Category expansion state (UI fold/unfold) is also persisted for convenience
