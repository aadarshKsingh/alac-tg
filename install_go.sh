#!/bin/bash

# Check if Go is already installed
if command -v go >/dev/null 2>&1; then
    echo "Go is already installed."
    go version
    exit 0
fi

# Step 1: Detect system architecture
ARCH=$(uname -m)

case $ARCH in
    "x86_64")
        ARCH_SUFFIX="amd64"
        ;;
    "aarch64"|"arm64")
        ARCH_SUFFIX="arm64"
        ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Step 2: Get latest Go version (or set manually)
# Uncomment to fetch latest stable Go version automatically:
# GO_VERSION=$(curl -s https://go.dev/VERSION?m=text | sed 's/go//')
GO_VERSION="23.1"
GO_TARBALL="go1.${GO_VERSION}.linux-${ARCH_SUFFIX}.tar.gz"
DOWNLOAD_URL="https://go.dev/dl/${GO2_TARBALL}"  # <-- NOTE: Fix this typo to ${GO_TARBALL}

# Fix the typo above:
DOWNLOAD_URL="https://go.dev/dl/${GO_TARBALL}"

echo "Downloading Go version ${GO_VERSION} for ${ARCH}..."
mkdir -p ~/Downloads
cd ~/Downloads
wget -c "$DOWNLOAD_URL"

# Step 3: Remove old Go installation if exists
echo "Removing old Go installation (if any)..."
sudo rm -rf /usr/local/go

# Step 4: Extract Go tarball to /usr/local
echo "Extracting Go tarball to /usr/local..."
sudo tar -C /usr/local/ -xzf "${GO_TARBALL}"

# Step 5: Verify extraction
if [ -d "/usr/local/go" ]; then
    echo "Go successfully extracted to /usr/local/go"
else
    echo "Error: Go extraction failed."
    exit 1
fi

# Step 6: Set PATH environment variable for the current session
echo "Setting PATH for the current session..."
export PATH=$PATH:/usr/local/go/bin

# Step 7: Make PATH change permanent for the user
echo "Making PATH change permanent for the user..."

PROFILE_FILE="$HOME/.profile"
if ! grep -q '/usr/local/go/bin' "$PROFILE_FILE"; then
    echo 'Adding Go to PATH in .profile...'
    echo '# set PATH so it includes /usr/local/go/bin if it exists' >> "$PROFILE_FILE"
    echo 'if [ -d "/usr/local/go/bin" ] ; then' >> "$PROFILE_FILE"
    echo '    PATH="/usr/local/go/bin:$PATH"' >> "$PROFILE_FILE"
    echo 'fi' >> "$PROFILE_FILE"
    source "$PROFILE_FILE"
fi

# Step 8: Set GOPATH for the current session
echo "Setting GOPATH for the current session..."
export GOPATH=$HOME/go

# Step 9: Make GOPATH change permanent for the user
echo "Making GOPATH change permanent for the user..."

if ! grep -q '$HOME/go/bin' "$PROFILE_FILE"; then
    echo 'Adding GOPATH to PATH in .profile...'
    echo '# Add GOPATH to PATH if it exists' >> "$PROFILE_FILE"
    echo 'if [ -d "$HOME/go/bin" ] ; then' >> "$PROFILE_FILE"
    echo '    PATH="$HOME/go/bin:$PATH"' >> "$PROFILE_FILE"
    echo 'fi' >> "$PROFILE_FILE"
    source "$PROFILE_FILE"
fi

echo "Go installation complete!"

# Verify Go version
go version
