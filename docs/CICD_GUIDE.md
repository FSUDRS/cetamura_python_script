# CI/CD Pipeline Guide for Cetamura Batch Tool

This guide explains the continuous integration and continuous deployment (CI/CD) pipeline set up for the Cetamura Batch Tool project.

## Table of Contents

1. [CI/CD Overview](#cicd-overview)
2. [Pipeline Components](#pipeline-components)
3. [Understanding the CI Workflow](#understanding-the-ci-workflow)
4. [Understanding the CD Workflow](#understanding-the-cd-workflow)
5. [Managing Releases](#managing-releases)
6. [Troubleshooting](#troubleshooting)

## CI/CD Overview

The CI/CD pipeline for this project uses GitHub Actions to automate testing, building, and deployment processes. The pipeline is designed with two main workflows:

1. **Continuous Integration (CI)** - Runs on every push to main/master branches and pull requests
2. **Continuous Deployment (CD)** - Triggered when a new version tag is pushed

This approach ensures code quality through automated testing while providing a streamlined process for releasing new versions of the application.

## Pipeline Components

The pipeline consists of the following components:

- **GitHub Actions** - Workflow automation platform
- **pytest** - Testing framework for running automated tests
- **PyInstaller** - Packaging tool for creating standalone executables
- **GitHub Releases** - Platform for publishing versioned releases

## Understanding the CI Workflow

The CI workflow (`ci.yml`) runs whenever code is pushed to the main/master branches or when a pull request is opened against these branches.

### Jobs in the CI Workflow

#### Test Job

This job runs your test suite against multiple Python versions and operating systems:

1. Checks out the code
2. Sets up Python environment (versions 3.9 and 3.11)
3. Installs dependencies from requirements.txt and requirements-dev.txt
4. Runs pytest to execute all tests

#### Build Job

This job builds the application executable:

1. Runs only after the test job completes successfully
2. Builds the executable using PyInstaller with the Cetamura_Batch_Tool.spec file
3. Archives the build artifacts for later use

## Understanding the CD Workflow

The CD workflow (`release.yml`) is triggered when you push a tag that starts with "v" (e.g., v1.0.0).

### Jobs in the CD Workflow

#### Build and Release Job

1. Checks out the code
2. Sets up Python environment
3. Installs dependencies
4. Builds the executable using PyInstaller
5. Archives the build as a zip file
6. Creates a GitHub Release with the archived executable

## Managing Releases

To create a new release:

1. Ensure all tests pass locally: `python -m pytest`
2. Update version information in relevant files
3. Commit your changes: `git commit -m "Prepare for release x.y.z"`
4. Create and push a tag: 
   ```
   git tag vx.y.z
   git push origin vx.y.z
   ```
5. The release workflow will automatically build and publish the release

## Troubleshooting

Common issues and their solutions:

### Tests Failing in CI but Passing Locally

- Check for environment-specific code
- Ensure all dependencies are in requirements.txt
- Look for hardcoded paths or environment variables

### Build Failures

- Verify PyInstaller spec file is correct
- Check for hidden dependencies
- Ensure all necessary files are included in the spec

### Release Creation Failures

- Check tag format (must begin with "v")
- Verify you have proper permissions in the repository
- Ensure the GitHub token has appropriate permissions
