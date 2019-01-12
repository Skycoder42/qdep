@echo off

C:\Python37-x64\Scripts\pip.exe install appdirs lockfile argcomplete setuptools || exit /B 1
move tests\qdep.pro .\dep.pro || exit /B 1

:: install qdep module
C:\Python37-x64\Scripts\pip.exe install -e . || exit /B 1
C:\Python37-x64\Scripts\qdep.exe prfgen --qmake "C:\projects\Qt\%QT_VER%\%PLATFORM%\bin\qmake" || exit /B 1
