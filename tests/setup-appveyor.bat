@echo off

python ./qdep.py prfgen

move tests\qdep.pro .\dep.pro
