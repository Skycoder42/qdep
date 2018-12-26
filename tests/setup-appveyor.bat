@echo off

./qdep.py prfgen --qmake (where /f qmake)

move tests\qdep.pro .\dep.pro
