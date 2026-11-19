// 简历相关 API 接口定义
import request from './client'

// 上传简历
export function uploadResume(file: File) {
  const form = new FormData()
  form.append('file', file)
  return request.post('/resumes/upload', form)
}

// 解析简历
export function parseResume(resumeId: number) {
  return request.post(`/resumes/${resumeId}/parse`)
}

// 评分
export function scoreResume(resumeId: number, targetJob = '') {
  return request.post(`/resumes/${resumeId}/score`, null, {
    params: { target_job: targetJob },
  })
}

// 优化
export function optimizeResume(resumeId: number, jobType: string) {
  return request.post(`/resumes/${resumeId}/optimize`, { job_type: jobType })
}

// 岗位匹配
export function matchJob(resumeId: number, jdText: string) {
  return request.post(`/resumes/${resumeId}/match`, { jd_text: jdText })
}

// 应用建议
export function applySuggestions(resumeId: number, acceptedIndices: number[]) {
  return request.post(`/resumes/${resumeId}/apply-suggestions`, {
    accepted_indices: acceptedIndices,
  })
}

// 获取对比
export function getDiff(resumeId: number) {
  return request.get(`/resumes/${resumeId}/diff`)
}

// 导出优化后简历（docx / pdf），返回 Blob
export function exportResume(resumeId: number, format: 'docx' | 'pdf') {
  return request.get(`/resumes/${resumeId}/export`, {
    params: { format },
    responseType: 'blob',
  })
}
