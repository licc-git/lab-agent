import service from '@/utils/request'

/** 分页查询设备列表（keywords 模糊搜索名称/型号，lab_id 按实验室过滤） */
export function getEquipmentPageList(params) {
    return service({
        url: '/api/equipment/list',
        method: 'get',
        params
    })
}

/** 新增设备 */
export function createEquipmentApi(data) {
    return service({
        url: '/api/equipment',
        method: 'post',
        data
    })
}

/** 更新设备 */
export function updateEquipmentApi(id, data) {
    return service({
        url: `/api/equipment/${id}`,
        method: 'put',
        data
    })
}

/** 删除单个设备 */
export function deleteEquipmentApi(id) {
    return service({
        url: `/api/equipment/${id}`,
        method: 'delete'
    })
}

/** 批量删除设备 */
export function deleteEquipmentListApi(data) {
    return service({
        url: '/api/equipment/batch',
        method: 'delete',
        data
    })
}
