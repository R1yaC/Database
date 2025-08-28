import sqlite3
import bcrypt
import pandas as pd
from datetime import datetime
import getpass

DB_PATH = "expense_report.db"

# Database Connection
def connect_db():
    return sqlite3.connect(DB_PATH)

# 1. Create User (Admin Only)
def create_user(admin_id, username, password, role="User"):
    conn = connect_db()
    cursor = conn.cursor()

    # Check if admin exists and has Admin role
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (admin_id,))
    admin = cursor.fetchone()

    if not admin or admin[0] != "Admin":
        print("Access denied! Only Admins can create users.")
        conn.close()
        return

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode('utf-8')

    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                      (username, hashed_password, role))
        conn.commit()
        print(f"User '{username}' created successfully with role '{role}'!")
    except sqlite3.IntegrityError:
        print("Error: Username already exists!")
    finally:
        conn.close()

# 2. Login User
def login_user(username, password):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, password, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_id, stored_hashed_password, role = user
        if bcrypt.checkpw(password.encode(), stored_hashed_password.encode()):
            print(f"Login successful! Welcome, {username} ({role})")
            return user_id, role
        else:
            print("Invalid password.")
    else:
        print("User not found.")
    return None, None

# 3. Logout
def logout():
    global user_id, role
    user_id = None
    role = None
    print("✅ Logged out successfully")

# 4. List Users (Admin Only)
def list_users(current_user_role):
    if current_user_role != "Admin":
        print("Access denied! Admin only.")
        return
    
    conn = connect_db()
    df = pd.read_sql_query("SELECT user_id, username, role FROM users", conn)
    conn.close()
    print(df.to_string(index=False))

# 5. Add Category (Admin Only)
def add_category(admin_id, category_name):
    conn = connect_db()
    cursor = conn.cursor()

    cursor.execute("SELECT role FROM users WHERE user_id = ?", (admin_id,))
    admin = cursor.fetchone()

    if not admin or admin[0] != "Admin":
        print("Access denied! Only Admins can create categories.")
        conn.close()
        return

    try:
        cursor.execute("INSERT INTO categories (name) VALUES (?)", (category_name,))
        conn.commit()
        print(f"Category '{category_name}' created successfully!")
    except sqlite3.IntegrityError:
        print("Error: Category already exists!")
    finally:
        conn.close()

# 6. List Categories
def list_categories():
    conn = connect_db()
    df = pd.read_sql_query("SELECT * FROM categories", conn)
    conn.close()
    print(df.to_string(index=False))

# 7. Add Payment Method (Admin only)
def add_payment_method(admin_id, method_name):
    conn = connect_db()
    cursor = conn.cursor()

    # Check if admin exists and has Admin role
    cursor.execute("SELECT role FROM users WHERE user_id = ?", (admin_id,))
    admin = cursor.fetchone()

    if not admin or admin[0] != "Admin":
        print("Access denied! Only Admins can add payment methods.")
        conn.close()
        return

    try:
        cursor.execute("INSERT INTO payment_methods (name) VALUES (?)", (method_name,))
        conn.commit()
        print(f"Payment method '{method_name}' created successfully!")
    except sqlite3.IntegrityError:
        print("Error: Payment method already exists!")
    finally:
        conn.close()

# 8. List Payment Methods
def list_payment_methods():
    conn = connect_db()
    df = pd.read_sql_query("SELECT * FROM payment_methods", conn)
    conn.close()
    print(df.to_string(index=False))

# 9. Add Expense
def add_expense(user_id, category_id, method_id, amount, date, description=None, tag=None):
    if amount <= 0:
        print("Error: Amount must be greater than zero.")
        return

    conn = connect_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""INSERT INTO expenses (user_id, category_id, method_id, amount, date, description, tag) 
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (user_id, category_id, method_id, amount, date, description, tag))
        conn.commit()
        print("Expense added successfully!")
    except sqlite3.IntegrityError:
        print("Error: Invalid category ID or payment method ID.")
    finally:
        conn.close()

# 10. Update Expense
def update_expense(user_id, user_role, expense_id, field, new_value):
    conn = connect_db()
    cursor = conn.cursor()

    # Validate expense belongs to user (unless admin)
    if user_role != "Admin":
        cursor.execute("SELECT expense_id FROM expenses WHERE expense_id = ? AND user_id = ?", 
                      (expense_id, user_id))
        if not cursor.fetchone():
            print("Error: You can only update your own expenses!")
            conn.close()
            return

    # Validate field name
    valid_fields = ['amount', 'category_id', 'method_id', 'date', 'description', 'tag']
    if field not in valid_fields:
        print(f"Error: Invalid field. Must be one of: {', '.join(valid_fields)}")
        conn.close()
        return

    try:
        # Handle different field types
        if field == 'amount':
            new_value = float(new_value)
        elif field == 'category_id' or field == 'method_id':
            new_value = int(new_value)
        elif field == 'date':
            datetime.strptime(new_value, '%Y-%m-%d')  # Validate date format

        cursor.execute(f"UPDATE expenses SET {field} = ? WHERE expense_id = ?", 
                      (new_value, expense_id))

        if cursor.rowcount == 0:
            print("Error: Expense ID not found.")
        else:
            conn.commit()
            print("Expense updated successfully!")
    except ValueError as e:
        print(f"Error: Invalid value for field {field}. {str(e)}")
    finally:
        conn.close()

# 11. Delete Expense
def delete_expense(user_id, user_role, expense_id):
    conn = connect_db()
    cursor = conn.cursor()

    # Validate ownership (unless Admin)
    if user_role != "Admin":
        cursor.execute("SELECT expense_id FROM expenses WHERE expense_id = ? AND user_id = ?", 
                      (expense_id, user_id))
        if not cursor.fetchone():
            print("Error: You can only delete your own expenses!")
            conn.close()
            return

    cursor.execute("DELETE FROM expenses WHERE expense_id = ?", (expense_id,))
    
    if cursor.rowcount == 0:
        print("Error: Expense ID not found.")
    else:
        conn.commit()
        print("Expense deleted successfully!")

    conn.close()

# 12. List Expenses with Filters
def list_expenses(user_id, user_role, filters=None):
    conn = connect_db()
    
    base_query = """SELECT e.expense_id, e.amount, c.name as category, 
                   p.name as payment_method, e.date, e.description, e.tag
                   FROM expenses e
                   JOIN categories c ON e.category_id = c.category_id
                   JOIN payment_methods p ON e.method_id = p.method_id"""
    
    where_clauses = []
    params = []
    
    if user_role != "Admin":
        where_clauses.append("e.user_id = ?")
        params.append(user_id)
    
    # Add filter conditions
    if filters:
        if 'category' in filters:
            where_clauses.append("c.name = ?")
            params.append(filters['category'])
        if 'date' in filters:
            where_clauses.append("e.date = ?")
            params.append(filters['date'])
        if 'amount_min' in filters:
            where_clauses.append("e.amount >= ?")
            params.append(filters['amount_min'])
        if 'amount_max' in filters:
            where_clauses.append("e.amount <= ?")
            params.append(filters['amount_max'])
        if 'payment' in filters:
            where_clauses.append("p.name = ?")
            params.append(filters['payment'])
    
    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)
    
    df = pd.read_sql_query(base_query, conn, params=params)
    conn.close()
    
    print(df if not df.empty else "No expenses found")

# 13. Export Expenses to CSV with Sorting
def export_expenses(filename, sort_field=None):
    conn = connect_db()
    
    query = """SELECT e.expense_id, e.user_id, e.amount, c.name as category, 
              p.name as payment_method, e.date, e.description, e.tag
              FROM expenses e
              JOIN categories c ON e.category_id = c.category_id
              JOIN payment_methods p ON e.method_id = p.method_id"""
    
    if sort_field:
        query += f" ORDER BY {sort_field}"
    
    df = pd.read_sql_query(query, conn)
    df.to_csv(filename, index=False)
    conn.close()
    print(f"Expenses exported to {filename}" + (f" sorted by {sort_field}" if sort_field else ""))

# 14. Import Expenses from CSV
def import_expenses(filename):
    try:
        df = pd.read_csv(filename)
        if "expense_id" in df.columns:
            df.drop(columns=["expense_id"], inplace=True)

        conn = connect_db()
        df.to_sql("expenses", conn, if_exists="append", index=False)
        conn.close()
        print(f"Expenses imported successfully from {filename}!")
    except FileNotFoundError:
        print(f"Error: File {filename} not found!")
    except sqlite3.IntegrityError as e:
        print(f"Integrity Error: {e}")
    except Exception as e:
        print(f"Error: {str(e)}")

# 16. Report Top N Expenses in Date Range
def report_top_expenses(user_id, user_role, n, start_date=None, end_date=None):
    conn = connect_db()
    
    base_query = """SELECT e.expense_id, e.amount, c.name as category, 
                   p.name as payment_method, e.date, e.description
                   FROM expenses e
                   JOIN categories c ON e.category_id = c.category_id
                   JOIN payment_methods p ON e.method_id = p.method_id"""
    
    where_clauses = []
    params = []
    
    if user_role != "Admin":
        where_clauses.append("e.user_id = ?")
        params.append(user_id)
    
    if start_date and end_date:
        where_clauses.append("e.date BETWEEN ? AND ?")
        params.extend([start_date, end_date])
    elif start_date:
        where_clauses.append("e.date >= ?")
        params.append(start_date)
    elif end_date:
        where_clauses.append("e.date <= ?")
        params.append(end_date)
    
    if where_clauses:
        base_query += " WHERE " + " AND ".join(where_clauses)
    
    base_query += " ORDER BY e.amount DESC LIMIT ?"
    params.append(n)
    
    df = pd.read_sql_query(base_query, conn, params=params)
    conn.close()
    
    print(f"\nTop {n} expenses" + (f" from {start_date} to {end_date}" if start_date or end_date else ""))
    print(df.to_string(index=False) if not df.empty else print("No expenses found"))

# 17. Report Category Spending
def report_category_spending(user_id, user_role, category_name):
    conn = connect_db()
    
    query = """SELECT SUM(e.amount) as total_spending
               FROM expenses e
               JOIN categories c ON e.category_id = c.category_id
               WHERE c.name = ?"""
    
    params = [category_name]
    
    if user_role != "Admin":
        query += " AND e.user_id = ?"
        params.append(user_id)
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    
    total = result[0] if result and result[0] is not None else 0
    print(f"\nTotal spending on '{category_name}': ${total:.2f}")

# 18. Report Expenses Above Category Average
def report_above_average_expenses(user_id, user_role):
    conn = connect_db()
    
    query = """SELECT e.expense_id, e.amount, c.name as category, e.date, e.description
               FROM expenses e
               JOIN categories c ON e.category_id = c.category_id
               JOIN (
                   SELECT c.category_id, AVG(e.amount) as avg_amount
                   FROM expenses e
                   JOIN categories c ON e.category_id = c.category_id
                   GROUP BY c.category_id
               ) avg ON e.category_id = avg.category_id
               WHERE e.amount > avg.avg_amount"""
    
    params = []
    if user_role != "Admin":
        query += " AND e.user_id = ?"
        params.append(user_id)
    
    query += " ORDER BY e.amount DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    print("\nExpenses above category average:")
    print(df.to_string(index=False) if not df.empty else print("No expenses found"))

# 19. Report Monthly Category Spending
def report_monthly_category_spending(user_id, user_role):
    conn = connect_db()
    
    query = """SELECT strftime('%Y-%m', e.date) as month, 
                      c.name as category, 
                      SUM(e.amount) as total_spending
               FROM expenses e
               JOIN categories c ON e.category_id = c.category_id"""
    
    where_clause = ""
    params = []
    if user_role != "Admin":
        where_clause = " WHERE e.user_id = ?"
        params.append(user_id)
    
    query += where_clause + """
               GROUP BY month, c.name
               ORDER BY month, total_spending DESC"""
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    print("\nMonthly spending by category:")
    print(df.to_string(index=False) if not df.empty else print("No expenses found"))

# 20. Report Highest Spender Per Month (Admin only)
def report_highest_spender_per_month():
    conn = connect_db()
    
    query = """SELECT month, username, max_spending FROM (
                 SELECT strftime('%Y-%m', e.date) as month,
                        u.username,
                        SUM(e.amount) as total_spending,
                        MAX(SUM(e.amount)) OVER (PARTITION BY strftime('%Y-%m', e.date)) as max_spending
                 FROM expenses e
                 JOIN users u ON e.user_id = u.user_id
                 GROUP BY month, u.user_id
               ) 
               WHERE total_spending = max_spending
               ORDER BY month"""
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print("\nHighest spender each month:")
    print(df.to_string(index=False) if not df.empty else print("No data found"))

# 21. Report Most Frequent Category
def report_frequent_category(user_id, user_role):
    conn = connect_db()
    
    query = """SELECT c.name as category, COUNT(*) as expense_count
               FROM expenses e
               JOIN categories c ON e.category_id = c.category_id"""
    
    params = []
    if user_role != "Admin":
        query += " WHERE e.user_id = ?"
        params.append(user_id)
    
    query += " GROUP BY c.name ORDER BY expense_count DESC LIMIT 1"
    
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    
    if result:
        print(f"\nMost frequent category: {result[0]} ({result[1]} expenses)")
    else:
        print("\nNo expenses found")

# 22. Report Payment Method Usage
def report_payment_method_usage(user_id, user_role):
    conn = connect_db()
    
    query = """SELECT p.name as payment_method, 
                      COUNT(*) as transaction_count,
                      SUM(e.amount) as total_spent
               FROM expenses e
               JOIN payment_methods p ON e.method_id = p.method_id"""
    
    params = []
    if user_role != "Admin":
        query += " WHERE e.user_id = ?"
        params.append(user_id)
    
    query += " GROUP BY p.name ORDER BY total_spent DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    print("\nPayment method usage:")
    print(df.to_string(index=False) if not df.empty else print("No expenses found"))

# 23. Report Expenses by Tag
def report_tag_expenses(user_id, user_role):
    conn = connect_db()
    
    query = """SELECT e.tag, COUNT(*) as expense_count,
                      SUM(e.amount) as total_spent
               FROM expenses e
               WHERE e.tag IS NOT NULL"""
    
    params = []
    if user_role != "Admin":
        query += " AND e.user_id = ?"
        params.append(user_id)
    
    query += " GROUP BY e.tag ORDER BY expense_count DESC"
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    print("\nExpenses by tag:")
    print(df.to_string(index=False) if not df.empty else print("No tagged expenses found"))

# Update the help menu to include reports
def print_help():
    print("""
Enter the NUMBER to select an option:           
                             
1. Create User (Admin only)                     
2. Login                                        
3. Logout                                      
4. List Users (Admin only)                       
5. Add Category (Admin only)                    
6. List Categories                               
7. Add Payment Method (Admin only)                          
8. List Payment Methods                          
9. Add Expense                                   
10. Update Expense                               
11. Delete Expense                              
12. List Expenses                                
13. Export to CSV (Admin only)                               
14. Import from CSV                            
15. Exit                                         

REPORTS:
16. Top N expenses in date range
17. Category spending summary
18. Expenses above category average
19. Monthly spending by category
20. Highest spender per month
21. Most frequent category
22. Payment method usage
23. Expenses by tag
""")

def get_input(prompt, password=False):
    if password:
        return getpass.getpass(prompt)
    return input(prompt)

if __name__ == "__main__":
    user_id = None
    role = None

    print("Type 'help' to see available options\n")

    while True:
        command = input("> ").strip().lower()

        if command == "help":
            print_help()
            continue
        elif command.isdigit():
            option = int(command)
            
            if option == 1:  # Create User
                if user_id is None or role != "Admin":
                    print("Access denied! Admin only.")
                    continue
                
                username = get_input("Enter username: ")
                password = get_input("Enter password: ", password=True)
                user_role = get_input("Enter role (Admin/User, default=User): ") or "User"
                create_user(user_id, username, password, user_role)

            elif option == 2:  # Login
                username = get_input("Username: ")
                password = get_input("Password: ", password=True)
                user_id, role = login_user(username, password)

            elif option == 3:  # Logout
                logout()

            elif option == 4:  # List Users
                if user_id is None:
                    print("You must log in first!")
                else:
                    list_users(role)

            elif option == 5:  # Add Category
                if user_id is None or role != "Admin":
                    print("Access denied! Admin only.")
                    continue
                name = get_input("Enter category name: ")
                add_category(user_id, name)

            elif option == 6:  # List Categories
                list_categories()

            elif option == 7:  # Add Payment Method
                if user_id is None or role != "Admin":
                    print("Access denied! Admin only.")
                    continue
                name = get_input("Enter payment method name: ")
                add_payment_method(user_id, name)

            elif option == 8:  # List Payment Methods
                list_payment_methods()

            elif option == 9:  # Add Expense
                if user_id is None:
                    print("You must log in first!")
                    continue
                try:
                    amount = float(get_input("Enter amount: "))
                    category_id = int(get_input("Enter category ID: "))
                    method_id = int(get_input("Enter payment method ID: "))
                    date = get_input("Enter date (YYYY-MM-DD): ")
                    description = get_input("Enter description (optional): ") or None
                    tag = get_input("Enter tag (optional): ") or None
                    add_expense(user_id, category_id, method_id, amount, date, description, tag)
                except ValueError:
                    print("Invalid input! Please enter correct values.")

            elif option == 10:  # Update Expense
                if user_id is None:
                    print("You must log in first!")
                    continue
                try:
                    expense_id = int(get_input("Enter expense ID to update: "))
                    field = get_input("Enter field to update (amount/category_id/method_id/date/description/tag): ")
                    new_value = get_input(f"Enter new value for {field}: ")
                    update_expense(user_id, role, expense_id, field, new_value)
                except ValueError:
                    print("Invalid input! Please enter correct values.")

            elif option == 11:  # Delete Expense
                if user_id is None:
                    print("You must log in first!")
                    continue
                try:
                    expense_id = int(get_input("Enter expense ID to delete: "))
                    delete_expense(user_id, role, expense_id)
                except ValueError:
                    print("Invalid expense ID!")

            elif option == 12:  # List Expenses
                if user_id is None:
                    print("You must log in first!")
                    continue
                print("Available filters (press enter to skip):")
                category = get_input("Filter by category name: ") or None
                date = get_input("Filter by date (YYYY-MM-DD): ") or None
                amount_min = get_input("Minimum amount: ") or None
                amount_max = get_input("Maximum amount: ") or None
                payment = get_input("Filter by payment method: ") or None
                
                filters = {}
                if category: filters['category'] = category
                if date: filters['date'] = date
                if amount_min: filters['amount_min'] = amount_min
                if amount_max: filters['amount_max'] = amount_max
                if payment: filters['payment'] = payment
                
                list_expenses(user_id, role, filters if any(filters.values()) else None)

            elif option == 13:  # Export to CSV
                if user_id is None or role != "Admin":
                    print("Access denied! Admin only.")
                    continue
                filename = get_input("Enter filename to export to (e.g., expenses.csv): ")
                sort_field = get_input("Sort by field (optional, press enter to skip): ") or None
                export_expenses(filename, sort_field)

            elif option == 14:  # Import from CSV
                filename = get_input("Enter filename to import from: ")
                import_expenses(filename)

            elif option == 15:  # Exit
                break
                
            elif option == 16:  # Top N expenses
                if user_id is None:
                    print("You must log in first!")
                    continue
                try:
                    n = int(get_input("Enter number of expenses to show: "))
                    date_range = get_input("Enter date range (YYYY-MM-DD to YYYY-MM-DD) or leave blank: ")
                    if date_range:
                        start_date, end_date = date_range.split(" to ")
                    else:
                        start_date = end_date = None
                    report_top_expenses(user_id, role, n, start_date, end_date)
                except ValueError:
                    print("Invalid input format!")

            elif option == 17:  # Category spending
                if user_id is None:
                    print("You must log in first!")
                    continue
                category = get_input("Enter category name: ")
                report_category_spending(user_id, role, category)

            elif option == 18:  # Above average expenses
                if user_id is None:
                    print("You must log in first!")
                    continue
                report_above_average_expenses(user_id, role)

            elif option == 19:  # Monthly category spending
                if user_id is None:
                    print("You must log in first!")
                    continue
                report_monthly_category_spending(user_id, role)

            elif option == 20:  # Highest spender per month
                if user_id is None:
                    print("You must log in first.")
                    continue
                report_highest_spender_per_month()

            elif option == 21:  # Frequent category
                if user_id is None:
                    print("You must log in first!")
                    continue
                report_frequent_category(user_id, role)

            elif option == 22:  # Payment method usage
                if user_id is None:
                    print("You must log in first!")
                    continue
                report_payment_method_usage(user_id, role)

            elif option == 23:  # Expenses by tag
                if user_id is None:
                    print("You must log in first!")
                    continue
                report_tag_expenses(user_id, role)

            else:
                print("Invalid option number. Type 'help' to see available options.")
        else:
            print("Please enter a number (1-23) or 'help'. Type 'help' to see options.")
               
