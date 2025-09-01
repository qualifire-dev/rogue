#!/bin/bash

# Rogue Install Script
# This script downloads and installs the latest release of Rogue

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
INSTALL_DIR="$HOME/rogue"
SKIP_PATH_UPDATE=false
FORCE_INSTALL=false
VERSION=""

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1" >&2
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" >&2
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Function to show usage
show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Options:
    -d, --dir DIR          Installation directory (default: ~/rogue)
    --skip-path            Skip PATH update
    -f, --force            Force installation even if directory exists
    -v, --version VER      Install specific version (e.g., v1.0.0, 1.0.0, or 'latest')
    -h, --help             Show this help message

Examples:
    $0                      # Install to ~/rogue
    $0 -d /opt/rogue       # Install to /opt/rogue
    $0 --skip-path         # Install without updating PATH
    $0 -f                  # Force installation
    $0 -v 1.0.0            # Install version v1.0.0
    $0 --version v2.1.0    # Install version v2.1.0
    $0 -v latest           # Install latest version (explicit)

EOF
}

# Function to detect platform and architecture
detect_platform() {
    local os
    local arch
    
    # Detect OS
    case "$(uname -s)" in
        Linux*)     os="linux" ;;
        Darwin*)    os="darwin" ;;
        CYGWIN*)   os="windows" ;;
        MINGW*)    os="windows" ;;
        MSYS*)     os="windows" ;;
        *)         os="unknown" ;;
    esac
    
    # Detect architecture
    case "$(uname -m)" in
        x86_64)    arch="amd64" ;;
        aarch64)   arch="arm64" ;;
        arm64)     arch="arm64" ;;
        *)         arch="unknown" ;;
    esac
    
    echo "${os}-${arch}"
}

# Function to detect shell type
detect_shell() {
    local shell_name
    if [ -n "$ZSH_VERSION" ]; then
        shell_name="zsh"
    elif [ -n "$BASH_VERSION" ]; then
        shell_name="bash"
    elif [ -n "$FISH_VERSION" ]; then
        shell_name="fish"
    else
        shell_name="unknown"
    fi
    echo "$shell_name"
}

# Function to get shell config file
get_shell_config() {
    local shell_type="$1"
    local home="$HOME"
    
    case "$shell_type" in
        "zsh")
            echo "$home/.zshrc"
            ;;
        "bash")
            if [ -f "$home/.bash_profile" ]; then
                echo "$home/.bash_profile"
            else
                echo "$home/.bashrc"
            fi
            ;;
        "fish")
            echo "$home/.config/fish/config.fish"
            ;;
        *)
            echo ""
            ;;
    esac
}

# Function to check if path is already in PATH
is_path_in_path() {
    local path_to_check="$1"
    local shell_type="$2"
    
    case "$shell_type" in
        "fish")
            fish -c "contains $path_to_check \$PATH" 2>/dev/null
            return $?
            ;;
        *)
            # Use regex with path separator to avoid substring matches
            echo "$PATH" | grep -q ":$path_to_check:" || echo "$PATH" | grep -q "^$path_to_check:" || echo "$PATH" | grep -q ":$path_to_check$" || echo "$PATH" | grep -q "^$path_to_check$"
            return $?
            ;;
    esac
}

# Function to add to PATH
add_to_path() {
    local install_dir="$1"
    local shell_type="$2"
    local config_file="$3"
    
    if [ -z "$config_file" ]; then
        print_warning "Could not determine shell config file for $shell_type"
        return 1
    fi
    
    # Don't create config file if it doesn't exist
    if [ ! -f "$config_file" ]; then
        print_warning "Shell config file $config_file does not exist"
        print_status "Please run this command manually to add to PATH:"
        echo "export PATH=\"$install_dir:\$PATH\""
        return 1
    fi
    
    # Check if already added (look for our specific comment and export line)
    if grep -q "# Rogue - Added by install script" "$config_file" 2>/dev/null && grep -q "export PATH.*$install_dir" "$config_file" 2>/dev/null; then
        print_status "PATH already configured in $config_file"
        print_status "Please restart your terminal or run 'source $config_file' to apply changes"
        return 0
    fi
    
    # Add to PATH
    echo "" >> "$config_file"
    echo "# Rogue - Added by install script" >> "$config_file"
    echo "export PATH=\"$install_dir:\$PATH\"" >> "$config_file"
    
    print_success "Added $install_dir to PATH in $config_file"
    print_warning "Please restart your terminal or run 'source $config_file' to apply changes"
}

# Function to download release
download_release() {
    local temp_dir="$1"
    local version="$2"
    local repo="qualifire-dev/rogue-private"
    
    local release_info
    local download_url
    
    # Set version to latest if not specified
    if [ -z "$version" ] || [ "$version" = "latest" ]; then
        version="latest"
    else
        # Ensure version has 'v' prefix
        if [[ "$version" != v* ]]; then
            version="v$version"
        fi
    fi

    # Fetch release information
    if [ "$version" = "latest" ]; then
        print_status "Fetching latest release information..."
        release_info=$(curl -s "https://api.github.com/repos/$repo/releases/latest" --header "Authorization: Bearer $GITHUB_TOKEN" 2>/dev/null)
    else
        print_status "Fetching release information for version $version..."
        release_info=$(curl -s "https://api.github.com/repos/$repo/releases/tags/$version" --header "Authorization: Bearer $GITHUB_TOKEN" 2>/dev/null)
    fi
    
    if [ $? -ne 0 ]; then
        print_error "Failed to fetch release information for $version"
        return 1
    fi
    
    # Extract the first asset "url" field from the assets array (not the release url)
    asset_url=$(echo "$release_info" | awk '/"assets": \[/,/\]/' | grep -o '"url": *"[^"]*"' | head -n 1 | sed 's/"url": *"\([^"]*\)"/\1/')

    if [ -z "$asset_url" ]; then
        print_error "Failed to parse release information for $version - no .zip asset URL found"
        print_error "Available assets:"
        echo "$release_info" | grep -o '"name": *"[^"]*"' | sed 's/.*"name": *"\([^"]*\)"/  - \1/' || true
        return 1
    fi
    
    # For latest version, also extract and update the tag name
    if [ "$version" = "latest" ]; then
        local tag_name
        tag_name=$(echo "$release_info" | grep -o '"tag_name": *"[^"]*"' | head -n 1 | sed 's/.*"tag_name": *"\([^"]*\)"/\1/')
        
        if [ -n "$tag_name" ]; then
            version="$tag_name"
            print_status "Latest release: $version"
        else
            print_warning "Could not parse tag name from latest release, continuing with 'latest'"
            print_status "Latest release: latest"
        fi
    else
        print_status "Found release: $version"
    fi
    
    print_status "Downloading release archive..."
    
    # Download the release
    local archive_name="rogue-release-${version}.zip"
    local archive_path="$temp_dir/$archive_name"
    
    if ! curl -L -o "$archive_path" --header "Accept: application/octet-stream" --header "Authorization: Bearer $GITHUB_TOKEN" "$asset_url"; then
        print_error "Failed to download release archive"
        return 1
    fi
    
    # Validate downloaded file is a valid zip archive
    print_status "Validating downloaded archive..."
    if ! unzip -t "$archive_path" >/dev/null 2>&1; then
        print_error "Downloaded file is not a valid zip archive"
        print_error "File size: $(ls -lh "$archive_path" | awk '{print $5}')"
        print_error "File type: $(file "$archive_path")"
        rm -f "$archive_path"
        return 1
    fi
    
    print_success "Downloaded release archive: $archive_name"
    echo "$archive_path"
}

# Function to extract and install files
extract_and_install() {
    local archive_path="$1"
    local install_dir="$2"
    local platform="$3"
    
    print_status "Extracting release archive..."
    
    # Create temporary extraction directory
    local temp_extract_dir
    temp_extract_dir=$(mktemp -d)
    
    # Extract the archive
    if ! unzip -q "$archive_path" -d "$temp_extract_dir"; then
        print_error "Failed to extract release archive"
        rm -rf "$temp_extract_dir"
        return 1
    fi
    
    # Find and extract the Python wheel
    local wheel_file
    wheel_file=$(find "$temp_extract_dir" -name "rogue-*.whl" | head -n 1)
    
    if [ -z "$wheel_file" ]; then
        print_error "No Python wheel found in release"
        rm -rf "$temp_extract_dir"
        return 1
    fi
    
    print_status "Found Python wheel: $(basename "$wheel_file")"
    
    # Find the appropriate binary for the current platform
    local binary_pattern="rogue-*${platform}*"
    local binary_file
    binary_file=$(find "$temp_extract_dir" -name "$binary_pattern" | head -n 1)
    
    if [ -z "$binary_file" ]; then
        print_warning "No binary found for platform $platform"
        print_status "Available files:"
        find "$temp_extract_dir" -name "rogue-*" -exec basename {} \;
    else
        print_status "Found binary: $(basename "$binary_file")"
    fi
    
    # Create installation directory
    mkdir -p "$install_dir"
    
    # Store the wheel file for uvx usage
    if [ -n "$wheel_file" ]; then
        print_status "Setting up Python wheel for uvx..."
        
        # Clean up any previous rogue wheels in the installation directory
        print_status "Cleaning up any previous rogue wheels..."
        find "$install_dir" -name "rogue-*.whl" -delete 2>/dev/null || true
        
        # Use the original wheel filename to preserve version information
        local wheel_filename
        wheel_filename=$(basename "$wheel_file")
        local wheel_dest="$install_dir/$wheel_filename"
        
        if ! cp "$wheel_file" "$wheel_dest"; then
            print_error "Failed to copy wheel file"
            rm -rf "$temp_extract_dir"
            return 1
        fi
        
        # Install the wheel and its dependencies using uv
        print_status "Installing wheel and dependencies with uv..."
        local wheel_path="$install_dir/$wheel_filename"
        
        # Create a virtual environment in the install directory
        if ! uv venv "$install_dir/venv" --python "$(which python3)"; then
            print_error "Failed to create virtual environment"
            rm -rf "$temp_extract_dir"
            return 1
        fi
        
        # Activate the virtual environment and install the wheel
        if ! source "$install_dir/venv/bin/activate" && uv pip install "$wheel_path"; then
            print_error "Failed to install wheel and dependencies"
            rm -rf "$temp_extract_dir"
            return 1
        fi
        
        # Create wrapper script for rogue command
        local wrapper_script="$install_dir/rogue"
        cat > "$wrapper_script" << EOF
#!/bin/bash
# Rogue wrapper script that uses the installed virtual environment
source "\$(dirname "\$0")/venv/bin/activate"
exec python -m rogue "\$@"
EOF
        
        chmod +x "$wrapper_script"
        print_success "Python wheel and dependencies installed successfully"
        print_status "Virtual environment: $install_dir/venv"
        print_status "Use 'rogue' command to run the installed package"
    fi
    
    # Install binary
    if [ -n "$binary_file" ]; then
        print_status "Installing binary..."
        local binary_name="rogue-tui"
        local binary_dest="$install_dir/$binary_name"
        
        if ! cp "$binary_file" "$binary_dest"; then
            print_error "Failed to copy binary"
            rm -rf "$temp_extract_dir"
            return 1
        fi
        
        # Make binary executable
        chmod +x "$binary_dest"
        print_success "Binary installed as $binary_name"
    fi
    
    # Clean up
    rm -rf "$temp_extract_dir"
    
    print_success "Installation completed successfully!"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --skip-path)
            SKIP_PATH_UPDATE=true
            shift
            ;;
        -v|--version)
            VERSION="$2"
            shift 2
            ;;
        -f|--force)
            FORCE_INSTALL=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main installation process
main() {
    print_status "Rogue Installer"
    print_status "========================"
    print_status "INSTALL_DIR: $INSTALL_DIR"
    print_status "SKIP_PATH_UPDATE: $SKIP_PATH_UPDATE"
    print_status "FORCE_INSTALL: $FORCE_INSTALL"
    print_status "VERSION: $VERSION"
    
    # Check if installation directory already exists
    if [ -d "$INSTALL_DIR" ] && [ "$FORCE_INSTALL" = false ]; then
        print_error "Installation directory $INSTALL_DIR already exists"
        print_status "Use -f or --force to overwrite, or specify a different directory with -d"
        exit 1
    fi
    
    # Detect platform and architecture
    local platform
    platform=$(detect_platform)
    print_status "Detected platform: $platform"
    
    # Detect shell type
    local shell_type
    shell_type=$(detect_shell)
    print_status "Detected shell: $shell_type"
    
    # Create temporary directory
    local temp_dir
    temp_dir=$(mktemp -d)
    trap "rm -rf '$temp_dir'" EXIT
    
    # Download release
    local archive_path
    archive_path=$(download_release "$temp_dir" "$VERSION")

    download_exit_code=$?
    if [ $download_exit_code -ne 0 ] || [ -z "$archive_path" ]; then
        exit 1
    fi
    
    # Extract and install files
    extract_and_install "$archive_path" "$INSTALL_DIR" "$platform"
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    # Update PATH if requested
    if [ "$SKIP_PATH_UPDATE" = false ]; then
        local shell_config
        shell_config=$(get_shell_config "$shell_type")
        
        if [ -n "$shell_config" ]; then
            if is_path_in_path "$INSTALL_DIR" "$shell_type"; then
                print_status "PATH already contains $INSTALL_DIR"
            else
                add_to_path "$INSTALL_DIR" "$shell_type" "$shell_config"
            fi
        else
            print_warning "Could not determine shell configuration file"
            print_status "Please manually add $INSTALL_DIR to your PATH"
        fi
    else
        print_status "Skipping PATH update as requested"
    fi
    
    # Final instructions
    echo
    print_success "Installation completed!"
    print_status "Installation directory: $INSTALL_DIR"
    
    if [ "$SKIP_PATH_UPDATE" = false ]; then
        local shell_config
        shell_config=$(get_shell_config "$shell_type")
        
        if [ -n "$shell_config" ]; then
            print_status "To use rogue commands, restart your terminal or run:"
            echo "  source $shell_config"
        fi
    fi
    
    print_status "Available commands:"
    if [ -f "$INSTALL_DIR/rogue" ]; then
        echo "  rogue - Python-based rogue agent evaluator (installed in virtual environment)"
    fi
    if [ -f "$INSTALL_DIR/rogue-tui" ]; then
        echo "  rogue-tui - Terminal UI for rogue agent evaluator"
    fi
}

# Run main function
main "$@"
