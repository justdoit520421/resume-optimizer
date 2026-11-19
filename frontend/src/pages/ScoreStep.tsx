// 步骤 3：智能评分（雷达图展示各维度）
import { useEffect, useRef, useState } from 'react'
import { Card, Button, Space, Statistic, Spin, message, Alert } from 'antd'
import { Radar } from '@ant-design/plots'
import { scoreResume } from '../api/resume'
import { useResumeStore } from '../store/resumeStore'

interface Props {
  onNext: () => void
  onPrev: () => void
}

export default function ScoreStep({ onNext, onPrev }: Props) {
  const resumeId = useResumeStore((s) => s.resumeId)
  const totalScore = useResumeStore((s) => s.totalScore)
  const dimensions = useResumeStore((s) => s.dimensions)
  const summary = useResumeStore((s) => s.scoreSummary)
  const setScore = useResumeStore((s) => s.setScore)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const fetchingRef = useRef(false)

  useEffect(() => {
    // StrictMode 下 effect 会执行两次，用 ref 守卫避免重复请求
    if (resumeId && totalScore === 0 && !fetchingRef.current) {
      fetchingRef.current = true
      handleScore().finally(() => { fetchingRef.current = false })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resumeId])

  const handleScore = async () => {
    if (!resumeId) return
    setLoading(true)
    setError('')
    try {
      const res: any = await scoreResume(resumeId)
      setScore(res.total_score, res.dimensions, res.summary)
      message.success('评分完成')
    } catch {
      setError('智能评分失败，请点击重试')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Card title="第四步：评分报告">
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <Spin size="large" />
          <div style={{ marginTop: 12, color: '#666' }}>AI 正在评分...</div>
        </div>
      </Card>
    )
  }

  // 雷达图数据
  const radarData = dimensions.map((d) => ({
    item: d.name,
    score: Math.round((d.score / d.max_score) * 100),
  }))

  return (
    <Card title="第四步：评分报告">
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {error && (
          <Alert
            type="error"
            showIcon
            message={error}
            action={<Button size="small" onClick={handleScore}>重试</Button>}
          />
        )}

        <Space size="large">
          <Statistic title="总分" value={totalScore} suffix="/ 100" valueStyle={{ color: '#1677ff' }} />
        </Space>

        <Card size="small" title="各维度得分">
          {radarData.length > 0 ? (
            <Radar
              data={radarData}
              xField="item"
              yField="score"
              height={320}
              point={{ size: 4 }}
              area={{ style: { fillOpacity: 0.3 } }}
              yAxis={{ min: 0, max: 100, grid: { line: { style: { lineDash: [4, 4] } } } }}
            />
          ) : (
            <div>暂无数据</div>
          )}
        </Card>

        {dimensions.map((d) => (
          <div key={d.name}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <b>{d.name}</b>
              <span>{d.score} / {d.max_score}</span>
            </div>
            <div style={{ color: '#666', fontSize: 13 }}>{d.reason}</div>
          </div>
        ))}

        {summary && (
          <Card size="small" title="整体评价" type="inner">
            {summary}
          </Card>
        )}

        <Space>
          <Button onClick={onPrev}>上一步</Button>
          <Button type="primary" onClick={onNext}>下一步：优化对比</Button>
        </Space>
      </Space>
    </Card>
  )
}
