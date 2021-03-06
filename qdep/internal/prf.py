qdep_prf = """isEmpty(QDEP_TOOL) QDEP_TOOL = $$system_path($$QDEP_PATH)

# verify versions are correct
__qdep_script_version = $$system($$QDEP_TOOL --version)
!equals(QDEP_VERSION, $$__qdep_script_version):error("qdep.py script version ($$__qdep_script_version) is different to qdep.prf version ($$QDEP_VERSION)! Run '$$QDEP_TOOL prfgen --qmake $$QMAKE_QMAKE' to update the prf file!")

# set some variables
isEmpty(QDEP_CACHE_SCOPE): QDEP_CACHE_SCOPE = stash

isEmpty(QDEP_GENERATED_DIR): QDEP_GENERATED_DIR = $$OUT_PWD
debug_and_release:CONFIG(release, debug|release): QDEP_GENERATED_SOURCES_DIR = $${QDEP_GENERATED_DIR}/release
else:debug_and_release:CONFIG(debug, debug|release): QDEP_GENERATED_SOURCES_DIR = $${QDEP_GENERATED_DIR}/debug
else: QDEP_GENERATED_SOURCES_DIR = $$QDEP_GENERATED_DIR
isEmpty(QDEP_GENERATED_TS_DIR): QDEP_GENERATED_TS_DIR = $$QDEP_GENERATED_DIR/.qdepts
debug_and_release:CONFIG(release, debug|release): QDEP_GENERATED_TS_DIR = $${QDEP_GENERATED_TS_DIR}/release
else:debug_and_release:CONFIG(debug, debug|release): QDEP_GENERATED_TS_DIR = $${QDEP_GENERATED_TS_DIR}/debug
isEmpty(QDEP_LUPDATE) {
	qtPrepareTool(QDEP_LUPDATE, lupdate)
	QDEP_LUPDATE += -recursive -locations relative
    qdep_lupdate_no_obsolete: QDEP_LUPDATE += -no-obsolete
}
isEmpty(QDEP_LCONVERT) {
	qtPrepareTool(QDEP_LCONVERT, lconvert)
	QDEP_LCONVERT += -sort-contexts 
}

isEmpty(QDEP_EXPORT_PATH): QDEP_EXPORT_PATH = $$QDEP_GENERATED_DIR
debug_and_release:CONFIG(release, debug|release): QDEP_EXPORT_PATH = $$QDEP_EXPORT_PATH/release
debug_and_release:CONFIG(debug, debug|release): QDEP_EXPORT_PATH = $$QDEP_EXPORT_PATH/debug
isEmpty(QDEP_EXPORT_NAME) {
	__qdep_base_name = $$basename(_PRO_FILE_)
	QDEP_EXPORT_NAME = $$replace(__qdep_base_name, "\\\\.[^\\\\.]*$", "_export.pri")
}

isEmpty(__QDEP_PRIVATE_SEPERATOR): __QDEP_PRIVATE_SEPERATOR = "==="
isEmpty(__QDEP_TUPLE_SEPERATOR): __QDEP_TUPLE_SEPERATOR = "---"

CONFIG += qdep_build
DEFINES += QDEP_BUILD

# The primary dependecy collector function
defineTest(qdepCollectDependencies) {
	# transform all dependencies into unique hashes
	qdep_dependencies = 
	for(arg, ARGS): qdep_dependencies += $$system_quote($$arg)
	qdep_ok = 
	qdep_hashes = $$system($$QDEP_TOOL dephash $$qdep_dependencies, lines, qdep_ok)
	!equals(qdep_ok, 0):return(false)

	for(dep_hash, qdep_hashes) {
		# handle each dependency, but each package only once
		dep_pkg = $$take_first(ARGS)
		!contains(__QDEP_INCLUDE_CACHE, $$dep_hash) {
			# Install the sources and extract some parameters
			dep_extra_args = 
			qdep_no_pull: dep_extra_args += --no-pull
			qdep_no_clone: dep_extra_args += --no-clone
			!isEmpty($${dep_hash}.version): dep_vers_arg = $$system_quote($$first($${dep_hash}.version))
			else: dep_vers_arg =
			qdep_ok = 
			dep_data = $$system($$QDEP_TOOL pkgresolve $$dep_extra_args $$system_quote($$dep_pkg) $$dep_vers_arg, lines, qdep_ok)
			!equals(qdep_ok, 0):return(false)
			!equals(dep_hash, $$take_first(dep_data)):error("Critical internal error: dependencies out of sync"):return(false)

			dep_version = $$take_first(dep_data)
			dep_base = $$take_first(dep_data)
			dep_path = $$take_first(dep_data)
			dep_needs_cache = $$take_first(dep_data)

			$${dep_hash}.package = $$dep_pkg
			$${dep_hash}.version = $$dep_version
			$${dep_hash}.path = $${dep_base}$${dep_path}
			$${dep_hash}.exports = 
			$${dep_hash}.local = 1
			export($${dep_hash}.package)
			export($${dep_hash}.version)
			export($${dep_hash}.path)
			export($${dep_hash}.local)

			# Cache the package version for dependencies with undetermined versions
			!qdep_no_cache:equals(dep_needs_cache, True):!cache($${dep_hash}.version, set $$QDEP_CACHE_SCOPE):warning("Failed to cache package version for $$dep_pkg")

			# Find all dependencies that package depends on and call this method recursively for those
			sub_deps = $$fromfile($$eval($${dep_hash}.path), QDEP_DEPENDS)
			__QDEP_REAL_DEPS_STACK += $$dep_hash			
			!isEmpty(sub_deps):!qdepCollectDependencies($$sub_deps):return(false)			
			__QDEP_INCLUDE_CACHE *= $$take_last(__QDEP_REAL_DEPS_STACK)
			export(__QDEP_INCLUDE_CACHE)

			# Handle all defines for symbol exports, if specified
			sub_exports = $$fromfile($$eval($${dep_hash}.path), QDEP_PACKAGE_EXPORTS)

			qdep_export_all|contains(QDEP_EXPORTS, $$dep_pkg) {
				!static:!staticlib:for(sub_export, sub_exports) {
					DEFINES += "$${sub_export}=Q_DECL_EXPORT"
					QDEP_EXPORTED_DEFINES += "$${sub_export}=Q_DECL_IMPORT"
					$${dep_hash}.exports += $$sub_export
				} else:for(sub_export, sub_exports) {
					DEFINES += "$${sub_export}="
					QDEP_EXPORTED_DEFINES += "$${sub_export}="
				}
			} else:for(sub_export, sub_exports): \\
				DEFINES += "$${sub_export}="
			export(DEFINES)
			export(QDEP_EXPORTED_DEFINES)
			export($${dep_hash}.exports)
		} else: \\
			!equals($${dep_hash}.package, $$dep_pkg): \\
			warning("Detected includes of multiple different versions of the same dependency. Package \\"$$first($${dep_hash}.package)\\" is used, and package \\"$$dep_pkg\\" was detected.")
	}

	return(true)
}

# The dependecy collector function for project dependencies in subdirs projects
defineTest(qdepCollectProjectDependencies) {
	# transform all dependencies into unique hashes
	qdep_dependencies = 
	for(arg, ARGS): qdep_dependencies += $$system_quote($$arg)
	qdep_ok = 
	qdep_hashes = $$system($$QDEP_TOOL dephash --project $$qdep_dependencies, lines, qdep_ok)
	!equals(qdep_ok, 0):return(false)

	for(dep_hash, qdep_hashes) {
		# handle each dependency, but each package only once
		dep_pkg = $$take_first(ARGS)
		!contains(__QDEP_INCLUDE_CACHE, $$dep_hash) {
			# Install the sources and extract some parameters
			dep_extra_args = 
			qdep_no_pull: dep_extra_args += --no-pull
			qdep_no_clone: dep_extra_args += --no-clone
			!isEmpty($${dep_hash}.version): dep_vers_arg = $$system_quote($$first($${dep_hash}.version))
			else: dep_vers_arg =
			qdep_ok = 
			dep_data = $$system($$QDEP_TOOL pkgresolve --project $$dep_extra_args $$system_quote($$dep_pkg) $$dep_vers_arg, lines, qdep_ok)
			!equals(qdep_ok, 0):return(false)
			!equals(dep_hash, $$take_first(dep_data)):error("Critical internal error: project dependencies out of sync"):return(false)

			dep_version = $$take_first(dep_data)
			dep_base = $$take_first(dep_data)
			dep_path = $$take_first(dep_data)
			dep_needs_cache = $$take_first(dep_data)

			$${dep_hash}.package = $$dep_pkg
			$${dep_hash}.version = $$dep_version
			$${dep_hash}.path = $${dep_base}$${dep_path}
			$${dep_hash}.exports = 
			$${dep_hash}.local = 0
			$${dep_hash}.target = sub$${dep_hash}
			export($${dep_hash}.package)
			export($${dep_hash}.version)
			export($${dep_hash}.path)
			export($${dep_hash}.local)
			export($${dep_hash}.target)

			# Cache the package version for dependencies with undetermined versions
			!qdep_no_cache:equals(dep_needs_cache, True):!cache($${dep_hash}.version, set $$QDEP_CACHE_SCOPE):warning("Failed to cache package version for $$dep_pkg")

			# link the project and write the version if not already there
			exists("$$_PRO_FILE_PWD_/.qdep/$${dep_hash}/.version"): linked_version = $$cat("$$_PRO_FILE_PWD_/.qdep/$${dep_hash}/.version", lines)
			else: linked_version =			
			qdep_ok = 
			!equals($${dep_hash}.version, $$linked_version) {
				$${dep_hash}.file = $$system($$QDEP_TOOL prolink --link $$system_quote($${dep_base}) $$system_quote($$_PRO_FILE_PWD_) $${dep_hash} $$system_quote($${dep_path}), lines, qdep_ok)
				!equals(qdep_ok, 0):return(false)
				!write_file("$$_PRO_FILE_PWD_/.qdep/$${dep_hash}/.version", $${dep_hash}.version): \\
					error("Failed to cache project dependency version for $$first($${dep_hash}.package)")
			} else {
				$${dep_hash}.file = $$system($$QDEP_TOOL prolink $$system_quote($$_PRO_FILE_PWD_) $${dep_hash} $$system_quote($${dep_path}), lines, qdep_ok)
				!equals(qdep_ok, 0):return(false)
			}
			export($${dep_hash}.file)

			# Find all further project dependencies that package depends on
			sub_deps = $$fromfile($$eval($${dep_hash}.path), QDEP_PROJECT_DEPENDS)
			!isEmpty(sub_deps) {
				qdep_ok = 
				$${dep_hash}.depends = $$system($$QDEP_TOOL dephash --project $$sub_deps, lines, qdep_ok)
				!equals(qdep_ok, 0):return(false)
				export($${dep_hash}.depends)
			}
			SUBDIRS += $${dep_hash}
			export(SUBDIRS)
			__QDEP_INCLUDE_CACHE += $${dep_hash}
			export(__QDEP_INCLUDE_CACHE)

			# calls this method recursively for all dependencies
			!qdepCollectProjectDependencies($$sub_deps):return(false)	
		} else: \\
			!equals($${dep_hash}.package, $$dep_pkg): \\
			warning("Detected includes of multiple different versions of the same dependency. Package \\"$$first($${dep_hash}.package)\\" is used, and package \\"$$dep_pkg\\" was detected.")
	}

	return(true)
}

# resolve qdep_depends of subdir dependencies to the actual hashes
defineTest(qdepResolveSubdirDepends) {
	for(subproj, 1) {
		!isEmpty($${subproj}.qdep_depends) {
			qdep_dependencies = 
			for(arg, $${subproj}.qdep_depends): qdep_dependencies += $$system_quote($$arg)
			qdep_ok = 
			$${subproj}.depends += $$system($$QDEP_TOOL dephash --project $$qdep_dependencies, lines, qdep_ok)
			!equals(qdep_ok, 0):return(false)
			export($${subproj}.depends)
		}
	}
	return(true)
}

# pass the root dir and dependencies and create QDEP_LINK_DEPENDS values from it
defineReplace(qdepResolveProjectLinkDeps) {
	qdep_dependencies = 
	for(arg, 2): qdep_dependencies += $$system_quote($$arg)
	qdep_ok = 
	dep_tuples = $$system($$QDEP_TOOL dephash --project --pkgpath $$qdep_dependencies, lines, qdep_ok)
	!equals(qdep_ok, 0):return()

	link_paths = 
	for(qdep_tuple, dep_tuples) {
		tpl_args = $$split(qdep_tuple, ";")
		dep_hash = $$take_first(tpl_args)
		dep_path = $$join(tpl_args, ";")
		qdep_ok = 
		link_paths += $$system($$QDEP_TOOL prolink $$system_quote($$absolute_path($$1, $$_PRO_FILE_PWD_)) $${dep_hash} $$system_quote($${dep_path}), lines, qdep_ok)
		!equals(qdep_ok, 0):return()
	}

	return($$link_paths)
}

# Write a quoted value for the given variable name as a single value
defineReplace(qdepOutQuote) {
	result = 
	var_name = $$1
	isEmpty(4): \\
		intendent = $$escape_expand(\\t)
	else {
		intendent = 
		for(x, "1..$$4"): \\
			intendent = "$$intendent$$escape_expand(\\t)"
	}
	equals(3, prepend): \\
		for(value, 2): result += "$$intendent$$var_name = $${LITERAL_DOLLAR}$${LITERAL_DOLLAR}quote($$value) $${LITERAL_DOLLAR}$${LITERAL_DOLLAR}$$var_name"
	else:equals(3, star): \\
		for(value, 2): result += "$$intendent$$var_name *= $${LITERAL_DOLLAR}$${LITERAL_DOLLAR}quote($$value)"
	else:equals(3, pop): \\
		for(value, 2): result += "$$intendent$${LITERAL_DOLLAR}$${LITERAL_DOLLAR}take_last($$var_name)"
	else: \\
		for(value, 2): result += "$$intendent$$var_name += $${LITERAL_DOLLAR}$${LITERAL_DOLLAR}quote($$value)"
	return($$result)
}

# A function to create a pri file to include the library and all exported
defineTest(qdepCreateExportPri) {
	# write include guard
	out_file_data = "!contains(__QDEP_EXPORT_QMAKE_INCLUDE_GUARD, $${LITERAL_DOLLAR}$${LITERAL_DOLLAR}PWD) {"
	out_file_data += $$qdepOutQuote(__QDEP_EXPORT_QMAKE_INCLUDE_GUARD, $${LITERAL_DOLLAR}$${LITERAL_DOLLAR}PWD)
	
	# write dependencies
	!static:!staticlib: \\
		out_file_data += $$qdepOutQuote(__QDEP_IS_DYNAMIC_EXPORT_INCLUDE_STACK, true)
	for(link_dep, QDEP_LINK_DEPENDS): \\
		out_file_data += "$$escape_expand(\\t)include($$qdepLinkExpand($$link_dep))"
	!static:!staticlib: \\
		out_file_data += $$qdepOutQuote(__QDEP_IS_DYNAMIC_EXPORT_INCLUDE_STACK, true, pop)
	
	# write basic variables
	out_file_data += $$qdepOutQuote(DEFINES, $$QDEP_EXPORTED_DEFINES $$QDEP_DEFINES)
	out_file_data += $$qdepOutQuote(INCLUDEPATH, $$QDEP_EXPORTED_INCLUDEPATH $$QDEP_INCLUDEPATH)
	out_file_data += $$qdepOutQuote(LIBS, $$QDEP_EXPORTED_LIBS $$QDEP_LIBS)
	for(exp_var_key, QDEP_VAR_EXPORTS): out_file_data += $$qdepOutQuote($$exp_var_key, $$eval($$exp_var_key))

	# write package cache
	for(dep_hash, __QDEP_INCLUDE_CACHE):equals($${dep_hash}.local, 1) {
		out_file_data += $$qdepOutQuote($${dep_hash}.package, $$eval($${dep_hash}.package))
		out_file_data += $$qdepOutQuote($${dep_hash}.version, $$eval($${dep_hash}.version))
		out_file_data += $$qdepOutQuote($${dep_hash}.path, $$eval($${dep_hash}.path))
		out_file_data += $$qdepOutQuote($${dep_hash}.exports, $$eval($${dep_hash}.exports))
		out_file_data += $$qdepOutQuote($${dep_hash}.local, 0)
		out_file_data += $$qdepOutQuote(__QDEP_INCLUDE_CACHE, $$dep_hash)
	}

	# write library linkage common parts
	isEmpty(DESTDIR) {
		out_libdir = $$OUT_PWD
		debug_and_release:CONFIG(release, debug|release): out_libdir = $${out_libdir}/release
		else:debug_and_release:CONFIG(debug, debug|release): out_libdir = $${out_libdir}/debug
	} else: out_libdir = $$absolute_path($$DESTDIR, $$OUT_PWD)
		
	!qdep_no_link {
		# write includepath
		out_file_data += $$qdepOutQuote(INCLUDEPATH, $$_PRO_FILE_PWD_)
	
		# write QT, PKGCONFIG and QDEP_LIBS (unless disabled)
		!qdep_no_export_link {
			qt: out_file_data += $$qdepOutQuote(QT, $$QT, star)
			link_pkgconfig: out_file_data += $$qdepOutQuote(PKGCONFIG, $$PKGCONFIG, star)
		}
	}

	# write static/dynamic specific library extra stuff
	static|staticlib:equals(TEMPLATE, lib) {
		out_file_data += "$$escape_expand(\\t)isEmpty(__QDEP_IS_DYNAMIC_EXPORT_INCLUDE_STACK) {"
		
		# write startup hooks
		debug_and_release:CONFIG(release, debug|release): out_file_data += "$$qdepOutQuote(__QDEP_HOOK_FILES, $$QDEP_GENERATED_DIR/release/qdep_$${TARGET}_hooks.h, "", 2)"
		else:debug_and_release:CONFIG(debug, debug|release): out_file_data += "$$qdepOutQuote(__QDEP_HOOK_FILES, $$QDEP_GENERATED_DIR/debug/qdep_$${TARGET}_hooks.h, "", 2)"
		else: out_file_data += "$$qdepOutQuote(__QDEP_HOOK_FILES, $$QDEP_GENERATED_DIR/qdep_$${TARGET}_hooks.h, "", 2)"
		
		# linkage
		!qdep_no_link {
			out_file_data += $$qdepOutQuote(DEPENDPATH, $$_PRO_FILE_PWD_, "", 2)

			win32-g++: out_file_data += $$qdepOutQuote(PRE_TARGETDEPS, "$${out_libdir}/lib$${TARGET}.a", "", 2)
			else:win32: out_file_data += $$qdepOutQuote(PRE_TARGETDEPS, "$${out_libdir}/$${TARGET}.lib", "", 2)
			else:unix: out_file_data += $$qdepOutQuote(PRE_TARGETDEPS, "$${out_libdir}/lib$${TARGET}.a", "", 2)

			out_file_data += $$qdepOutQuote(LIBS, "-l$${TARGET}", prepend, 2)
			out_file_data += $$qdepOutQuote(LIBS, "-L$${out_libdir}/", prepend, 2)
		}
		
		out_file_data += "$$escape_expand(\\t)}"
	} else {
		# linkage
		!qdep_no_link {
			equals(TEMPLATE, lib):out_file_data += $$qdepOutQuote(LIBS, "-l$${TARGET}", prepend)
			else {
				win32: bin_suffix = .exe
				out_file_data += $$qdepOutQuote(LIBS, "-l:$${TARGET}$${bin_suffix}", prepend)
			}
			out_file_data += $$qdepOutQuote(LIBS, "-L$${out_libdir}/", prepend)
		}
	}

	out_file_data += "}"
	write_file($$1, out_file_data):return(true)
	else:return(false)
}

# get the full pri path of a link dependency
defineReplace(qdepLinkExpand) {
	base_path = $$1
	suffix = $$str_member($$base_path, -4, -1)

	!equals(suffix, ".pri") {
		equals(suffix, ".pro") {
			file_name = $$basename(base_path)
			file_name = "$$str_member($$file_name, 0, -5)_export.pri"
			base_path = $$dirname(base_path)
		} else {
			file_name = "$$basename(base_path)_export.pri"
		}
		debug_and_release:CONFIG(release, debug|release): base_path = $$base_path/release/$$file_name
		else:debug_and_release:CONFIG(debug, debug|release):  base_path = $$base_path/debug/$$file_name
		else: base_path = $$base_path/$$file_name
	}

	base_path = $$absolute_path($$base_path, $$_PRO_FILE_PWD_)
	s_base_path = $$shadowed($$base_path)
	!isEmpty(s_base_path):exists($$s_base_path):return($$s_base_path)
	else:!isEmpty(base_path):exists($$base_path):return($$base_path)
	else:return()
}

# find the SUBDIRS project build directory that this qdep project was linked from
defineReplace(qdepResolveLinkRoot) {
	path_segments = $$split(1, "/")
	path_count = $$size(path_segments)
	c_path = $$1
	check_next = 0
	for(index, 0..$$path_count) {
		equals(check_next, 1): \\
			exists("$$c_path/Makefile"): \\
			return($$c_path)

		c_name = $$basename(c_path)
		equals(c_name, ".qdep"): check_next = 1
		else: check_next = 0
		c_path = $$dirname(c_path)
		!exists($$c_path):return()
	}
	return()
}

# shell_escape a list of files
defineReplace(qdepShellQuote) {
	out_files = 
	for(input, ARGS): out_files += $$shell_quote($$absolute_path($$input, $$_PRO_FILE_PWD_))
	return($$out_files)
}

# dump dependencies for update collection
defineTest(qdepDumpUpdateDeps) {
	dump_data = $$_PRO_FILE_
	dump_data += $$QDEP_DEPENDS
	dump_data += $$QDEP_PROJECT_SUBDIRS
	dump_data += $$QDEP_PROJECT_LINK_DEPENDS
	dump_data += $$QDEP_PROJECT_DEPENDS
	write_file($$OUT_PWD/qdep_depends.txt, dump_data):return(true)
	else:return(false)
}

# dump deps if in update mode
__qdep_dump_dependencies: \\
	!qdepDumpUpdateDeps(): \\
	error("Failed to dump dependencies")

# First transform project link depends to normal link depends
!isEmpty(QDEP_PROJECT_ROOT): \\
	!isEmpty(QDEP_PROJECT_LINK_DEPENDS): \\
	QDEP_LINK_DEPENDS = $$qdepResolveProjectLinkDeps($$QDEP_PROJECT_ROOT, $$QDEP_PROJECT_LINK_DEPENDS) $$QDEP_LINK_DEPENDS  # always prepend project link depends

# Second transform project depends to normal link depends
# This will only work if the project is imported as qdep project dependency
!isEmpty(QDEP_PROJECT_DEPENDS) {
	__qdep_project_link_root = $$qdepResolveLinkRoot($$OUT_PWD)
	isEmpty(__qdep_project_link_root): warning("Failed to find including subdirs project - only use QDEP_PROJECT_DEPENDS in qdep project depenencies")
	else: QDEP_LINK_DEPENDS = $$qdepResolveProjectLinkDeps($$__qdep_project_link_root, $$QDEP_PROJECT_DEPENDS) $$QDEP_LINK_DEPENDS  # always prepend project link depends
}

# Next collect all indirect dependencies
# for GCC: create a link group, as these all add libs in arbitrary order
!isEmpty(QDEP_LINK_DEPENDS): \\
	for(link_dep, QDEP_LINK_DEPENDS): \\
	!include($$qdepLinkExpand($$link_dep)): \\
	error("Failed to include linked library $$link_dep")

# Collect all dependencies and then include them
!isEmpty(QDEP_DEPENDS): {
	__qdep_cached_hooks = $$QDEP_HOOK_FNS
	QDEP_HOOK_FNS = 
	__qdep_cached_resources = $$RESOURCES
	RESOURCES = 

	!qdepCollectDependencies($$QDEP_DEPENDS):error("Failed to collect all dependencies")
	else:for(dep, __QDEP_INCLUDE_CACHE):equals($${dep}.local, 1) {
		__qdep_define_offset = $$size(DEFINES)
		__qdep_include_offset = $$size(INCLUDEPATH)
		__qdep_libs_offset = $$size(LIBS)
		include($$first($${dep}.path)) {
			qdep_export_all|contains(QDEP_EXPORTS, $$first($${dep}.package)) {
				QDEP_EXPORTED_DEFINES += $$member(DEFINES, $$__qdep_define_offset, -1)
				export(QDEP_EXPORTED_DEFINES)
				QDEP_EXPORTED_INCLUDEPATH += $$member(INCLUDEPATH, $$__qdep_include_offset, -1)
				export(QDEP_EXPORTED_INCLUDEPATH)
				QDEP_EXPORTED_LIBS += $$member(LIBS, $$__qdep_libs_offset, -1)
				export(QDEP_EXPORTED_LIBS)
			}
		} else:error("Failed to include pri file $$first($${dep}.package)")
	}

	QDEP_HOOK_FNS += $$__qdep_cached_hooks
	RESOURCES += $$__qdep_cached_resources
}

# Collect all project dependencies
equals(TEMPLATE, subdirs):!isEmpty(QDEP_PROJECT_SUBDIRS) {
	!qdepCollectProjectDependencies($$QDEP_PROJECT_SUBDIRS): \\
		error("Failed to collect all project dependencies")
	!qdepResolveSubdirDepends($$SUBDIRS): \\
		error("Failed to link all project dependencies")
}

# create special target for resource hooks in static libs
# or if not, reference their hooks of static libs (as special compiler, only for non-static apps/libs)
static|staticlib:equals(TEMPLATE, lib) {
	__qdep_hook_generator_c.name = qdep hookgen ${QMAKE_FILE_IN}
	__qdep_hook_generator_c.input = _PRO_FILE_ RESOURCES 
	__qdep_hook_generator_c.variable_out = HEADERS
	__qdep_hook_generator_c.commands = $$QDEP_PATH hookgen --hooks $$QDEP_HOOK_FNS -- $${TARGET} ${QMAKE_FILE_OUT} ${QMAKE_FILE_IN}
	__qdep_hook_generator_c.output = $$QDEP_GENERATED_SOURCES_DIR/qdep_$${TARGET}_hooks.h
	__qdep_hook_generator_c.CONFIG += target_predeps combine no_link
	__qdep_hook_generator_c.depends += $$QDEP_PATH
	QMAKE_EXTRA_COMPILERS += __qdep_hook_generator_c
} else:!equals(TEMPLATE, aux) {
	__qdep_hook_importer_c.name = qdep hookimp ${QMAKE_FILE_IN}
	__qdep_hook_importer_c.input = _PRO_FILE_ __QDEP_HOOK_FILES
	__qdep_hook_importer_c.variable_out = GENERATED_SOURCES
	__qdep_hook_importer_c.commands = $$QDEP_PATH hookimp --hooks $$QDEP_HOOK_FNS -- ${QMAKE_FILE_OUT} ${QMAKE_FILE_IN}
	__qdep_hook_importer_c.output = $$QDEP_GENERATED_SOURCES_DIR/qdep_imported_hooks.cpp
	__qdep_hook_importer_c.CONFIG += target_predeps combine
	__qdep_hook_importer_c.depends += $$QDEP_PATH
	QMAKE_EXTRA_COMPILERS += __qdep_hook_importer_c
}

# Create lupdate target
__qdep_lupdate_target.target = lupdate
__qdep_lupdate_target.commands = $$QDEP_LUPDATE $$qdepShellQuote($$_PRO_FILE_PWD_ $$QDEP_LUPDATE_INPUTS) -ts $$qdepShellQuote($$TRANSLATIONS)
__qdep_lupdate_target.depends += $$QDEP_LUPDATE_EXE $$_PRO_FILE_PWD_ $$QDEP_LUPDATE_INPUTS
QMAKE_EXTRA_TARGETS += __qdep_lupdate_target

# fix for broken lrelease make feature
{
	isEmpty(LRELEASE_DIR): LRELEASE_DIR = .qm
	debug_and_release:CONFIG(release, debug|release): __qdep_lrelease_real_dir = $${LRELEASE_DIR}/release
	else:debug_and_release:CONFIG(debug, debug|release): __qdep_lrelease_real_dir = $${LRELEASE_DIR}/debug
	else: __qdep_lrelease_real_dir = $$LRELEASE_DIR
	__qdep_lrelease_real_dir = $$absolute_path($$__qdep_lrelease_real_dir, $$OUT_PWD)
	!exists($$__qdep_lrelease_real_dir): \\
		!mkpath($$__qdep_lrelease_real_dir): \\
		warning("Failed to create lrelease directory: $$__qdep_lrelease_real_dir")
}
qm_files.CONFIG += no_check_exist

# Create special targets for translations
!qdep_no_qm_combine {
	# move translations into temporary var for the compiler to work
	__QDEP_ORIGINAL_TRANSLATIONS = $$TRANSLATIONS
	TRANSLATIONS = 

	# compiler for combined translations
	__qdep_qm_combine_c.name = qdep lrelease ${QMAKE_FILE_IN}
	__qdep_qm_combine_c.input = __QDEP_ORIGINAL_TRANSLATIONS 
	__qdep_qm_combine_c.variable_out = TRANSLATIONS
	__qdep_qm_combine_c.commands = $$QDEP_PATH lconvert --combine $$qdepShellQuote($$QDEP_TRANSLATIONS) -- ${QMAKE_FILE_IN} ${QMAKE_FILE_OUT} $$QDEP_LCONVERT
	__qdep_qm_combine_c.output = $$QDEP_GENERATED_TS_DIR/${QMAKE_FILE_BASE}.ts
	__qdep_qm_combine_c.CONFIG += no_link
	__qdep_qm_combine_c.depends += $$QDEP_PATH $$QDEP_LCONVERT_EXE $$QDEP_TRANSLATIONS
	QMAKE_EXTRA_COMPILERS += __qdep_qm_combine_c

	# copy from lrelease.prf - needed as TRANSLATIONS is now empty
	for(translation, $$list($$__QDEP_ORIGINAL_TRANSLATIONS $$EXTRA_TRANSLATIONS)) {
		translation = $$basename(translation)
		QM_FILES += $$__qdep_lrelease_real_dir/$$replace(translation, \\\\..*$, .qm)
	}
} else {
	# add qdep translations to extra to allow lrelease processing
	EXTRA_TRANSLATIONS += $$QDEP_TRANSLATIONS
}

# Create qdep pri export, if modules should be exported
equals(TEMPLATE, lib):!qdep_no_link|qdep_link_export|qdep_export_all|!isEmpty(QDEP_EXPORTS): \\
	!qdepCreateExportPri($$QDEP_EXPORT_PATH/$$QDEP_EXPORT_NAME): \\
	error("Failed to create export file $$QDEP_EXPORT_FILE")

DEFINES += $$QDEP_DEFINES
INCLUDEPATH += $$QDEP_INCLUDEPATH
LIBS += $$QDEP_LIBS
"""
