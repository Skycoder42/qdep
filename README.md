# qdep
A very basic yet simple to use dependency management tool for qmake based projects.

[![Travis Build Status](https://travis-ci.org/Skycoder42/qdep.svg?branch=master)](https://travis-ci.org/Skycoder42/qdep)
[![Appveyor Build status](https://ci.appveyor.com/api/projects/status/s222vatjpd4ic70w/branch/master?svg=true)](https://ci.appveyor.com/project/Skycoder42/qdep/branch/master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/373a21f05f8847c29ce08739891631e8)](https://www.codacy.com/app/Skycoder42/qdep)
[![AUR](https://img.shields.io/aur/version/qdep.svg)](https://aur.archlinux.org/packages/qdep/)

## Features
- Seamless integration in qmake projects - no extra files needed
- Basic dependency management using git repositories as package sources
- Globally caches source files to speed up builds
- Packages are simple pri-files that are included by the target project
- Recursive dependency solving
- Allows branch and tag based versioning
- Supports translations for qdep packages
- Supports automatic export of qdep packages from dynamic libraries
- Handles QRC-Resources and startup hooks to work even when used in static libraries
- Supports special "Project dependencies" wich allows you to add whole qmake projects to a SUBDIRS project
- Can generate "library export" pri files that provide an easy and reliable way to link against libraries
	- Implicitly supports exported qdep packages and projects

## Design Goals/Scope
qdep was designed with the following goals in mind:

1. Full qmake integration: qdep should not require any extra commands to install packages and prepare a project to be built. Just running qmake on the target project should take care of this
2. Simple installation: Using python makes it easy to use the tool on any platform. Besides the install only a single setup command is needed to make qdep work for any Qt installation
3. Full Qt support: All features of Qt - including resources, startup hooks and translations should be supported with minimal effort for application developers
4. Library exports: Since all qdep packages are source based, having multiple libraries that use the same package can be problematic. With qdep, one can "export" a package from a library, making it available to all the others.
5. No additional server infrastructure: qdep should not require any extra servers to provide a package index. Any git repository can server as a package without any extra preparations needed

Please note that qdep is kept intentionally small to fullfill exactly those goals. Other build systems or more complex package management features are not supported and never will be. This project will stay active until the Qt Company switches their build systems to CMake. At that point this project will either be dropped or ported to CMake, depending on what alternative solutions already exist at that point.

## Installation
To install the package, follow one of the following possibilities. Please note that only Python >= 3.7 is officially supported. Earlier versions might work as well, but have not been tested.

1. **Arch Linux:** Use the AUR-Package: [qdep](https://aur.archlinux.org/packages/qdep/)
2. **Any Platform:** Install via pip: [`pip install qdep`](https://pypi.org/project/qdep/)
3. **Any Platform:** Clone the repository and install the sources directly: `python setup.py install`

After installing, you have to "enable" qdep for each Qt-Kit you want to use qdep with. This can be done by opening a terminal and calling:
```
qdep prfgen --qmake "</path/to/qmake>"
```
For example, if you have installed Qt 5.12.0 for MSVC 2017 x64 on windows in the default location (`C:\Qt`), the command would look like this:
```
qdep prfgen --qmake "C:\Qt\5.12.0\msvc2017_64\bin\qmake.exe"
```

**Note:** Depending on how the corresponding Qt-Kit was installed, you might need to run the command with administrator/sudo permissions. Alternatively, you can call the command with `--dir /some/path` and export that very same path as value to the `QMAKEPATH` environment variable, if you have no such permissions.

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
 QDEP_DEPENDS               | in        | `<empty>`                     | Specify all dependencies to qdep packages to be included into your project
 QDEP_PROJECT_SUBDIRS       | in        | `<empty>`                     | Specify all dependencies to qdep projects to be added as qmake project to the SUBDIRS variable. Only evaluted in projects that specify TEMPLATE as `subdirs`
 QDEP_PROJECT_ROOT          | in        | `<empty>`                     | The path to a project qmake project directory or file to resolve QDEP_PROJECT_LINK_DEPENDS against
 QDEP_PROJECT_LINK_DEPENDS  | in        | `<empty>`                     | Sepcify all dependencies to qdep projects this project should be linked against. The dependencies are assumed to be provided in that project via QDEP_PROJECT_SUBDIRS. 
 QDEP_DEFINES               | in        | `<empty>`                     | Specify DEFINES that are exported if the library exports a pri file. All values are automatically added to DEFINES by qdep
 QDEP_INCLUDEPATH           | in        | `<empty>`                     | Specify INCLUDEPATHS that are exported if the library exports a pri file. All values are automatically added to INCLUDEPATH by qdep 
 QDEP_EXPORTS               | in        | `<empty>`                     | Specify qdep dependencies of which the API should be exported. Can be useful to export packages when used in dynamic libraries - only works if packages explicitly support this
 QDEP_PACKAGE_EXPORTS       | in (pkg)  | `<empty>`                     | Variables to be defined as import/export/nothing and be used as prefix to a class. See TODO
 QDEP_TRANSLATIONS          | in (pkg)  | `<empty>`                     | Specify translation subfiles within a qdep dependency to be merged with the translations of the project they are included from
 QDEP_PROJECT_DEPENDS       | in (pkg)  | `<empty>`                     | Specify all dependencies to qdep projects this qdep project depends on. Can only be used in qdep project dependencies and adds it's contents to QDEP_PROJECT_SUBDIRS of the project that includes this dependency 
 QDEP_VAR_EXPORTS           | in (pkg)  | `<empty>`                     | Specify the names of additional qmake variables that should be exported from a qdep dependency besides DEFINES and INCLUDEPATH

##### SUBDIRS extension
- `qdep_depends`: Can be added to any variable passed to `SUBDIRS` in a project that uses `QDEP_PROJECT_SUBDIRS` to specify that a certain subdir project depends on that specific package. This does **not** take care of linkage etc. It only ensures that the make targets are build in the correct order.

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

#### Configuration values
##### Input value
- `qdep_force`: Enforce the full evaluation of qdep, even if the pro file is beeing evaluated without a context (This is potentially dangerous and should not be used unless absolutely neccessary)
- `qdep_no_pull`: Do not pull for newer versions of branch-based dependencies. Cloning new packages will still work
- `qdep_no_clone`: Do not clone completely new packages or package versions. Pulling on already cached branches will still work
- `qdep_no_cache`: Do not cache the used versions of packages without a specified versions. Instead the latest version is queried on every run
- `qdep_export_all`: export all dependant packages, i.e. any QDEP_PACKAGE_EXPORTS for every package are treated as if added to QDEP_EXPORTS
- `qdep_no_link`: When exporting packages from a library, do not add the qmake code to link the library (and to it's includes) to the generate export.pri file
- `qdep_link_private`: When creating a library export file, instead of adding the library itself to LIBS, it is added to LIBS_PRIVATE
- `qdep_no_qm_combine`: Do not combine TRANSLATIONS with QDEP_TRANSLATIONS. Instead treat QDEP_TRANSLATIONS as EXTRA_TRANSLATIONS and generate seperate qm files for them
- `qdep_link_export`: Enforce the creation of an export pri file. Normally only libraries without qdep_no_link defined or projects that specify qdep_export_all or have values in QDEP_EXPORTS generate such files

##### Output values
- `qdep_build`: Is set in case the qdep features was loaded correctly and is enabled

#### Environment variables
- `QDEP_CACHE_DIR`: The directory where to cache downloaded sources. Is automatically determined for every system but can be overwritten with this variable
- `QDEP_SOURCE_OVERRIDE`: Allows to provide a mapping in the format `<pkg1>;<pkg2>^<pkg3>;<pkg4>`. This will make qdep automatically replace any occurance of `pkg1` with `pkg2` etc. Can be used by developers to temporarily overwrite packages
- `QDEP_DEFAULT_PKG_FN`: A template that is used to resolve non-url packages like `User/package` to a full url. The default method for that is `https://github.com/{}.git` - with `{}` being replaced by the short package name.

#### Internal
##### Variables
- `__QDEP_PRIVATE_SEPERATOR`: Seperator between datasets
- `__QDEP_TUPLE_SEPERATOR`: Seperator between values within a dataset
- `__QDEP_INCLUDE_CACHE`: objects with details about included depdendencies of all kinds
- `__QDEP_ORIGINAL_TRANSLATIONS`: All original translation that were in TRANSLATIONS before apply translation combination with QDEP_TRANSLATIONS from included packages
- `__QDEP_HOOK_FILES`: Paths to header files that contain hook definitions that must be included and loaded by a project

##### Configuration values
- `__qdep_script_version`: The version detected at runtime as reported by the qdep executable
- `__qdep_dump_dependencies`: Create a file named qdep_depends.txt in the build directory that contains all direct dependencies of the project

##### QMAKE test functions
- `qdepCollectDependencies(dependencies ...)`: Downloads all specified normal dependencies and adds them to `__QDEP_INCLUDE_CACHE` to be linked later by qdep. Works recursively
- `qdepCollectProjectDependencies(dependencies ...)`: Downloads all specified project dependencies and adds them to `SUBDIRS`. Works recursively
- `qdepResolveSubdirDepends(subdir-vars ...)`: Converts the values of the `qdep_depends` subvar of all variables passed to the function to normal subdirs `depends` subvars
- `qdepCreateExportPri(path)`: Creates a file named path and adds all export-related code to it
- `qdepDumpUpdateDeps()`: Creates a file named qdep_depends.txt in the build directory that contains all direct dependencies of the project

##### QMAKE replace functions
- `qdepResolveProjectLinkDeps(project-root, link-depends ...)`: Resolves all link-depends project packages to subdir paths, assuming they are provided by the project located at project-root
- `qdepOutQuote(name, values)`: Creates a number of lines of qmake code that assing each value in values to a variable named name, in a securely quoted manner
- `qdepLinkExpand(path)`: Expands a shortened or relative path to a project that exports dependencies to get the path of the export pri file
- `qdepResolveLinkRoot(path)`: Searches for a top-level qmake project, that has this project included as project dependency and returns the path to that pro file. Search is started based on path, which must be a build directory
