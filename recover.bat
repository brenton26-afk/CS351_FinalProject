@echo off

:: This is ran whenever a currupted file is detected OR if manually ran
:: This should sync, then repair.
:: Then this should restore...? Maybe add this part to the python script?
echo This will now try to recover a file(s).
echo !!!!!!!!!!!!!!!!!!!!STOP HERE!!!!!!!!!!!!!!!!!!!!! YOU FOUND THE ISSUE!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

::call the python file that takes the file name. trys to repair it.
:: if yes then yay
:: if no
:: versioning from the bucket. -> sync it.