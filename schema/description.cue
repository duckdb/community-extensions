// CUE Schema for DuckDB Community Extension description.yml files
package description

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
	// Required fields
	name:        string & !=""                      // Extension name (non-empty)
	description: string & !=""                      // Description (non-empty)
	version?:    string | number                    // Version string or number (optional, e.g., "1.0.0", 2024120401)
	language:    string & !=""                      // Programming language (e.g., "C++", "Rust", "Rust & C++")
	build:       "cmake" | "CMake" | "cargo"        // Build system
	maintainers: [...string | #Maintainer] & [_, ...] // At least one maintainer (string or struct)

	// Optional fields
	license?:                 string & !=""         // License (e.g., "MIT", "Apache-2.0", "MIT OR Apache-2.0")
	licence?:                 string & !=""         // Alternative spelling (deprecated)
	excluded_platforms?:      string | [...string]  // Platforms to exclude (string or list)
	requires_toolchains?:     string | [...string]  // Required toolchains (string or list)
	opt_in_platforms?:        string                // Semicolon-separated opt-in platforms
	vcpkg_commit?:            string                // Specific vcpkg commit hash
	vcpkg_url?:               string                // Custom vcpkg URL
	custom_toolchain_script?: string | bool         // Path to custom toolchain setup script or boolean
	test_config?:             string                // Test configuration
	requires_extensions?:     string | [...string]  // Required extensions (string or list)
	extended_description?:    string                // Extended description (deprecated, use docs.extended_description)
}

// Maintainer can be a string or structured object
#Maintainer: {
	name:    string
	github?: string
}

// Repository information
#Repo: {
	github:          string & !="" // GitHub repo in format "owner/repo"
	ref:             string & !="" // Git commit hash or tag
	ref_next?:       string        // Next reference for testing
	canonical_name?: string        // Canonical name override
}

// Documentation - can be a string (URL) or structured object
#Docs: string | {
	hello_world?:          string // Quick start example
	extended_description?: string // Detailed documentation
	readme?:               string // README content
	docs_url?:             string // External documentation URL

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
