# qdep
A very basic yet simple to use dependency management tool for qmake based projects

## vardump
- prf: qdep (explicit load)
- vars: QDEP_PATH, QDEP_VERSION, QDEP_CACHE_SCOPE, QDEP_TOOL, QDEP_DEPENDS
- config: qdep_no_cache, qdep_build
- tests: qdepCollectDependencies
- replaces: 
- private:
    - vars: __QDEP_INCLUDE_CACHE, __QDEP_REAL_DEPS_STACK, __QDEP_REAL_DEPS