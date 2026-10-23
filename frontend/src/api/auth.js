import service from "@/utils/request";

export function loginApi (data) {
    return service({
        url: '/api/auth/login',
        method: 'POST',
        data: data
    })
}

export function registerApi (data) {
    return service({
        url: '/api/auth/register',
        method: 'POST',
        data: data
    })
}
