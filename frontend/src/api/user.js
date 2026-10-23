import service from "@/utils/request";

export function getUserInfoApi() {
    return service({
        url: "/api/user/profile",
        method: "get"
    })
}

export function updateUserInfoApi(data) {
    return service({
        url: "/api/user/profile",
        method: "put",
        data: data
    })
}

export function uploadAvatarApi(img) {
    const formData = new FormData()
    formData.append('file', img)
    return service({
        url: "/api/files/upload",
        method: "post",
        data: formData,
        headers: { "Content-Type": "multipart/form-data" }
    })
}

export function updatePasswordApi(data) {
    return service({
        url: "/api/user/password",
        method: 'put',
        data: data
    })
}

export function getUserPageListApi(params) {
    return service({
        url: '/api/user/list',
        method: 'get',
        params: params
    })
}

export function createUserApi(data) {
    return service({
        url: '/api/user',
        method: 'post',
        data: data
    })
}

export function deleteUserApi(userId) {
    return service({
        url: `/api/user/${userId}`,
        method: 'delete'
    })
}

export function deleteUsersApi(ids) {
    return service({
        url: '/api/user/batch',
        method: 'delete',
        data: { ids }
    })
}

export function updateUserApi(userId, data) {
    return service({
        url: `/api/user/${userId}`,
        method: 'put',
        data: data
    })
}