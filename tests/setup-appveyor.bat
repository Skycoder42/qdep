@echo off

:: install dependencies
C:\Python37-x64\Scripts\pip.exe install appdirs lockfile argcomplete setuptools || exit /B 1
C:\Python37-x64\Scripts\pip.exe uninstall -y qdep || exit /B 1

:: install/prepare qdep
C:\Python37-x64\Scripts\pip.exe install -e . || exit /B 1
C:\Python37-x64\Scripts\qdep.exe prfgen --qmake "C:\projects\Qt\%QT_VER%\%PLATFORM%\bin\qmake" || exit /B 1

:: move project file
move tests\qdep.pro .\dep.pro || exit /B 1
