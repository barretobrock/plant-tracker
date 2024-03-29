# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

_Note: 'Unreleased' section below is used for untagged changes that will be issued with the next version bump_

### [Unreleased] - 2024-00-00
#### Added
#### Changed
#### Deprecated
#### Removed
#### Fixed
#### Security
__BEGIN-CHANGELOG__
 
### [0.0.6] - 2024-03-23
#### Added
 - Map view of all items
 - Map list of all non-plant items
 - Irrigated plants now get a sign rendered on map
#### Changed
 - Plant & species image carousels are now unified
 - Refactor template files to `.jinja` extension for better syntax highlighting in development
#### Deprecated
#### Removed
 - Support for plant map objects in map list (this should only be accessed through plant object) 
#### Fixed
 - Plant geodata map object input now works
#### Security
 
### [0.0.5] - 2024-03-18
#### Changed
 - Logic for determining location is now handled under one function for all geodata
#### Fixed
 - Adjusted model to better organize region/subregion hierarchy for plant location
 - Issue where plant family table object wasn't being properly referenced
 
### [0.0.4] - 2024-03-10
#### Added
 - Support for pasting images from clipboard
 - All forms have 'cancel' button that just goes back a page
 - Geodata, maintenance, observation and watering logging support
#### Changed
 - Broke out routes for alternate names and scheduled maintenance
#### Fixed
 - image carousel now works
 
### [0.0.3] - 2024-03-09
#### Added
 - More routes, still not done with fully-functional ;)
 
### [0.0.2] - 2024-03-07
#### Fixed
 - Resolved issue where a trailing forward slash returns 404 error


### [0.0.1] - 2024-01-21
#### Added
 - Initiated project

__END-CHANGELOG__