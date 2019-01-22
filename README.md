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

### Preparing qmake
After installing (except when using the AUR-package), you have to "enable" qdep for each Qt-Kit you want to use qdep with. This can be done by opening a terminal and calling:
```bash
qdep prfgen --qmake "</path/to/qmake>"
```
For example, if you have installed Qt 5.12.0 for MSVC 2017 x64 on windows in the default location (`C:\Qt`), the command would look like this:
```bash
qdep prfgen --qmake "C:\Qt\5.12.0\msvc2017_64\bin\qmake.exe"
```

**Note:** Depending on how the corresponding Qt-Kit was installed, you might need to run the command with administrator/sudo permissions. Alternatively, you can call the command with `--dir /some/path` and export that very same path as value to the `QMAKEPATH` environment variable, if you have no such permissions.

### Shell completitions
For Unix systems, qdep makes use of [argcomplete](https://argcomplete.readthedocs.io/en/latest/) to provide completitions for bash/zsh to activate them, add the following code your shell initializer scripts:

For **zsh**, add this to `~/.zshrc`:
```bash
autoload bashcompinit
bashcompinit
autoload compinit
compinit
eval "$(register-python-argcomplete qdep)"
```

For **bash**, add this to `~/.bashrc`:
```
eval "$(register-python-argcomplete qdep)"
```

When using BASH, you can alternatively use global completition - see [Activating global completion](https://argcomplete.readthedocs.io/en/latest/#activating-global-completion) for more details on that. Other shells might work as well, depending on how well argcomplete works with them. Refer to the argcomplete documentation and their GitHub Repository .

## Getting started
The basic usage of qdep is very simple. For this example, we assume you want to add for example [QHotkey](https://github.com/Skycoder42/QHotkey) to a project via qdep. All you have to do is to install (and prepare) qdep and then add the following two lines to your pro-file:

```qmake
QDEP_DEPENDS += Skycoder42/QHotkey
!load(qdep):error("Failed to load qdep feature")
```

Thats it! The next time you run qmake qdep will automatically download the latest release and add them to your project. Just compile the project and you can use the library. A more explicit way to specify the package (and what that shorter string extends to) would be `https://github.com/Skycoder42/QHotkey.git@1.2.2/qhotkey.pri`

## Getting deeper
Besides this basic functionality of referencing qdep packages, qdep offers a few additional things to make using (and developing) those easier. In the following sections, they will be explained in detail.

### Dependency IDs
Qdep dependencies are described by IDs. These IDs follow the format `<url>[@<version>[/<path>]]`. The only relevant part is the URL, and it can either be implicit or explicit. Implicit URLs follow the format `<user>/<repository>` and are automatically expanded to `https://github.com/<user>/<repository>.git`. For the explicit format, all kinds of GIT-URLs are supportet, i.e. HTTPS, SSH and FILE urls.

If you leave out the path part of a qdep package, qdep assumes that there is a pri file named `<repository_lower>.pri` in the repositories root directory. If that is not the case, or if a package has multiple different pri files to choose from, you can specify a path relative to the repositories root to that pri file to use that one instead of the automatically detected one.

#### Versioning
Qdep supports 3 kinds of versioning: Unversioned, branches, tags. If you leave out the version, qdep will automatically query the corresponding repository and get the latest tag (by "creation") and use that one. If you do specify a version, it can either be a git tag or a git branch. In case of a tag, qdep will simply download it and assume it to be persistant, i.e. never check for updates on that specific tag. Referencing a branch however will lead to qdep "tracking" that branch, and before every build, qdep pulls on the branch to update if neccessary.

Generelly speaking, it is recommended to use explicit tags. Implicit versioning is fine, too, but updates to packages might break your builds at times you do not want them to. Branch versioning is always dangerous and should only be used on explicitly stable branches or for package delevopment.

#### Package-uniqueness and version conflicts
When working with recursive package dependencies, it can sometimes happen that two different packages include different versions of the same package. qdep circumvents this issue by making shure only a single version of each package is ever included. The first version this is referenced is the one that is choosen. Explicit package paths however are not considered the same package, i.e. it is possible to include two different pri files from the same git repository. Generelly speaking, a packages unique identifier is determined by its `<url>` and its `<path>` - both case insensitive.

### Normal dependencies
Normal dependencies, aka pri-dependencies specified via `QDEP_DEPENDS` are the primary dependency type of qdep. They are typically resolve to a simple pri files, that is included into your project by qdep. You can do anything in these pri files you would also in a "normal" pri file. However, there are a few extra things that become possible when including qdep dependencies.

#### Translations
The first feature is extended support for translations. Qdep packages can come with translation source files for their own sources. These are typically exported via the `QDEP_TRANSLATIONS` qmake variable. When creating your own translations, qdep will automatically merge these with your own translations at build time. This however onyl works if you make use of the `lrelease` qmake feature, provided by qt. See [QMake TRANSLATIONS](https://doc.qt.io/qt-5/qmake-variable-reference.html#translations) and [QMake QM_FILES_INSTALL_PAT](https://doc.qt.io/qt-5/qmake-variable-reference.html#qm-files-install-path) for more details.

#### Library support
When using qdep in static or dynamic libraries, there are often special steps needed to make that fully work. However, qdep takes care of those steps and performs them for you. The only thing you need to do is enable library exports from your library and then import that export from your primary project. For example, assuimg you have the following project structure:
```
root (subdirs)
 |-library (lib)
 |-app (app)
```
And you have a library that depends on QHotkey. If you want to use this library from app, you would create the library pro file as follows:
```qmake
TEMPLATE = lib
CONFIG += static  # dynamic libraries are also possible, but dependencies must support exporting for them to work on windows

# ...

QDEP_DEPENDS += Skycoder42/QHotkey
QDEP_EXPORTS += Skycoder42/QHotkey
CONFIG += qdep_link_export
!load(qdep):error("Failed to load qdep feature")
```
And then reference the library in the app pro file. This also takes care of linking the library to the app, so no additional `INCLUDEPATH` or `LIBS` changes are needed:
```qmake
TEMPLATE = app

# ...

QDEP_LINK_DEPENDS += ../library
!load(qdep):error("Failed to load qdep feature")
```
And thats it! You can now use the QHotkey in the library and the app project without any additional work, as qdep will reference the QHotkey that is now embedded into the library project. 

**Note:** This will also work for dynamic librabries, but only if the *explicitly* support qdep package exporting. If not, linking will fail at least on windows, and possibly on other platforms as well.

#### Creating normal dependencies
This section is intended for developers that want to create their own qdep packages. Generally speaking, there is not much you need to do different from creating normal pri includes. However, there are a few small things in qdep you can use to your advantage to create better packages. They are described in the following sub sections and are:

- Translation generation
- Resources and startup hooks
- automatic exports

##### Creating qdep translations
The only difference when creating translations with qdep is where you put them. Instead of TRANSLATIONS, create a qmake variable called QDEP_TRANSLATIONS and add all the ts files you want to generate to it. Next, call the following command to actually generate the ts-files based on your pri file:
```bash
qdep lupdate --qmake "</path/to/qmake>" --pri-file "</path/to/project.pri>" [-- <extra lupdate arguments>...]
```
And thats it. You should now be able to find the generated TS-files where you wanted them to be as specified in the pri file.

When creating packages that should work with and without qdep, you can add the following to your pri file to still make these translations available if the package is included without qdep:
```qmake
!qdep_build: EXTRA_TRANSLATIONS += $$QDEP_TRANSLATIONS
```

##### Resources and hooks
One thing that can be problematic, especially when working with static libraries, is the use of RESOURCES and startup hooks. To make it work, qdep automatically generates code to load them. For resources, there is nothing special you need to do as package developer.

For hooks however, thats a different story. Assuming you have the following function you want to be run as `Q_COREAPP_STARTUP_FUNCTION`:
```cpp
void my_package_startup_hook()
{
    doStuff();
}
```
You will have to add the following line to your qdep pri file to make shure this hook actually gets called:
```pro
QDEP_HOOK_FNS += my_package_startup_hook
```
And with that, qdep will automatically generate the code needed to call this method as `Q_COREAPP_STARTUP_FUNCTION`.

When creating packages that should work with and without qdep, you can add the following to the cpp file that contains the hook function to make it work for non-static projects, even if the package is included without qdep:
```cpp
#ifndef QDEP_BUILD
#include <QCoreApplication>
Q_COREAPP_STARTUP_FUNCTION(my_package_startup_hook)
#endif
```

##### Automatic exports
Another very useful tool are automatic package exports. This allows qdep to automatically export a qdep package from a dynamic library, so other applications that link to that library can use the exported qdep packages API. This is basically equivalent to the following:

```cpp
#ifdef BUILD_PACKAGE_AS_LIBRARY
	#ifdef IS_DLL_BUILD
		#define MY_PACKAGE_EXPORT Q_DECL_EXPORT
	#else
		#define MY_PACKAGE_EXPORT Q_DECL_IMPORT
	#endif
#else
	#define MY_PACKAGE_EXPORT
#endif

class MY_PACKAGE_EXPORT MyClass {
	// ...
};
```

qdep basically automates the define part, so you don't have to care about correctly defining all those macros and your code can be reduced to:
```cpp
class MY_PACKAGE_EXPORT MyClass {
	// ...
};
```
To make it work, simply add the following to your pri file:
```qmake
QDEP_PACKAGE_EXPORTS += MY_PACKAGE_EXPORT
```
And thats it! When using the package normally, qdep will automatically add an empty define that defines MY_PACKAGE_EXPORT to nothing. When building a dynamic library and the end user wants to export the package, it gets defined as Q_DECL_EXPORT (and Q_DECL_IMPORT for consuming applications).

When creating packages that should work with and without qdep, you can add the following to the pri file to manually define the macro to nothing, even if the package is included without qdep:
```qmake
!qdep_build: DEFINES += "MY_PACKAGE_EXPORT="
```

### Project dependencies
Another side of qdep besides normal pri dependencies are full project dependencies. In this scenario, you include a full qmake project into your tree as child of a SUBDIRS projects. This allows the use of qdep package export pri files to link to these projects without much effort. To make use of this feature, you have to use a subdirs project that references the pro dependency, as well as normal projects that link against it. One great advantage of using project dependencies is, that they can reference other project dependencies they depend on, which means even for full projects, qdep takes care of the recursive dependency resolving for you.

To get started, assume the following project structure:
```
root (subdirs)
  |--libs (subdirs)
  |    |--lib (lib)
  |--app (app)
```
Both lib and app are assumed to depend on a theoretical qdep project dependency name `Skycoder42/SuperLib`, but app also depends on lib.

The first step would be to choose a subdirs project to add the dependency to. For this example, the libs project is choosen. Add the following lines to add the dependency:
```qmake
TEMPLATE = subdirs
SUBDIRS += lib

# ....

QDEP_PROJECT_SUBDIRS += Skycoder42/SuperLib
lib.qdep_depends += Skycoder42/SuperLib
!load(qdep):error("Failed to load qdep feature")
```
The `QDEP_PROJECT_SUBDIRS` is used to actually pull in the project dependency, while adding it to `lib.qdep_depends` *only* makes sure that the qdep dependency is built before lib. This is not needed if lib does not depend on the qdep dependency. It is however recommended to always have a seperate subdirs project for qdep dependencies, i.e. for this concrete example it would be better to move the lib project one stage up or create another subdir project within libs that references the qdep dependencies.

Next, we need to reference the library itself in app/lib. The procedure is the same for both, so here it is only shown for the app project as an example. In the app pro file, add the lines:
```qmake
QDEP_PROJECT_ROOT = libs  # Or "./libs" - would be ".." for the lib project
QDEP_PROJECT_LINK_DEPENDS += Skycoder42/SuperLib
!load(qdep):error("Failed to load qdep feature")
```
`QDEP_PROJECT_ROOT` tells qdep where the project is located, that contains the reference to the actual qdep project dependency, and `QDEP_PROJECT_LINK_DEPENDS` list all the dependencies this project (app) depends on. If any dependency listed there was not specified in the libs project via `QDEP_PROJECT_SUBDIRS`, the build will fail.

And with that, the project dependency has been sucessfully added and referenced. With the next build, the project would be downloaded, compiled and linked against app/lib.

#### Creating project dependencies
Generally speaking, project dependencies are just normal qmake projects. However, such a project should **always** include the qdep feature and add `qdep_link_export` to the config, as without the generated export pri file, it will not be usable as qdep project dependency. But besides that, you can do anything you want, i.e. add other normal qdep pri dependencies etc. and even export them if needed.

However, there is one additional feature that is only possible with qdep project dependencies: You can directly reference other qdep project dependencies. Doing so will make sure that whichever subdirs project that includes this project will also include the dependencies as subdirs and ensure the qmake build order, as well as referencing the corresponding export pri files. To for example reference `Skycoder42/SuperLib` from within a qdep project dependency, add the following:
```qmake
QDEP_PROJECT_DEPENDS += Skycoder42/SuperLib
!load(qdep):error("Failed to load qdep feature")
```

## Documentation
In the following sections, all the functions, variables etc. of qdep are documented for reference. 

### Command line interface
qdep has a public and a private command line API. The public API is intended to be used by delevopers, while the internal API is used by the qdep qmake feature to perform various operations. The following sections list all the commands with a short description. For more details on each command, type `qdep <command> --help` 

#### Public API operations:
```
prfgen     Generate a qmake project feature (prf) for the given qmake.
init       Initialize a pro file to use qdep by adding the required lines.
lupdate    Run lupdate for the QDEP_TRANSLATION variable in a given pri
           file.
clear      Remove all sources from the users global cache.
versions   List all known versions/tags of the given package
query      Query details about a given package identifier
get        Download the sources of one ore more packages into the source
           cache.
update     Check for newer versions of used packages and optionally update
           them.
```

#### Private API operations:
```
dephash     Generated unique identifying hashes for qdep
            packages.
pkgresolve  Download the given qdep package and extract relevant
            information from it.
hookgen     Generate a header file with a method to load all
            resource hooks.
hookimp     Generate a source file that includes and runs all
            qdep hooks as normal startup hook.
lconvert    Combine ts files with translations from qdep
            packages.
prolink     Resolve the path a linked project dependency would
            be at.
```

### QMAKE-Feature
This is the documentation of the qmake feature that is generated by qdep and loaded by adding `load(qdep)` to your project. All variables, CONFIG-flags and more are documented below.

#### Variables
##### Common Variables
 Name                       | Direction | Default                       | Descriptions
----------------------------|-----------|-------------------------------|--------------
 QDEP_PATH                  | in/out    | `<system>`                    | Holds the path to the qdep binary to be used. Can be overwritten to specify a custom locations
 QDEP_VERSION               | out       | `<system>`                    | The version of qdep which was used to generate the qdep feature
 QDEP_GENERATED_DIR         | in        | `$$OUT_PWD`                   | The sub-directory in the build folder where qdep should place all it's generated files. Can be an absolute or relative path
 QDEP_EXPORT_PATH           | in        | `$$QDEP_GENERATED_DIR/<type>` | The directory where to place export pri files for libraries that export dependencies. Can be relative to OUT_PWD or absolute. Use QDEP_EXPORT_NAME to get the name of that file without a path
 QDEP_DEPENDS               | in        | `<empty>`                     | Specify all dependencies to qdep packages to be included into your project
 QDEP_LINK_DEPENDS          | in        | `<empty>`                     | Reference other projects in the same build tree that this project should link against. Those projects must be exporting a pri file
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

##### Defines
- `QDEP_BUILD`: Is defined in case the qdep features was loaded correctly and is enabled

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
