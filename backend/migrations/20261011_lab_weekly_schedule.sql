-- Apply once to existing MySQL databases before starting the updated backend.
-- Existing dated hours retain their clock portion; legacy rows are assigned weekdays.
-- Legacy NULL times (used by the seed data to represent "全天") become 00:00-23:59.
ALTER TABLE labs
    ADD COLUMN open_days JSON NULL COMMENT '每周开放日，0为周一',
    ADD COLUMN open_time_new TIME NULL COMMENT '每日开放开始时间',
    ADD COLUMN close_time_new TIME NULL COMMENT '每日开放结束时间';

UPDATE labs
SET open_time_new = COALESCE(TIME(open_time), '00:00:00'),
    close_time_new = COALESCE(TIME(close_time), '23:59:00'),
    open_days = JSON_ARRAY(0, 1, 2, 3, 4);

ALTER TABLE labs
    DROP COLUMN open_time,
    DROP COLUMN close_time,
    CHANGE COLUMN open_time_new open_time TIME NULL COMMENT '每日开放开始时间',
    CHANGE COLUMN close_time_new close_time TIME NULL COMMENT '每日开放结束时间',
    MODIFY COLUMN open_days JSON NOT NULL COMMENT '每周开放日，0为周一';
