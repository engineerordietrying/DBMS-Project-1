
# VCT Master Player Performance UI

This is a UI is to view the Player's Performance for VCT Masters Shanghai and Madrid.

## Setup Instructions

1. **Clone the repository:**

   ```bash
   git clone https://github.com/engineerordietrying/DBMS-Project-1
   cd Projects-1
   ```

2. **Import the Database:**

   - Create a new database within MySQL:
     ```sql
     CREATE DATABASE <new_database>;
     ```

   - Exit MySQL and return to the terminal.

   - Run the following command to import the database dump:
     ```bash
     mysql -u username -p new_database < vctmastersproj.sql
     ```


## User Accounts

| Username  | Password  | Role        | Permissions                          		       |
|-----------|-----------|-------------|--------------------------------------------------------|
|  admin    |   admin   | Staff       | Able to access staff functions (CRUD Operations)       |

## Required Libraries
- tkinter
- mysql-connector

## What to install

import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkFont

## Start the UI

run vctmastersproj.py
