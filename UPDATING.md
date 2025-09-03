# Community Extension Update Guide

This guide provides instructions for updating a community extension. Currently, these instructions apply only to extensions
built with the [C++ extension template](https://github.com/duckdb/extension-template).

Extensions based on the [C++ extension template](https://github.com/duckdb/extension-template) are strongly tied to a
specific DuckDB version. Additionally, the C++ API against which these extensions are built is not a stable API, meaning
that it can change between DuckDB releases. For Community Extension maintainers, this means that there might be some
work required to make their extension compatible with a new version of DuckDB.

This document outlines the update process to make it as straightforward as possible. In most cases, no changes will be
required for your extension.

## The DuckDB release cycle

Let's begin by reviewing the DuckDB release cycle, which follows these main steps:

- Releases are scheduled and marked in the [calendar](https://duckdb.org/release_calendar.html)
- ~2 weeks before the release, a phase called "feature freeze" starts
- On start of the feature freeze, a new branch is created called `vx.y-codename` matching the version and codename of the upcoming release.
    - the `vx.y-codename` branch is effectively the release candidate for the upcoming `vx.y.z` release.
    - the `vx.y-codename` branch will only receive crucial fixes now.
    - all new features can now only be merged into the `main` branch
- On release, the latest commit of the `vx.y-codename` is tagged as the release
- After release the `vx.y-codename` branch is kept alive for any bugfix releases that may follow.

## Community Extension release cycle

### Example extension
To illustrate the community extension release cycle, we're going to assume you are maintaining an extension that has been cloned from the [C++ extension template](https://github.com/duckdb/extension-template) and has it's CI closely resembling what is in the template.

First, let's examine
the [distribution workflow](https://github.com/duckdb/extension-template/blob/main/.github/workflows/MainDistributionPipeline.yml)
from the template that defines the extension build process. A typical configuration looks like this:

```yaml
duckdb-stable-build:
  name: Build extension binaries
  uses: duckdb/extension-ci-tools/.github/workflows/_extension_distribution.yml@v1.3.2
  with:
    duckdb_version: v1.3.2
    ci_tools_version: v1.3.2
    extension_name: quack

duckdb-next-build:
  name: Build extension binaries
  uses: duckdb/extension-ci-tools/.github/workflows/_extension_distribution.yml@main
  with:
    duckdb_version: main
    ci_tools_version: main
    extension_name: quack
```

We can see that we are running two workflows that call into the same reusable workflow. 

Firstly we have the `duckdb-stable-build` workflow, which should target the latest stable release of DuckDB. This workflow is used to build and test the extension binaries ensuring the extensions work with the latest stable version of DuckDB. The community extensions repository CI will use this very same workflow to build and distribute new versions of the extensions as its updated.

Secondly we have the `duckdb-next-build` workflow. This workflow has a very different purpose: it will try to build the extension against the latest version of DuckDB, to make sure that it still works. This is not used for any release process but is purely meant to inform the maintainer whether the extension is still compatible with latest DuckDB main.

Now let's take a look at our extension descriptor in the community extensions repo, we take this sample from [the quack extension](`https://github.com/duckdb/community-extensions/blob/main/extensions/quack/description.yml`) which builds the [C++ extension template](https://github.com/duckdb/extension-template) as a community extension:

```yaml
extension:
  name: quack
  description: Provides a hello world example demo
  version: 0.0.1
  language: C++
  build: cmake
  license: MIT
  maintainers:
    - hannes

repo:
  github: duckdb/extension-template
  ref: c7d9ef3463376dc2b64959abf3a477eae2280142
```

### Release process
There are 2 main ways in which community extensions get released.

Firstly, whenever an extension descriptor is updated, the extension is rebuilt and released. This will always target the latest stable version of DuckDB.

Secondly, whenever a new version of DuckDB is released, all community extensions are rebuilt as part of the release process. This will ensure the extensions are available
right from the moment the new DuckDB release is out. We will take a closer look at how this works in the next section.

## Upgrading an extension to a new DuckDB version
When a new DuckDB version is (about to be) released, there are two states your extension can be in, which we will illustrate using the example extension described before:

1. Extension is compatible both with the latest and upcoming version of DuckDB, meaning both `duckdb-stable-build` and
   `duckdb-next-build` are passing
2. Extension requires changes to be compatible with upcoming DuckDB release. Only `duckdb-stable-build` is passing

For state 1, no action is required. Your extension will be released automatically as part of the upcoming DuckDB release.

State 2 indicates that changes in DuckDB's API, build system, or CI require updates to your extension's repository to
maintain compatibility. Action is needed to prepare your extension for the upcoming release.

### Update path: Before DuckDB release 
Whenever your extension is in state 2 **before** a release, we recommend following the following steps to ensure your extension is available on release day.

**Step 1:** in your extension repository, create a branch that you call `vx.y-<codename>` following the name/version of the upcoming DuckDB release. The goal of this branch is to develop and test a version of your extension that *is* compatible with the upcoming release.

**Step 2:** In
the [distribution workflow](https://github.com/duckdb/extension-template/blob/main/.github/workflows/MainDistributionPipeline.yml)
of the newly created `vx.y-<codename>` branch, make the following changes:

```yaml
duckdb-stable-build:
  # ...
  if: false # Disabled because we are now in `vx.y-<codename>` branch that will be incompatible with latest stable release
  # ...
```

**Step 2:** check out the duckdb submodule also to the `vx.y-codename` branch, and commit the updated workflow and submodule change.

**Step 3:** Apply all fixes to the extension repository in the `vx.y-codename` branch.

**Step 4:** PR the latest commit of your `vx.y-codename` branch in to community-extensions by adding a `repo.ref_next` field to your descriptor:

```yaml
repo:
  github: duckdb/extension-template
  ref: c7d9ef3463376dc2b64959abf3a477eae2280142
  ref_next: <latest commit of vx.y-codename of your repo>
```

### Update path: After DuckDB release

If you're updating your extension after a DuckDB release, the process is more straightforward. Follow these simplified
steps:

**Step 1:** Check out the upgrade instructions for the relevant update. Apply fixes directly on `main` branch of extension

**Step 2:** Bump the stable DuckDB version in the [distribution workflow](https://github.com/duckdb/extension-template/blob/main/.github/workflows/MainDistributionPipeline.yml) and update the submodule. Merge into your main branch.

**Step 3:** PR your updated commit to the descriptor file as normal.