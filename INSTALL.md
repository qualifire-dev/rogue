# Rogue Installation Guide

This guide explains how to install Rogue using the automated install script.

## Quick Start

The easiest way to install Rogue is to use the provided install script:

```bash
curl -fsSL https://raw.githubusercontent.com/qualifire-dev/rogue-private/main/install.sh | bash
```

Or download and run the script manually:

```bash
# Download the script
curl -fsSL -o install.sh https://raw.githubusercontent.com/qualifire-dev/rogue-private/main/install.sh

# Make it executable
chmod +x install.sh

# Run the installer
./install.sh
```

## What the Install Script Does

The install script automates the entire installation process:

1. **Downloads the latest release** from GitHub releases
2. **Installs to `~/rogue`** by default (customizable)
3. **Updates your shell PATH** automatically for easier use (unless requested otherwise)

## Installation Options

### Basic Installation
```bash
./install.sh
```
Installs to `~/rogue`.

### Custom Installation Directory
```bash
./install.sh -d /opt/rogue
./install.sh --dir /usr/local/rogue
```
Installs to the specified directory.

### Install Specific Version
```bash
# Unix/Linux/macOS
./install.sh -v 1.0.0
./install.sh --version v2.1.0
./install.sh -v latest  # Same as `./install.sh`

# Windows (PowerShell)
.\install.ps1 -Version 1.0.0
.\install.ps1 -Version v2.1.0
.\install.ps1 -Version latest  # Same as .\install.ps1
```
Installs a specific version. If no version is specified, the latest version is used automatically.

### Skip PATH Update
```bash
./install.sh --skip-path
```
Installs the files but doesn't modify your shell configuration.

### Force Installation
```bash
./install.sh -f
```
Overwrites existing installation directory.

### Help
```bash
./install.sh -h
./install.sh --help
```
Shows all available options.

## Manual Installation

If you prefer to install manually or the script doesn't work for your environment:

### 1. Download the Latest Release

Visit [GitHub Releases](https://github.com/qualifire-dev/rogue-private/releases) and download the latest `rogue-release-*.zip` file.

### 2. Extract the Archive

```bash
unzip rogue-release-*.zip
```

### 3. Setup Python Wheel for uvx

```bash
# Find the Python wheel file
ls rogue-*.whl

# Copy it to your installation directory
mkdir -p ~/rogue
cp rogue-*.whl ~/rogue/rogue.whl

# Create a wrapper script
cat > ~/rogue/rogue << 'EOF'
#!/bin/bash
# Rogue wrapper script that uses uvx to run the wheel
uvx "$(dirname "$0")/rogue.whl" "$@"
EOF

chmod +x ~/rogue/rogue
```

### 4. Install Binary

```bash
# Find the appropriate binary for your platform
ls rogue-*

# Copy and rename it
cp rogue-*linux-amd64 ~/rogue/rogue-tui  # Example for Linux x86_64
chmod +x ~/rogue/rogue-tui
```

### 5. Add to PATH (optional)

Add the installation directory to your shell's PATH:

**Bash/Zsh:**
```bash
echo 'export PATH="$HOME/rogue:$PATH"' >> ~/.bashrc
# or
echo 'export PATH="$HOME/rogue:$PATH"' >> ~/.zshrc
```

**Fish:**
```bash
echo 'set -gx PATH $HOME/rogue $PATH' >> ~/.config/fish/config.fish
```

## Supported Platforms

The install script automatically detects and installs the appropriate binary for:

- **Linux**: `x86_64`, `aarch64`
- **macOS**: `x86_64`, `arm64`
- **Windows**: `x86_64`

## Shell Support

The script automatically detects and configures:

- **Bash** (`.bashrc` or `.bash_profile`)
- **Zsh** (`.zshrc`)
- **Fish** (`~/.config/fish/config.fish`)
- **PowerShell** (Windows environment variables)

## Verification

After installation, verify that everything works:

```bash
# Check if commands are available
which rogue
which rogue-tui

# Test the commands
rogue --help
rogue-tui --help
```

## Troubleshooting

### Permission Denied
```bash
chmod +x install.sh
```

### Python Wheel Installation Fails
Ensure you have uvx installed and Python 3.10+:
```bash
python3 --version
uvx --version
```

If uvx is not installed, follow [uv installation guide](https://docs.astral.sh/uv/getting-started/installation/):

### PATH Not Updated
Manually add the installation directory to your shell configuration file.

### Unsupported Platform
The script will show available files and you can manually copy the appropriate one.

## Uninstalling

To uninstall Rogue:

1. **Remove the installation directory:**
   ```bash
   rm -rf ~/rogue
   ```

2. **Remove from PATH** (edit your shell config file):
   - Remove the line: `export PATH="$HOME/rogue:$PATH"`
   - Or comment it out: `# export PATH="$HOME/rogue:$PATH"`


3. **Reload your shell:**
   ```bash
   source ~/.bashrc  # or ~/.zshrc
   ```

4. If you installed Rogue to a custom location, modify steps 1 and 2 accordingly.

## Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.10 or higher
- **Shell**: Bash, Zsh, or Fish
- **Dependencies**: `curl`, `unzip`, `uvx`

## Security Note

The install script downloads and executes code from the internet. Always verify the source and review the script before running it on production systems.

## Support

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/qualifire-dev/rogue-private/issues)
2. Review the troubleshooting section above
3. Create a new issue with details about your environment and the error
