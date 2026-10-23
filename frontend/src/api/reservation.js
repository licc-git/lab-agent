import service from "@/utils/request";

export function createReservationApi(data) {
    return service({
        url: "/api/reservation",
        method: "post",
        data: data
    })
}

export function getReservationListApi(params) {
    return service({
        url: "/api/reservation/list",
        method: "get",
        params: params
    })
}

export function cancelReservationApi(reservation_id) {
    return service({
        url: `/api/reservation/${reservation_id}/cancel`,
        method: "put",
    })
}

export function auditReservationApi(reservation_id, data) {
    return service({
        url: `/api/reservation/${reservation_id}/audit`,
        method: "put",
        data: data
    })
}
