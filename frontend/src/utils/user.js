// 仅供页面  setup 函数使用

import { ref } from "vue";
import { setToken, setUserInfo, getUserInfo, removeToken, removeUserInfo } from "./auth";

const userInfo = ref(getUserInfo())

export function useUser() {     // 组合式函数：给页面用的"工具包"
    function saveLoginData(data) {
        setToken(data.token);
        setUserInfo(data.user);
        userInfo.value = data.user;
    }

    function updateUser(user) {
        setUserInfo(user);
        userInfo.value = user;
    }

    function reloadUser() {
        userInfo.value = getUserInfo();
    }

    function logout() {
        removeToken();
        removeUserInfo();
        userInfo.value = null;
    }
    return { userInfo, saveLoginData, updateUser, reloadUser, logout }
}