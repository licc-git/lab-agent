-- 创建用户（允许本地访问）
create user `lab_agent`@`localhost` identified by 'Lab_agent@2026#App';

-- 授权该用户在项目数据库的所有权限
grant all privileges on lab_agent_db.* to 'lab_agent'@'localhost';

-- 刷新权限
flush privileges;

-- 创建数据库（推荐，指定字符集 utf8mb4）
CREATE DATABASE lab_agent_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
