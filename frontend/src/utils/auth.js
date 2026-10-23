//  存储token、存储用户信息、获取token、用户信息，删除token、用户信息这些作用

const TOKEN_KEY = 'token'
const USER_KEY = 'userInfo'

export function getToken() {
    return localStorage.getItem(TOKEN_KEY)
}

export function getUserInfo() {
    return JSON.parse(localStorage.getItem(USER_KEY))
}

export function setToken(token) {
    return localStorage.setItem(TOKEN_KEY, token)
}

export function setUserInfo(user) {
    return localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function removeToken() {
    localStorage.removeItem(TOKEN_KEY)
}

export function removeUserInfo() {
    localStorage.removeItem(USER_KEY)
}
