#!/usr/bin/env bash
#
# This script installs the 'llm' command for the AI-Monitor control center.
# It creates a symbolic link in /usr/local/bin to the main control_center.sh script.
#
set -e

# Get the absolute path of the project root directory
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)
PROJECT_ROOT=$(dirname "$SCRIPT_DIR")
CONTROL_CENTER_SCRIPT="$PROJECT_ROOT/control_center.sh"
SYMLINK_PATH="/usr/local/bin/llm"

# 1. Check if control_center.sh exists
if [ ! -f "$CONTROL_CENTER_SCRIPT" ]; then
  echo "❌ Error: control_center.sh not found at $CONTROL_CENTER_SCRIPT"
  exit 1
fi

# 2. Make control_center.sh executable
echo "⚙️  Making control_center.sh executable..."
chmod +x "$CONTROL_CENTER_SCRIPT"
echo "✅ Done."

# 3. Create the symbolic link using sudo
echo "🔗 Creating system-wide command 'llm'..."
echo "   This will create a symlink at $SYMLINK_PATH."
echo "   You may be prompted for your administrator password."

if [ -L "$SYMLINK_PATH" ]; then
  echo "ℹ️  'llm' command already exists. Removing old link first."
  sudo rm "$SYMLINK_PATH"
fi

sudo ln -s "$CONTROL_CENTER_SCRIPT" "$SYMLINK_PATH"

# 4. Verify installation
if [ "$(readlink "$SYMLINK_PATH")" == "$CONTROL_CENTER_SCRIPT" ]; then
  echo "✅ Successfully installed the 'llm' command."
  echo "🚀 You can now run the control center from anywhere using:"
  echo
  echo "   llm start         # To start all services"
  echo "   llm status        # To check service status"
  echo "   llm launch_ui     # To open the web control panel"
  echo "   llm help          # To see all available commands"
  echo
else
  echo "❌ Installation failed. Please check permissions for /usr/local/bin."
  exit 1
fi

exit 0 