BEGIN TRANSACTION;

CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL CHECK(length(username) >= 4),
    password TEXT NOT NULL, 
    role TEXT NOT NULL CHECK(role IN ('Admin', 'User')) DEFAULT 'User',
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0,1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL CHECK(length(name) >= 3),
    monthly_budget REAL CHECK(monthly_budget >= 0),
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0,1))
);

INSERT OR IGNORE INTO categories (name, monthly_budget) VALUES
('Food', 500),
('Travel', 300),
('Utilities', 400),
('Entertainment', 200);

CREATE TABLE IF NOT EXISTS payment_methods (
    method_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL CHECK(length(name) >= 3),
    is_active INTEGER DEFAULT 1 CHECK(is_active IN (0,1))
);

INSERT OR IGNORE INTO payment_methods (name) VALUES
('Cash'),
('Credit Card'),
('Bank Transfer'),
('UPI');

CREATE TABLE IF NOT EXISTS expenses (
    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    method_id INTEGER NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    date DATE NOT NULL, 
    description TEXT,
    tag TEXT CHECK(length(tag) <= 20),
    status TEXT CHECK(status IN ('Pending', 'Approved', 'Rejected')) DEFAULT 'Pending',
    receipt_image TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE SET NULL,
    FOREIGN KEY (method_id) REFERENCES payment_methods(method_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    expense_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('Create','Update','Delete')),
    notes TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expense_id) REFERENCES expenses(expense_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_expenses_user ON expenses(user_id);
CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date);
CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category_id);
CREATE INDEX IF NOT EXISTS idx_expenses_status ON expenses(status);
CREATE INDEX IF NOT EXISTS idx_expenses_method ON expenses(method_id);

COMMIT;