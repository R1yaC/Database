Group Members: Riya Chaurasia, Abhipsha Luitel, Piya Shah, Moksha Shah, Vineesha Vuppala

This project is a comprehensive Expense Management System built using Python and SQLite.
It allows users (Admins and Regular Users) to track expenses, categorize spending, generate reports,
and manage budgets with role-based access control.

a. Project Structure

expense.py           # Main Python script with all functionality
db.sql               # SQL schema and initial data setup
expense_report.db    # SQLite database file
expenses_export.csv  # Sample exported expense data
README.txt           # This documentation file

b. Complete Menu System

MAIN FUNCTIONALITY:
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
12. List Expenses (with filters)
13. Export to CSV (Admin only)
14. Import from CSV
15. Exit

REPORTING FEATURES:
16. Top N expenses in date range
17. Category spending summary
18. Expenses above category average
19. Monthly spending by category
20. Highest spender per month (Admin only)
21. Most frequent category
22. Payment method usage
23. Expenses by tag

c. Key Features

- Role-based access control (Admin/User)
- Secure password hashing
- Expense categorization
- Flexible filtering and reporting
- CSV import/export functionality
- Comprehensive reporting system

d. Usage Notes

- Admins have full access to all features
- Regular users can only manage their own expenses
- All financial data is stored in the SQLite database
- Reports can be generated for analysis
- System uses secure password storage with bcrypt
