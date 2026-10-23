-- Allow status 4 (expired) for pending reservations whose time window has ended.
ALTER TABLE reservations
    DROP CHECK check_reservation_status;

ALTER TABLE reservations
    ADD CONSTRAINT check_reservation_status CHECK (status IN (0, 1, 2, 3, 4)),
    MODIFY COLUMN status INT NOT NULL DEFAULT 0
        COMMENT '预约状态：0-待审核，1-已通过，2-已拒绝，3-已取消，4-已过期';
