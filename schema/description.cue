// CUE Schema for DuckDB Community Extension description.yml files
// 
// This schema validates the structure and content of extension description files.
// All extensions must provide a valid description.yml in their extension directory.
//
// Quick Example:
//   extension:
//     name: my_extension
//     description: Does something useful
//     version: 0.1.0
//     language: C++
//     build: cmake
//     license: MIT
//     maintainers:
//       - username
//   repo:
//     github: owner/repository
//     ref: abc123...  # 40-char commit hash
//
// See: https://github.com/duckdb/community-extensions for full documentation
package description

// Valid DuckDB platform identifiers
// These are the target platforms DuckDB builds for.
// Use in excluded_platforms to skip building on specific platforms.
// Example: excluded_platforms: "wasm_mvp;wasm_eh;wasm_threads"
#Platform: "linux_amd64_musl" | "linux_arm64" | "osx_amd64" | "osx_arm64" | "wasm" | "wasm_eh" | "wasm_mvp" | "wasm_threads" | "windows_amd64" | "windows_amd64_mingw" | "windows_amd64_rtools" | "windows_arm64" | "windows_arm64_mingw"

// Common SPDX license identifiers
// See: https://spdx.org/licenses/
// Prefer SPDX identifiers for standardization, but custom license strings are accepted.
// For dual licensing, use: "MIT OR Apache-2.0"
// Example: license: "MIT"
#SPDXLicense: "MIT" | "Apache-2.0" | "BSD-2-Clause" | "BSD-3-Clause" | "GPL-2.0" | "GPL-3.0" | "LGPL-2.1" | "LGPL-3.0" | "MPL-2.0" | "ISC" | "Unlicense" | "BSL 1.1" | "MIT OR Apache-2.0" | "MIT AND Apache-2.0" | "Apache-2.0 OR MIT"

// Build system type
// cmake: Most C++ extensions (lowercase only)
// cargo: Rust extensions
#BuildSystem: "cmake" | "cargo"

// Valid toolchain identifiers
// Required build dependencies beyond the standard DuckDB toolchain.
// Use semicolon-separated list: "rust;python3"
// Example: requires_toolchains: "rust;python3"
#Toolchain: "rust" | "python3" | "vcpkg" | "parser_tools" | "cmake" | "openssl" | "libxml2" | "zlib" | "fortran" | "omp" | "valhalla"

// Top-level structure of description.yml
#Description: {
	extension:             #Extension
	repo:                  #Repo
	docs?:                 #Docs
	extended_description?: string                // Top-level extended_description (deprecated)
	redirect_from?:        string | [...string]  // Jekyll redirect configuration (string or list)
	...                                          // Allow other fields for compatibility
}

// Extension metadata
#Extension: {
	// ========== REQUIRED FIELDS ==========
	
	// Extension name (lowercase, alphanumeric and underscores)
	// Example: name: "my_extension"
	name:        string & !=""
	
	// Short description of what the extension does
	// Example: description: "Provides JSON parsing capabilities"
	description: string & !=""
	
	// Programming language(s) used
	// Common values: "C++", "Rust", "Rust & C++", "SQL & C++"
	// Example: language: "C++"
	language:    string & !=""
	
	// Build system - must be either cmake or cargo
	// Example: build: cmake
	build:       #BuildSystem
	
	// Extension maintainers - at least one required
	// Can be GitHub username strings or structured objects with name/github
	// Example: maintainers: ["username1", "username2"]
	// Example: maintainers: [{name: "John Doe", github: "johndoe"}]
	maintainers: [...string | #Maintainer] & [_, ...]

	// ========== OPTIONAL FIELDS ==========
	
	// Version number - accepts semantic versions, numeric dates, or numbers
	// Semantic: "0.1.0", "1.2.3-alpha.1", "2.1.0"
	// Date format: "2024120401" (YYYYMMDD + revision)
	// Example: version: "0.1.0"
	version?:    string & =~"^([0-9]+\\.[0-9]+(\\.[0-9]+)?(\\.[0-9]+)?(-[a-zA-Z0-9.]+)?|[0-9]{8,})$" | number
	
	// SPDX license identifier (recommended) or custom license string
	// Example: license: "MIT"
	// Example: license: "MIT OR Apache-2.0"
	license?:                 #SPDXLicense | string & !=""
	
	// Alternative British spelling of license (deprecated, use 'license')
	licence?:                 #SPDXLicense | string & !=""
	
	// Platforms to exclude from building (semicolon-separated or list)
	// String format: "wasm_mvp;wasm_eh;wasm_threads"
	// List format: ["wasm_mvp", "wasm_eh", "wasm_threads"]
	// Example: excluded_platforms: "windows_amd64_mingw"
	excluded_platforms?:      string | [...#Platform]
	
	// Additional build toolchains required (semicolon-separated or list)
	// Common: rust, python3, vcpkg, cmake, openssl
	// Note: Empty string is deprecated - remove the field if not needed
	// Example: requires_toolchains: "rust;python3"
	// Example: requires_toolchains: ["rust", "python3"]
	requires_toolchains?:     string | [...#Toolchain]
	
	// Platforms to opt-in for building (semicolon-separated)
	// Must contain only valid platform names from #Platform enum
	// Example: opt_in_platforms: "windows_arm64;"
	opt_in_platforms?:        string & =~"^(linux_amd64_musl|linux_arm64|osx_amd64|osx_arm64|wasm|wasm_eh|wasm_mvp|wasm_threads|windows_amd64|windows_amd64_mingw|windows_amd64_rtools|windows_arm64|windows_arm64_mingw)(;(linux_amd64_musl|linux_arm64|osx_amd64|osx_arm64|wasm|wasm_eh|wasm_mvp|wasm_threads|windows_amd64|windows_amd64_mingw|windows_amd64_rtools|windows_arm64|windows_arm64_mingw))*;?$"
	
	// Specific vcpkg commit hash (40 hexadecimal characters)
	// Get from: https://github.com/microsoft/vcpkg/commits/master
	// Example: vcpkg_commit: "abc123def456..."
	vcpkg_commit?:            string & =~"^[a-f0-9]{40}$"
	
	// Custom vcpkg repository URL
	// Example: vcpkg_url: "https://github.com/microsoft/vcpkg.git"
	vcpkg_url?:               string
	
	// Path to custom toolchain setup script or boolean flag
	// Example: custom_toolchain_script: true
	// Example: custom_toolchain_script: "scripts/setup.sh"
	custom_toolchain_script?: string | bool
	
	// Test configuration (JSON or custom format)
	// Example: test_config: '{test_env_variables: {SKIP_TESTS: 1}}'
	test_config?:             string
	
	// Other extensions this extension depends on
	// Example: requires_extensions: "httpfs;parquet"
	requires_extensions?:     string | [...string]
	
	// Extended description (deprecated - use docs.extended_description instead)
	extended_description?:    string
}

// Maintainer can be a string (GitHub username) or structured object
#Maintainer: {
	// Maintainer's name
	name:    string
	
	// GitHub username (alphanumeric and hyphens, no leading/trailing hyphens)
	// Example: github: "octocat"
	github?: string & =~"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$"
}

// Repository information
#Repo: {
	// GitHub repository in format "owner/repository"
	// Example: github: "duckdb/duckdb"
	github:          string & !=""
	
	// Git commit hash (40 hex chars) or version tag
	// Commit: "abc123def456..." (preferred for stability)
	// Tag: "v1.0.0" or "main" (will track moving target)
	// Example: ref: "7f71365c5ce61b2b346717af07c9d448cfc9d3c3"
	ref:             string & !=""
	
	// Next reference for testing against unreleased DuckDB versions
	// Example: ref_next: "main"
	ref_next?:       string
	
	// Override the canonical extension name (rarely needed)
	// Example: canonical_name: "my_extension"
	canonical_name?: string
}

// Documentation - can be a string (URL) or structured object
// 
// Simple format (URL string):
//   docs: "https://github.com/owner/repo/blob/main/README.md"
//
// Structured format (recommended):
//   docs:
//     hello_world: |
//       SELECT 'Hello World';
//     extended_description: |
//       Detailed documentation here...
//
#Docs: string | {
	// Quick start SQL example showing basic usage
	// Example: hello_world: "SELECT my_function();"
	hello_world?:          string
	
	// Detailed documentation in Markdown format
	// Example: extended_description: "This extension provides..."
	extended_description?: string
	
	// README content in Markdown format
	readme?:               string
	
	// External documentation URL (must start with http:// or https://)
	// Example: docs_url: "https://myextension.readthedocs.io"
	docs_url?:             string & =~"^https?://"

	// Allow additional documentation fields for specific extensions
	...
}

// Validation rules
#Description & {
	// Validate github format (should contain owner/repo)
	repo: github: =~"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+$"

	// Validate ref is a commit hash (40 chars hex) or semantic version tag
	repo: ref: =~"^([a-f0-9]{40}|v?[0-9]+\\.[0-9]+\\.?[0-9]*.*|[a-z0-9_.-]+)$"
}
