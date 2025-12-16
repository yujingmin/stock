-- 修改 verification_codes 表的列名
-- 将 code_type 改为 purpose 以匹配 SQLAlchemy 模型

ALTER TABLE verification_codes
RENAME COLUMN code_type TO purpose;
