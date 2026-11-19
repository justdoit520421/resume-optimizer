// 步骤 2：解析预览
import { useEffect, useRef, useState } from 'react'
import { Card, Button, Space, Descriptions, Tag, Spin, message, Alert } from 'antd'
import { parseResume } from '../api/resume'
import { useResumeStore } from '../store/resumeStore'

interface Props {
  onNext: () => void
  onPrev: () => void
}

export default function ParseStep({ onNext, onPrev }: Props) {
  const resumeId = useResumeStore((s) => s.resumeId)
  const parsed = useResumeStore((s) => s.parsed)
  const setParsed = useResumeStore((s) => s.setParsed)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchingRef = useRef(false)

  useEffect(() => {
    // StrictMode 下 effect 会执行两次，用 ref 守卫避免重复请求
    if (resumeId && !parsed && !fetchingRef.current) {
      fetchingRef.current = true
      handleParse().finally(() => { fetchingRef.current = false })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resumeId])

  const handleParse = async () => {
    if (!resumeId) return
    setLoading(true)
    setError('')
    try {
      const res: any = await parseResume(resumeId)
      setParsed(res.raw_text, res.parsed)
      message.success('解析完成')
    } catch {
      setError('简历解析失败，请点击重试')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card title="第二步：解析预览">
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 12, color: '#666' }}>AI 正在解析简历...</div>
        </div>
      </Card>
    )
  }

  const info = parsed?.basic_info || {}
  const edu = parsed?.education || []
  const work = parsed?.work_experience || []
  const projects = parsed?.projects || []
  const skills = parsed?.skills || []

  return (
    <Card title="第二步：解析预览">
      <Space direction="vertical" size="middle" style={{ width: '100%' }}>
        {error && (
          <Alert
            type="error"
            showIcon
            message={error}
            action={<Button size="small" onClick={handleParse}>重试</Button>}
          />
        )}
        <Descriptions title="基本信息" bordered column={2}>
          <Descriptions.Item label="姓名">{info.name || '-'}</Descriptions.Item>
          <Descriptions.Item label="电话">{info.phone || '-'}</Descriptions.Item>
          <Descriptions.Item label="邮箱">{info.email || '-'}</Descriptions.Item>
        </Descriptions>

        <Card size="small" title="教育背景">
          {edu.map((e: any, i: number) => (
            <div key={i}>{e.school} · {e.major} · {e.degree} · {e.period}</div>
          ))}
        </Card>

        <Card size="small" title="工作经历">
          {work.map((w: any, i: number) => (
            <div key={i} style={{ marginBottom: 12 }}>
              <b>{w.company} - {w.position}</b>（{w.period}）
              <div style={{ color: '#666' }}>{w.content}</div>
            </div>
          ))}
        </Card>

        <Card size="small" title="项目经历">
          {projects.map((p: any, i: number) => (
            <div key={i} style={{ marginBottom: 12 }}>
              <b>{p.name}</b>（{p.role} · {p.period}）
              <div style={{ color: '#666' }}>{p.content}</div>
            </div>
          ))}
        </Card>

        <Card size="small" title="技能">
          {skills.map((s: string, i: number) => (
            <Tag key={i} color="blue">{s}</Tag>
          ))}
        </Card>

        <Space>
          <Button onClick={onPrev}>上一步</Button>
          <Button type="primary" onClick={onNext}>下一步：岗位匹配</Button>
        </Space>
      </Space>
    </Card>
  )
}
