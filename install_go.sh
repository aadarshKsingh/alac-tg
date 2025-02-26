#!/bin/bash

# Step 1: Download the Go tarball to ~/Downloads
GO_VERSION="23.1" # Change this if a new version of Go is released
GO_TARBALL="go1.${GO_VERSION}.linux-amd64.tar.gz"
DOWNLOAD_URL="https://go.dev/dl/${GO_TARBALL}"

echo "Downloading Go version ${GO_VERSION}..."
cd ~/Downloads
wget -c $DOWNLOAD_URL

# Step 2: Remove old Go installation if exists
echo "Removing old Go installation (if any)..."
sudo rm -rf /usr/local/go

# Step 3: Extract Go tarball to /usr/local
echo "Extracting Go tarball to /usr/local..."
sudo tar -C /usr/local/ -xzf ${GO_TARBALL}

# Step 4: Verify extraction
if [ -d "/usr/local/go" ]; then
    echo "Go successfully extracted to /usr/local/go"
else
    echo "Error: Go extraction failed."
    exit 1
fi

# Step 5: Set PATH environment variable for the current session
echo "Setting PATH for the current session..."
export PATH=$PATH:/usr/local/go/bin

# Step 6: Make PATH change permanent for the user
echo "Making PATH change permanent for the user..."

PROFILE_FILE="$HOME/.profile"
if ! grep -q '/usr/local/go/bin' "$PROFILE_FILE"; then
    echo 'Adding Go to PATH in .profile...'
    echo '# set PATH so it includes /usr/local/go/bin if it exists' >> $PROFILE_FILE
    echo 'if [ -d "/usr/local/go/bin" ] ; then' >> $PROFILE_FILE
    echo '    PATH="/usr/local/go/bin:$PATH"' >> $PROFILE_FILE
    echo 'fi' >> $PROFILE_FILE
    source $PROFILE_FILE
fi

# Step 7: Set GOPATH for the current session
echo "Setting GOPATH for the current session..."
export GOPATH=$HOME/go

# Step 8: Make GOPATH change permanent for the user
echo "Making GOPATH change permanent for the user..."

if ! grep -q '$HOME/go/bin' "$PROFILE_FILE"; then
    echo 'Adding GOPATH to PATH in .profile...'
    echo '# Add GOPATH to PATH if it exists' >> $PROFILE_FILE
    echo 'if [ -d "$HOME/go/bin" ] ; then' >> $PROFILE_FILE
    echo '    PATH="$HOME/go/bin:$PATH"' >> $PROFILE_FILE
    echo 'fi' >> $PROFILE_FILE
    source $PROFILE_FILE
fi

echo "Go installation complete!"

# Verify Go version
go version
