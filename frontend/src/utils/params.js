/**
 * 
 * @param {*} obj 
 * @returns {*} 
 ** 清理参数空值
 */

export function cleanParams(obj) {
    const result = {}
    for (const [key, value] of Object.entries(obj)) {
        if (value === '' || value === null || value === undefined) continue
        result[key] = value
    }
    return result
}