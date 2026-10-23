import service from "@/utils/request";


export function getChatApi() {
    return service({
        url: '/api/ai/chat',
        method: 'get',
    })
}

export function chatApi(data) {
    return service({
        url: '/api/ai/chat',
        method: 'post',
        data: data,
        timeout: 30000,
    })
}
