// 步骤 4：一键优化（逐条建议，可接受/拒绝）
import { useEffect, useRef, useState } from 'react'
import {
  Card, Button, Space, Select, Spin, message, Tag, Radio, Empty, Divider, Alert,
} from 'antd'
import { CheckOutlined, CloseOutlined } from '@ant-design/icons'
import { optimizeResume, applySuggestions } from '../api/resume'
import { useResumeStore } from '../store/resumeStore'

interface Props {
  onNext: () => void
  onPrev: () => void
}

const TYPE_LABEL: Record<string, string> = {
  quantification: '量化补充',
  wording: '措辞润色',
  structure: '结构优化',
  keyword: '关键词强化',
}

const TYPE_COLOR: Record<string, string> = {
  quantification: 'orange',
  wording: 'blue',
  structure: 'green',
  keyword: 'purple',
}

export default function OptimizeStep({ onNext, onPrev }: Props) {
  const resumeId = useResumeStore((s) => s.resumeId)
  const jobType = useResumeStore((s) => s.jobType)
  const suggestions = useResumeStore((s) => s.suggestions)
  const setSuggestions = useResumeStore((s) => s.setSuggestions)
  const setOptimizedText = useResumeStore((s) => s.setOptimizedText)

  const [loading, setLoading] = useState(false)
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState('')
  const [selectedType, setSelectedType] = useState<string>(jobType)

  const fetchingRef = useRef(false)

  useEffect(() => {
    // StrictMode 下 effect 会执行两次，用 ref 守卫避免重复请求
    if (resumeId && suggestions.length === 0 && !fetchingRef.current) {
      fetchingRef.current = true
      handleOptimize().finally(() => { fetchingRef.current = false })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resumeId])

  const handleOptimize = async () => {
    if (!resumeId) return
    setLoading(true)
    setError('')
    try {
      const res: any = await optimizeResume(resumeId, selectedType)
      setSuggestions(res.suggestions)
      message.success('优化建议生成完成')
    } catch {
      setError('优化建议生成失败，请点击「重新生成」重试')
    } finally {
      setLoading(false)
    }
  }

  // 切换单条建议的接受状态（纯前端）
  const toggleAccept = (idx: number) => {
    const next = suggestions.map((s, i) =>
      i === idx ? { ...s, accepted: !s.accepted } : s,
    )
    setSuggestions(next)
  }

  const handleApply = async () => {
    if (!resumeId) return
    const acceptedIndices = suggestions
      .map((s, i) => (s.accepted ? i : -1))
      .filter((i) => i >= 0)
    setApplying(true)
    try {
      const res: any = await applySuggestions(resumeId, acceptedIndices)
      setOptimizedText(res.optimized_text)
      message.success(`已应用 ${res.accepted_count} 条建议`)
      onNext()
    } catch {
      // 已处理
    } finally {
      setApplying(false)
    }
  }

  if (loading) {
    return (
      <Card title="第五步：优化对比">
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 12, color: '#666' }}>AI 正在生成优化建议...</div>
        </div>
      </Card>
    )
  }

  return (
    <Card title="第五步：优化对比">
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Space>
          <span>目标岗位类型：</span>
          <Select
            value={selectedType}
            onChange={setSelectedType}
            style={{ width: 160 }}
            options={[
              { value: 'tech', label: '技术岗' },
              { value: 'product', label: '产品岗' },
              { value: 'operation', label: '运营岗' },
              { value: 'design', label: '设计岗' },
            ]}
          />
          <Button onClick={handleOptimize}>重新生成</Button>
        </Space>

        {error && <Alert type="error" showIcon message={error} />}

        {suggestions.length === 0 ? (
          <Empty description={error ? '生成失败' : '暂无优化建议'} />
        ) : (
          suggestions.map((s, idx) => (
            <Card key={idx} size="small" bordered style={{ background: s.accepted ? '#f6ffed' : '#fff' }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Space>
                  <Tag color={TYPE_COLOR[s.type] || 'default'}>{TYPE_LABEL[s.type] || s.type}</Tag>
                  <Tag color={s.accepted ? 'green' : 'default'}>
                    {s.accepted ? '已接受' : '未接受'}
                  </Tag>
                </Space>
                <div>
                  <div style={{ color: '#999', textDecoration: 'line-through' }}>原文：{s.original}</div>
                  <div style={{ color: '#52c41a', fontWeight: 500 }}>优化后：{s.improved}</div>
                  <div style={{ color: '#666', fontSize: 13 }}>理由：{s.reason}</div>
                </div>
                <Radio.Group
                  value={s.accepted ? 'accept' : 'reject'}
                  onChange={() => toggleAccept(idx)}
                >
                  <Radio.Button value="accept">
                    <CheckOutlined /> 接受
                  </Radio.Button>
                  <Radio.Button value="reject">
                    <CloseOutlined /> 拒绝
                  </Radio.Button>
                </Radio.Group>
              </Space>
            </Card>
          ))
        )}

        <Divider />
        <Space>
          <Button onClick={onPrev}>上一步</Button>
          <Button type="primary" loading={applying} onClick={handleApply}>
            应用接受的建议并预览最终简历
          </Button>
        </Space>
      </Space>
    </Card>
  )
}
