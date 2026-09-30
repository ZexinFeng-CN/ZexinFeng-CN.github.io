#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# Match the Ruby version used by the local bundle.
if [ -x /opt/homebrew/opt/ruby@3.1/bin/ruby ]; then
  export PATH="/opt/homebrew/opt/ruby@3.1/bin:$PATH"
fi

# Keep the compiler and SDK from the same developer installation.
export SDKROOT="$(xcrun --sdk macosx --show-sdk-path)"
export CC="$(xcrun --find clang)"
export CXX="$(xcrun --find clang++)"
export BUNDLE_PATH=vendor/bundle

bundle exec jekyll serve --livereload "$@"
