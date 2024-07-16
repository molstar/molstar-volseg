PERM_FOLDER="external_tools/castle_model_converter/"

LINUX_URL="https://github.com/castle-engine/castle-model-viewer/releases/download/v5.0.0/castle-model-viewer-5.0.0-linux-x86_64.tar.gz"
MAC_URL="https://github.com/castle-engine/castle-model-viewer/releases/download/v5.0.0/castle-model-viewer-5.0.0-darwin-x86_64.zip"
WIN32_URL="https://github.com/castle-engine/castle-model-viewer/releases/download/v5.0.0/castle-model-viewer-5.0.0-win64-x86_64.zip"

TEMP_ARCHIVE_BASE="$PERM_FOLDER/temp/"

mkdir -p $TEMP_ARCHIVE_BASE || echo "Error while creating folder"


# windows
# cd external_tools/castle_model_viewer/temp

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # echo "Linux Gnu"
    TEMP_ARCHIVE="$TEMP_ARCHIVE_BASE.tar.gz"
    wget -O "$TEMP_ARCHIVE" "$LINUX_URL"
    echo "$TEMP_ARCHIVE" -C "$TEMP_ARCHIVE_BASE"
    tar -xvzf "$TEMP_ARCHIVE" -C "$TEMP_ARCHIVE_BASE"
# elif [[ "$OSTYPE" == "darwin"* ]]; then
#     # echo "Mac OSX"
#     TEMP_ARCHIVE="$TEMP_ARCHIVE_BASE.zip"
#     wget -O "$TEMP_ARCHIVE" "$MAC_URL"
#     unzip "$TEMP_ARCHIVE" -d "$TEMP_ARCHIVE_BASE"
# elif [[ "$OSTYPE" == "cygwin" ]]; then
#     echo "CYGWIN"
# elif [[ "$OSTYPE" == "msys" ]]; then
#     echo "MINGW"
# elif [[ "$OSTYPE" == "win32" ]]; then
#     TEMP_ARCHIVE="$TEMP_ARCHIVE_BASE.zip"
#     wget -O "$TEMP_ARCHIVE" "$WIN32_URL"
#     unzip "$TEMP_ARCHIVE" -d "$TEMP_ARCHIVE_BASE"
# elif [[ "$OSTYPE" == "freebsd"* ]]; then
#     echo "FREE BSD"
# else
#     echo "Unknown"
fi

# # copying
cp "$TEMP_ARCHIVE_BASE/castle-model-viewer/castle-model-converter" "$PERM_FOLDER/."
rm -rf "$TEMP_ARCHIVE_BASE" || echo "Failed to remove directory"