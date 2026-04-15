-- ------------------------------------------------------------
-- ROLES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS roles (
    role_id     INT AUTO_INCREMENT PRIMARY KEY,
    role_name   VARCHAR(10)  NOT NULL UNIQUE,
    description VARCHAR(100)
);

-- ------------------------------------------------------------
-- USERS (encrypted passwords stored as bcrypt hashes)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(30)  NOT NULL UNIQUE,
    email         VARCHAR(254),
    password_hash VARCHAR(60)  NOT NULL,
    role_id       INT          NOT NULL,
    is_active             BOOLEAN      NOT NULL DEFAULT TRUE,
    failed_login_attempts INT          NOT NULL DEFAULT 0,
    locked_at             DATETIME     NULL,
    created_at            DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login            DATETIME,
    FOREIGN KEY (role_id) REFERENCES roles(role_id)
);

-- Seed roles
INSERT IGNORE INTO roles (role_name, description) VALUES
('user', 'Standard passenger-facing access: flight search and timetable'),
('admin',   'Full access: user management, simulation control, financial reports');

-- NOTE: admin user is seeded at backend startup via Python/bcrypt (see app/__init__.py)
-- Seed default regular user (username: user, password: pass)
INSERT IGNORE INTO users (username, password_hash, role_id) VALUES
('user', '$2b$12$zJe4W0kI2bSc4tK2NySAi.4iUVYQOizgYB4WGnHLqKcLl9y3PZoxa', (SELECT role_id FROM roles WHERE role_name = 'user'));
