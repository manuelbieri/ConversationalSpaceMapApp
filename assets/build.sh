#!/usr/bin/env bash

cd "$(dirname "${BASH_SOURCE[0]}")/.."

printf 'Create build template...\n'
briefcase create

printf 'Update assets...\n'
briefcase update --update-resources

printf 'Build...\n'
briefcase build

printf 'Run...\n'
briefcase run
