-- Map legacy reservation states to the new status values:
-- -1 (previously approved) -> 1 (approved)
--  0 (pending approval)    -> 0 (pending approval)
--  1 (previously shared by rejected/cancelled) -> 2 (rejected)
ALTER TABLE reservations
    DROP CHECK check_reservation_status;

UPDATE reservations
SET status = CASE status
    WHEN -1 THEN 1
    WHEN 1 THEN 2
    ELSE status
END
WHERE status IN (-1, 1);

ALTER TABLE reservations
    ADD CONSTRAINT check_reservation_status CHECK (status IN (0, 1, 2, 3)),
    MODIFY COLUMN status INT NOT NULL DEFAULT 0
        COMMENT '预约状态：0-待审核，1-已通过，2-已拒绝，3-已取消';
