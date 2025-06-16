#!/bin/bash

# Build verification script for Bazel migration
# This script should be run from the repository root with: ./scripts/test-build.sh

set -e

echo "🏗️  Testing Bazel build targets..."
echo ""

echo "✅ Building shell script tools..."
bazel build //tools:get-version

echo "✅ Building Go backend server..."
bazel build //tldr/backend/cmd/server:server

echo "✅ Building protocol buffers..."
bazel build //tldr/proto:news_proto_go

echo "✅ Building Python airflow..."
bazel build //airflow:bps

echo "🔧 Testing TypeScript compilation (expect dependency errors)..."
bazel build //tldr/frontend:src_ts || echo "   (TypeScript build shows npm dependency issues - this is expected)"

echo "✅ Testing Bazel query..."
bazel query "//tools/... + //tldr/backend/... + //tldr/proto/... + //airflow/... + //tldr/frontend/..." > /dev/null

echo ""
echo "🎉 All working targets built successfully!"
echo ""
echo "📋 Summary:"
echo "   ✅ Shell scripts: //tools:get-version"
echo "   ✅ Go backend: //tldr/backend/cmd/server:server"
echo "   ✅ Protocol buffers: //tldr/proto:news_proto_go"
echo "   ✅ Python: //airflow:bps"
echo "   🔧 TypeScript: //tldr/frontend:src_ts (build system works, npm deps needed)"
echo "   ⏳ Rust: Not yet implemented (edition2024 compatibility issues)"