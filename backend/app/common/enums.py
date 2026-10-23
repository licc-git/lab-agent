from enum import IntEnum


class ReservationStatus(IntEnum):
    PendingApproval = 0 # 待审核
    Approved = 1        # 通过
    Rejected = 2        # 拒绝
    Cancelled = 3       # 取消
    Expired = 4         # 过期


    
