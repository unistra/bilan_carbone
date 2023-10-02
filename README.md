# Bilan carbone

## Pré-requis

Python 3.6+

## Installation

`pip install -r requirements.txt`

Documentation d'installation de pyrfc : https://github.com/SAP/PyRFC#download-and-installation

## Utilisation

En paramètre un fichier texte avec deux colonnes séparées par une virgule contiendra la liste des employés et missions.
* Colonne 1 : N° employé
* Colonne 2 : Numéro de mission

Exemple :

```csv
EMPLOYEENUMBER,TRIPNUMBER
12,58717
12,59152
18,56885
18,57005
18,57874
```

Commande :
```
usage: bilan_carbone.py [-h] [-a AHOST] [-s SYSNR] [-c CLIENT] [-u USER]
                        [-p PASSWORD]
                        input_file
```