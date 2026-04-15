-- 添加 Hermes 自优化模式字段
ALTER TABLE novels ADD COLUMN hermes_mode INTEGER NOT NULL DEFAULT 0;

-- hermes_mode = 0: 关闭（默认）
-- hermes_mode = 1: 开启 Hermes 自优化，每章完成后自动提取 Skill 并优化下一章
