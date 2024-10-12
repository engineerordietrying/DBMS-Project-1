import mysql.connector
from mysql.connector import Error
import tkinter as tk
from tkinter import *
from tkinter import ttk, messagebox
import tkinter.font as tkFont

# Function to connect to the database
def connect_to_database(user, password):
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user=user,  # MariaDB username
            password=password,  # MariaDB password
            database="vctmastersproj"  # Name of the database
        )
        if connection.is_connected():
            return connection
    except Error as e:
        messagebox.showerror("Connection Error", f"Error connecting to the database: {e}")
        return None

# Get list of table names from the database
def get_table_names(connection):
    cursor = connection.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    cursor.close()
    return [table[0] for table in tables]

# Display sorted table data with column sorting functionality
def display_sorted_table_data(connection, table_name, canvas_frame, sort_column=None, reverse=False):
    cursor = connection.cursor()
    query = f"SELECT * FROM `{table_name}`"  # Use backticks for table name
    cursor.execute(query)

    columns = [i[0] for i in cursor.description]
    rows = cursor.fetchall()

    if sort_column is not None:
        column_index = columns.index(sort_column)
        rows.sort(key=lambda row: row[column_index], reverse=reverse)

    for widget in canvas_frame.winfo_children():
        widget.destroy()

    data_frame = Frame(canvas_frame)
    data_frame.pack()

    default_font = tkFont.Font()
    column_widths = []
    for idx, col in enumerate(columns):
        max_width = get_column_width(col, default_font)
        for row in rows:
            cell_text = str(row[idx])
            max_width = max(max_width, get_column_width(cell_text, default_font))
        column_widths.append(max_width)

    def sort_by_column(col_name):
        new_reverse = not reverse if col_name == sort_column else False
        display_sorted_table_data(connection, table_name, canvas_frame, col_name, new_reverse)

    for idx, col in enumerate(columns):
        header = Button(data_frame, text=col, relief=RIDGE, width=column_widths[idx] // 10,
                        command=lambda c=col: sort_by_column(c), bg='lightgrey')
        header.grid(row=0, column=idx, sticky='nsew')

    for i, row in enumerate(rows, start=1):
        for j, value in enumerate(row):
            cell = Label(data_frame, text=value, relief=RIDGE, width=column_widths[j] // 10)
            cell.grid(row=i, column=j, sticky='nsew')

    cursor.close()

def get_column_width(text, font):
    return font.measure(text) + 10  # Add some padding

def display_table_data(connection, table_name, canvas_frame):
    display_sorted_table_data(connection, table_name, canvas_frame)

def create_scrollable_frame(tab, connection, table_name):
    canvas = Canvas(tab)
    canvas.pack(side=LEFT, fill=BOTH, expand=1)

    scrollbar = Scrollbar(tab, orient=VERTICAL, command=canvas.yview)
    scrollbar.pack(side=RIGHT, fill=Y)

    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    canvas_frame = Frame(canvas)
    canvas.create_window((0, 0), window=canvas_frame, anchor="nw")

    display_table_data(connection, table_name, canvas_frame)

def create_table_tabs(connection, root):
    notebook = ttk.Notebook(root)
    tables = get_table_names(connection)

    # Existing table tabs
    for table_name in tables:
        tab = Frame(notebook)
        notebook.add(tab, text=table_name)
        create_scrollable_frame(tab, connection, table_name)

    # Search tab
    search = Frame(notebook)
    notebook.add(search, text="Search")
    create_search_section(search)

    # Admin login tab
    login_tab = Frame(notebook)
    notebook.add(login_tab, text="Admin Login")
    create_login_section(login_tab, notebook, connection)  # Pass notebook for CRUD actions

    notebook.pack(expand=1, fill='both')

def clear_entries(entry_widgets):
    for entry in entry_widgets.values():
        entry.delete(0, END)

def clear_inputs_and_output(player_name_entry, team_name_entry):
    player_name_entry.delete(0, END)
    team_name_entry.delete(0, END)

    for widget in output_frame.winfo_children():
        widget.destroy()

def clear_output(result_label):
    result_label.config(text="")

def create_search_section(parent):
    global output_frame  # Declare output_frame as global

    search_frame = Frame(parent, relief=RAISED, borderwidth=2)
    search_frame.pack(fill=X, padx=10, pady=10)

    header_label = Label(search_frame, text="Search", font=("Helvetica", 16))
    header_label.pack(pady=5)

    # Increase width for Player Name entry
    event_name_label = Label(search_frame, text="Player Name:")
    event_name_label.pack(side=LEFT, padx=5)
    event_name_entry = Entry(search_frame, width=40)  # Increased width here
    event_name_entry.pack(side=LEFT, padx=5)

    # Team Name field
    team_name_label = Label(search_frame, text="Team Name:")
    team_name_label.pack(side=LEFT, padx=5)
    team_name_entry = Entry(search_frame, width=40)  # Increased width here
    team_name_entry.pack(side=LEFT, padx=5)

    search_button = Button(search_frame, text="Search",
                           command=lambda: perform_search(event_name_entry.get(), team_name_entry.get()))
    search_button.pack(side=LEFT, padx=5)

    clear_button = Button(search_frame, text="Clear",
                          command=lambda: clear_inputs_and_output(event_name_entry, team_name_entry))
    clear_button.pack(side=LEFT, padx=5)

    global output_frame
    output_frame = Frame(parent)
    output_frame.pack(fill=BOTH, padx=10, pady=10)


# Functionality to perform search
# Functionality to perform search
def perform_search(player_name, team_name):
    cursor = connection.cursor()

    # Initialize an empty list for storing results
    results = []

    # If searching by both player name and team name
    if player_name and team_name:
        query = """
            SELECT DISTINCT e.playername, t.teamname, e.eventname, s.kills, s.death, s.assist, s.firstkill, s.acs
            FROM events e
            JOIN teams t ON e.playername = t.playername
            JOIN stats s ON e.playername = s.playername AND e.eventid = s.eventid
            WHERE e.playername LIKE %s AND t.teamname LIKE %s
        """
        cursor.execute(query, (f"%{player_name}%", f"%{team_name}%"))
        results = cursor.fetchall()

    elif player_name:  # If only player name is provided
        query = """
            SELECT DISTINCT e.playername, t.teamname, e.eventname, s.kills, s.death, s.assist, s.firstkill, s.acs
            FROM events e
            JOIN teams t ON e.playername = t.playername
            JOIN stats s ON e.playername = s.playername AND e.eventid = s.eventid
            WHERE e.playername LIKE %s
        """
        cursor.execute(query, (f"%{player_name}%",))
        results = cursor.fetchall()

    elif team_name:  # If only team name is provided
        query = """
            SELECT DISTINCT t.teamname, t.teamnameabr, e.playername
            FROM teams t
            JOIN events e ON e.playername = t.playername
            WHERE t.teamname LIKE %s
        """
        cursor.execute(query, (f"%{team_name}%",))
        results = cursor.fetchall()

    else:
        messagebox.showwarning("Search Error", "Please enter a player name or team name to search.")
        return

    # Clear previous output
    for widget in output_frame.winfo_children():
        widget.destroy()

    if results:
        canvas = Canvas(output_frame)
        scroll_y = Scrollbar(output_frame, orient=VERTICAL, command=canvas.yview)
        scroll_x = Scrollbar(output_frame, orient=HORIZONTAL, command=canvas.xview)

        results_frame = Frame(canvas)
        canvas.create_window((0, 0), window=results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        header = Label(results_frame, text="Search Results", font=("Helvetica", 14))
        header.grid(row=0, columnspan=8, pady=5)  # Updated column span for more columns

        # Define headers based on what was searched
        if team_name and not player_name:
            Label(results_frame, text="Team Name", relief=RIDGE, width=30).grid(row=1, column=0, sticky='nsew')
            Label(results_frame, text="Team Abbreviation", relief=RIDGE, width=20).grid(row=1, column=1, sticky='nsew')
            Label(results_frame, text="Player Name", relief=RIDGE, width=20).grid(row=1, column=2, sticky='nsew')
        else:
            # For player name search results
            Label(results_frame, text="Player Name", relief=RIDGE, width=10).grid(row=1, column=0, sticky='nsew')
            Label(results_frame, text="Team Name", relief=RIDGE, width=10).grid(row=1, column=1, sticky='nsew')
            Label(results_frame, text="Event Name", relief=RIDGE, width=30).grid(row=1, column=2, sticky='nsew')
            Label(results_frame, text="Kills", relief=RIDGE, width=10).grid(row=1, column=3, sticky='nsew')
            Label(results_frame, text="Deaths", relief=RIDGE, width=10).grid(row=1, column=4, sticky='nsew')
            Label(results_frame, text="Assists", relief=RIDGE, width=10).grid(row=1, column=5, sticky='nsew')
            Label(results_frame, text="First Kill", relief=RIDGE, width=10).grid(row=1, column=6, sticky='nsew')
            Label(results_frame, text="Avg. Combat Score", relief=RIDGE, width=20).grid(row=1, column=7, sticky='nsew')

        # Populate the result rows
        for i, row in enumerate(results, start=2):
            if team_name and not player_name:
                # For team search results
                Label(results_frame, text=row[0], relief=RIDGE, width=30).grid(row=i, column=0,
                                                                               sticky='nsew')  # Team Name
                Label(results_frame, text=row[1], relief=RIDGE, width=20).grid(row=i, column=1,
                                                                               sticky='nsew')  # Team Abbreviation
                Label(results_frame, text=row[2], relief=RIDGE, width=20).grid(row=i, column=2,
                                                                               sticky='nsew')  # Player Name
            else:
                # For player search results
                Label(results_frame, text=row[0], relief=RIDGE, width=10).grid(row=i, column=0,
                                                                               sticky='nsew')  # Player Name
                Label(results_frame, text=row[1], relief=RIDGE, width=10).grid(row=i, column=1,
                                                                               sticky='nsew')  # Team Name
                Label(results_frame, text=row[2], relief=RIDGE, width=25).grid(row=i, column=2,
                                                                               sticky='nsew')  # Event Name
                Label(results_frame, text=row[3], relief=RIDGE, width=10).grid(row=i, column=3, sticky='nsew')  # Kills
                Label(results_frame, text=row[4], relief=RIDGE, width=10).grid(row=i, column=4, sticky='nsew')  # Deaths
                Label(results_frame, text=row[5], relief=RIDGE, width=10).grid(row=i, column=5,
                                                                               sticky='nsew')  # Assists
                Label(results_frame, text=row[6], relief=RIDGE, width=10).grid(row=i, column=6,
                                                                               sticky='nsew')  # First Kill
                Label(results_frame, text=row[7], relief=RIDGE, width=20).grid(row=i, column=7, sticky='nsew')  # ACS

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scroll_y.pack(side=RIGHT, fill=Y)
        scroll_x.pack(side=BOTTOM, fill=X)

        results_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

    else:
        no_results_label = Label(output_frame, text="No results found.")
        no_results_label.pack()


# Function to create a login section for admins
def create_login_section(parent, notebook, connection):
    login_frame = Frame(parent, relief=RAISED, borderwidth=2)
    login_frame.pack(fill=X, padx=10, pady=10)

    Label(login_frame, text="Admin Login", font=("Helvetica", 16)).pack(pady=5)

    Label(login_frame, text="Username:").pack(side=LEFT, padx=5)
    username_entry = Entry(login_frame)
    username_entry.pack(side=LEFT, padx=5)

    Label(login_frame, text="Password:").pack(side=LEFT, padx=5)
    password_entry = Entry(login_frame, show="*")
    password_entry.pack(side=LEFT, padx=5)

    login_button = Button(login_frame, text="Login", command=lambda: login(username_entry, password_entry, notebook, connection))
    login_button.pack(side=LEFT, padx=5)

# Function to handle admin login and display CRUD tab
def login(username_entry, password_entry, notebook, connection):
    user = username_entry.get()
    password = password_entry.get()

    # Here we can add admin user validation, for simplicity assuming any user can login
    if user == "admin" and password == "admin":  # Placeholder credentials
        create_crud_tab(notebook, connection)
        messagebox.showinfo("Login Success", "You are now logged in as admin.")
    else:
        messagebox.showerror("Login Failed", "Invalid credentials!")


# Function to create a new tab with CRUD operations (wk add here)
login
def create_crud_tab(notebook, connection):
    crud_tab = Frame(notebook)
    notebook.add(crud_tab, text="CRUD Operations")

    Label(crud_tab, text="Admin CRUD Operations", font=("Helvetica", 16)).pack(pady=10)

    Button(crud_tab, text="Create", command=lambda: open_create_window(connection)).pack(pady=5)
    # Button(crud_tab, text="Read", command=lambda: messagebox.showinfo("Action", "Read Operation")).pack(pady=5)
    Button(crud_tab, text="Update", command=lambda: open_update_window(connection)).pack(pady=5)
    Button(crud_tab, text="Delete", command=lambda: open_delete_window(connection)).pack(pady=5)


def open_create_window(connection):
    # Create new window
    create_window = Toplevel()
    create_window.title("Create New Entry")

    # Create a dropdown for table selection
    table_label = Label(create_window, text="Select Table:")
    table_label.grid(row=0, column=0, padx=10, pady=5)

    table_names = get_table_names(connection)
    selected_table = StringVar(create_window)
    selected_table.set(table_names[0])  # Set the default value

    table_dropdown = OptionMenu(create_window, selected_table, *table_names,
                                command=lambda table: display_column_inputs(create_window, table, connection))
    table_dropdown.grid(row=0, column=1, padx=10, pady=5)

    # Frame to hold column input fields
    global input_frame
    input_frame = Frame(create_window)
    input_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

    # Button to submit the entry
    submit_button = Button(create_window, text="Submit Entry",
                           command=lambda: submit_entry(connection, selected_table.get()))
    submit_button.grid(row=2, column=0, columnspan=2, pady=10)


# Function to display input fields based on the selected table
def display_column_inputs(window, table_name, connection):
    for widget in input_frame.winfo_children():
        widget.destroy()  # Clear any existing input fields

    cursor = connection.cursor()
    query = f"DESCRIBE {table_name}"
    cursor.execute(query)
    columns = cursor.fetchall()

    global entry_widgets
    entry_widgets = {}

    for i, column in enumerate(columns):
        column_name = column[0]

        # Label for each column
        label = Label(input_frame, text=column_name)
        label.grid(row=i, column=0, padx=5, pady=5)

        # Entry widget for each column
        entry = Entry(input_frame)
        entry.grid(row=i, column=1, padx=5, pady=5)

        # Store entry widgets in a dictionary to retrieve their values later
        entry_widgets[column_name] = entry

    cursor.close()


# Function to submit a new entry to the selected table
def submit_entry(connection, table_name):
    cursor = connection.cursor()

    # Prepare the SQL query
    columns = ', '.join(entry_widgets.keys())
    placeholders = ', '.join(['%s'] * len(entry_widgets))
    query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

    # Retrieve values from the entry widgets
    values = [entry.get() for entry in entry_widgets.values()]

    try:
        # Execute the insert query
        cursor.execute(query, values)
        connection.commit()
        messagebox.showinfo("Success", "Entry created successfully.")
    except Error as e:
        messagebox.showerror("Error", f"Failed to insert entry: {e}")
    finally:
        cursor.close()


def open_update_window(connection):
    # Create new window
    update_window = Toplevel()
    update_window.title("Update Entry")

    # Create a dropdown for table selection
    table_label = Label(update_window, text="Select Table:")
    table_label.grid(row=0, column=0, padx=10, pady=5)

    table_names = get_table_names(connection)
    selected_table = StringVar(update_window)
    selected_table.set(table_names[0])  # Set the default value

    table_dropdown = OptionMenu(update_window, selected_table, *table_names,
                                command=lambda table: display_update_inputs(update_window, table))
    table_dropdown.grid(row=0, column=1, padx=10, pady=5)

    # Frame to hold update input fields
    global update_input_frame
    update_input_frame = Frame(update_window)
    update_input_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

    # Button to submit the update request
    update_button = Button(update_window, text="Update Entry",
                           command=lambda: update_entry(connection, selected_table.get()))
    update_button.grid(row=2, column=0, columnspan=2, pady=10)


def display_update_inputs(window, table_name):
    for widget in update_input_frame.winfo_children():
        widget.destroy()  # Clear any existing input fields

    global update_entry_widgets
    update_entry_widgets = {}

    # Define input fields based on table-specific conditions
    if table_name == "events":
        required_fields = ["playername", "eventname"]
    elif table_name == "stats":
        required_fields = ["eventid", "playername"]
    elif table_name == "players":
        required_fields = ["playername"]
    elif table_name == "teams":
        required_fields = ["teamname"]
    else:
        required_fields = []  # If table doesn't match any known pattern

    for i, field in enumerate(required_fields):
        label = Label(update_input_frame, text=f"Enter {field} to identify:")
        label.grid(row=i, column=0, padx=5, pady=5)

        entry = Entry(update_input_frame)
        entry.grid(row=i, column=1, padx=5, pady=5)

        # Store entry widgets in a dictionary to retrieve their values later
        update_entry_widgets[field] = entry

    # Load other columns for updating
    Button(update_input_frame, text="Load Data", command=lambda: load_update_data(table_name)).grid(
        row=len(required_fields), columnspan=2, pady=10)


def load_update_data(table_name):
    cursor = connection.cursor()
    conditions = []
    values = []

    # Build conditions for identifying the entry
    for field in update_entry_widgets.keys():
        conditions.append(f"{field} = %s")
        values.append(update_entry_widgets[field].get())

    where_clause = " AND ".join(conditions)
    query = f"SELECT * FROM {table_name} WHERE {where_clause}"

    cursor.execute(query, values)
    row = cursor.fetchone()

    if row:
        # Create input fields for all columns in the table
        cursor.execute(f"DESCRIBE {table_name}")
        columns = cursor.fetchall()

        global update_all_widgets
        update_all_widgets = {}

        # Start placing the new widgets after the Load Data button
        start_row = len(update_entry_widgets) + 1  # Adjust to prevent overlap

        for i, column in enumerate(columns):
            column_name = column[0]

            # Label for each column
            label = Label(update_input_frame, text=column_name)
            label.grid(row=i + start_row, column=0, padx=5, pady=5)  # Use start_row to avoid overlap

            # Entry widget for each column
            entry = Entry(update_input_frame)
            entry.grid(row=i + start_row, column=1, padx=5, pady=5)  # Use start_row to avoid overlap

            # Store entry widgets in a dictionary to retrieve their values later
            update_all_widgets[column_name] = entry
            entry.insert(0, row[i])  # Pre-fill the entry with existing data

    else:
        messagebox.showwarning("Load Error", "No matching entry found.")

    cursor.close()


def update_entry(connection, table_name):
    cursor = connection.cursor()

    # Prepare the SQL update query
    set_clause = ', '.join([f"{col} = %s" for col in update_all_widgets.keys()])
    where_clause = ' AND '.join([f"{key} = %s" for key in update_entry_widgets.keys()])

    query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

    # Retrieve values from the entry widgets
    set_values = [entry.get() for entry in update_all_widgets.values()]
    where_values = [update_entry_widgets[field].get() for field in update_entry_widgets.keys()]

    values = set_values + where_values

    try:
        cursor.execute(query, values)
        connection.commit()
        messagebox.showinfo("Success", "Entry updated successfully.")
    except Error as e:
        messagebox.showerror("Error", f"Failed to update entry: {e}")
    finally:
        cursor.close()


def display_delete_inputs(window, table_name):
    for widget in delete_input_frame.winfo_children():
        widget.destroy()  # Clear any existing input fields

    global delete_entry_widgets
    delete_entry_widgets = {}

    # Define input fields based on table-specific conditions
    if table_name == "events":
        required_fields = ["playername", "eventname"]
    elif table_name == "stats":
        required_fields = ["eventid", "playername"]
    elif table_name == "players":
        required_fields = ["playername"]
    elif table_name == "teams":
        required_fields = ["teamname"]
    else:
        required_fields = []  # If table doesn't match any known pattern

    for i, field in enumerate(required_fields):
        label = Label(delete_input_frame, text=f"Enter {field}:")
        label.grid(row=i, column=0, padx=5, pady=5)

        entry = Entry(delete_input_frame)
        entry.grid(row=i, column=1, padx=5, pady=5)

        # Store entry widgets in a dictionary to retrieve their values later
        delete_entry_widgets[field] = entry


def delete_entry(connection, table_name):
    cursor = connection.cursor()

    # Build the delete query based on the selected table
    if table_name == "events":
        query = "DELETE FROM events WHERE playername = %s AND eventname = %s"
        values = (delete_entry_widgets["playername"].get(), delete_entry_widgets["eventname"].get())
    elif table_name == "stats":
        query = "DELETE FROM stats WHERE eventid = %s AND playername = %s"
        values = (delete_entry_widgets["eventid"].get(), delete_entry_widgets["playername"].get())
    elif table_name == "players":
        query = "DELETE FROM players WHERE playername = %s"
        values = (delete_entry_widgets["playername"].get(),)
    elif table_name == "teams":
        query = "DELETE FROM teams WHERE teamname = %s"
        values = (delete_entry_widgets["teamname"].get(),)
    else:
        messagebox.showerror("Error", "Invalid table selected.")
        return

    try:
        cursor.execute(query, values)
        connection.commit()
        messagebox.showinfo("Success", "Entry deleted successfully.")
    except Error as e:
        messagebox.showerror("Error", f"Failed to delete entry: {e}")
    finally:
        cursor.close()
        connection.commit()


def open_delete_window(connection):
    # Create new window
    delete_window = Toplevel()
    delete_window.title("Delete Entry")

    # Create a dropdown for table selection
    table_label = Label(delete_window, text="Select Table:")
    table_label.grid(row=0, column=0, padx=10, pady=5)

    table_names = get_table_names(connection)
    selected_table = StringVar(delete_window)
    selected_table.set(table_names[0])  # Set the default value

    table_dropdown = OptionMenu(delete_window, selected_table, *table_names,
                                command=lambda table: display_delete_inputs(delete_window, table))
    table_dropdown.grid(row=0, column=1, padx=10, pady=5)

    # Frame to hold delete input fields
    global delete_input_frame
    delete_input_frame = Frame(delete_window)
    delete_input_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5)

    # Button to submit the delete request
    delete_button = Button(delete_window, text="Delete Entry",
                           command=lambda: delete_entry(connection, selected_table.get()))
    delete_button.grid(row=2, column=0, columnspan=2, pady=10)

# Main function to start the application
def main():
    root = Tk()
    root.title("Database Tables Viewer")

    global connection
    connection = connect_to_database("root", "1234")  # Replace with your actual DB credentials
    if connection:
        create_table_tabs(connection, root)

    root.mainloop()

if __name__ == "__main__":
    main()
