import service from '@/utils/request'

/** 分页查询实验室 */
export function getLabPageList(params) {
    return service({
        url: '/api/lab/list',
        method: 'get',
        params
    })
}

/** 查询实验室详情 */
export function getLabId(lab_id) {
    return service({
        url: `/api/lab/${lab_id}`,
        method: 'get'
    })
}

/** 实验室下拉选项（不分页，仅 id+name） */
export function getLabOptionsApi() {
    return service({
        url: '/api/lab/options',
        method: 'get'
    })
}

/** 新增实验室 */
export function createLabApi(data) {
    return service({
        url: '/api/lab',
        method: 'post',
        data
    })
}

/** 修改实验室 */
export function updateLabApi(labId, data) {
    return service({
        url: `/api/lab/${labId}`,
        method: 'put',
        data
    })
}

/** 删除实验室 */
export function deleteLabApi(labId) {
    return service({
        url: `/api/lab/${labId}`,
        method: 'delete'
    })
}


/** 批量删除实验室 */
export function deleteLabListApi(data) {
    return service({
        url: `/api/lab/batch`,
        method: 'delete',
        data: data
    })
}