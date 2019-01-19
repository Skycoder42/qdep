# qdep
A very basic yet simple to use dependency management tool for qmake based projects

## Features

## Installation

## Getting started

## Getting deeper

### Dependency IDs
#### Versioning
#### Multi-Packages

### Normal dependencies
#### Translations
#### Library support
##### Resources and hooks
##### Automatic exports
#### Creating normal dependencies

### Project dependencies
#### Inclusion via SUBDIRS
#### Referencing project dependencies
#### Creating project dependencies

## Documentation
...

### QMAKE-Feature

#### Variables
##### Common Variables
 Name                       | Direction | Default                       | Descriptions
----------------------------|-----------|-------------------------------|--------------
 QDEP_PATH                  | in/out    | `<system>`                    | Holds the path to the qdep binary to be used. Can be overwritten to specify a custom locations
 QDEP_VERSION               | out       | `<system>`                    | The version of qdep which was used to generate the qdep feature
 QDEP_GENERATED_DIR         | in        | `$$OUT_PWD`                   | The sub-directory in the build folder where qdep should place all it's generated files. Can be an absolute or relative path
 QDEP_EXPORT_PATH           | in        | `$$QDEP_GENERATED_DIR/<type>` | The directory where to place export pri files for libraries that export dependencies. Can be relative to OUT_PWD or absolute. Use QDEP_EXPORT_NAME to get the name of that file without a path
 QDEP_PACKAGE_EXPORTS       | in        | `<empty>`                     | Variables to be defined as import/export/nothing and be used as prefix to a class. See TODO
 QDEP_DEPENDS               | in        | `<empty>`                     | Specify all dependencies to qdep packages to be included into your project
 QDEP_PROJECT_SUBDIRS       | in        | `<empty>`                     | Specify all dependencies to qdep projects to be added as qmake project to the SUBDIRS variable. Only evaluted in projects that specify TEMPLATE as `subdirs`
 QDEP_PROJECT_ROOT          | in        | `<empty>`                     | The path to a project qmake project directory or file to resolve QDEP_PROJECT_LINK_DEPENDS against
 QDEP_PROJECT_LINK_DEPENDS  | in        | `<empty>`                     | Sepcify all dependencies to qdep projects this project should be linked against. The dependencies are assumed to be provided in that project via QDEP_PROJECT_SUBDIRS. 
 QDEP_PROJECT_DEPENDS       | in        | `<empty>`                     | Specify all dependencies to qdep projects this qdep project depends on. Can only be used in qdep project dependencies and adds it's contents to QDEP_PROJECT_SUBDIRS of the project that includes this dependency 
 QDEP_TRANSLATIONS          | in        | `<empty>`                     | Specify translation subfiles within a qdep dependency to be merged with the translations of the project they are included from
 QDEP_DEFINES               | in        | `<empty>`                     | Specify DEFINES that are exported if the library exports a pri file. All values are automatically added to DEFINES by qdep
 QDEP_INCLUDEPATH           | in        | `<empty>`                     | Specify INCLUDEPATHS that are exported if the library exports a pri file. All values are automatically added to INCLUDEPATH by qdep 
 QDEP_EXPORTS               | in        | `<empty>`                     | Specify qdep dependencies of which the API should be exported. Can be useful to export packages when used in dynamic libraries - only works if packages explicitly support this
 QDEP_VAR_EXPORTS           | in        | `<empty>`                     | Specify the names of additional qmake variables that should be exported from a qdep dependency besides DEFINES and INCLUDEPATH

##### Advanced Variables
 Name                       | Direction | Default                               | Descriptions
----------------------------|-----------|---------------------------------------|--------------
 QDEP_TOOL                  | in/out    | `<system>`                            | The escaped command line base for qdep commands run from within qmake
 QDEP_CACHE_SCOPE           | in        | `stash`                               | The method of caching to be used to cache various qmake related stuff. Can be &lt;empty>, super or stash
 QDEP_GENERATED_SOURCES_DIR | out       | `$$QDEP_GENERATED_DIR/<type>`         | The directory where generated source files are placed. Is determined by the build configuration to take debug/release builds into account
 QDEP_GENERATED_TS_DIR      | in        | `$$QDEP_GENERATED_DIR/.qdepts/<type>` | The directory where generated translation sources are placed.
 QDEP_LCONVERT              | in        | `lconvert -sort-contexts`             | The path to the lconvert tool and additional arguments to be used to combine translations
 QDEP_EXPORT_NAME           | in/out    | `<pro-file-name>_export.pri`          | The name of a generated library import file. Must be only the name of the file, use QDEP_EXPORT_PATH to specify the location
 QDEP_EXPORTED_DEFINES      | out       | `<empty>`                             | DEFINES that come from QDEP_PACKAGE_EXPORTS or DEFINES from any directly included qdep dependency
 QDEP_EXPORTED_INCLUDEPATH  | out       | `<empty>`                             | INCLUDEPATHs that come from any directly included qdep dependency
 QDEP_HOOK_FNS              | out       | `<empty>`                             | Holds all names of functions to be run as startup hook by qdep

#### Internal
##### Variables
- __QDEP_PRIVATE_SEPERATOR: Seperator between datasets
- __QDEP_TUPLE_SEPERATOR: Seperator between values within a dataset
- __QDEP_INCLUDE_CACHE: objects with details about included depdendencies of all kinds
- __QDEP_ORIGINAL_TRANSLATIONS: All original translation that were in TRANSLATIONS before apply translation combination with QDEP_TRANSLATIONS from included packages
- __QDEP_HOOK_FILES: Paths to header files that contain hook definitions that must be included and loaded by a project

## vardump
- prf: qdep (explicit load)
- config(in): qdep_no_cache, qdep_no_link, qdep_no_pull, qdep_no_clone, qdep_export_all, qdep_no_qm_combine, qdep_link_export, qdep_link_private
- config(out): qdep_build
- tests: qdepCollectDependencies, qdepCollectLinkDependencies, qdepSplitPrivateVar
- replaces: qdepJoinPrivateVar
- env_vars: QDEP_CACHE_DIR, QDEP_SOURCE_OVERRIDE, QDEP_DEFAULT_PKG_FN
- install targets: qdep_ts_target
- extensions to SUBDIRS