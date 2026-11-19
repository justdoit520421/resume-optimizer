// 步骤 3：岗位匹配（输入 JD，输出匹配度与差距）
import { useState } from 'react'
import {
  Card, Button, Space, Input, Statistic, Spin, message, Tag, List, Alert,
} from 'antd'
import { matchJob } from '../api/resume'
import { useResumeStore } from '../store/resumeStore'

interface Props {
  onNext: () => void
  onPrev: () => void
}

const { TextArea } = Input

export default function MatchStep({ onNext, onPrev }: Props) {
  const resumeId = useResumeStore((s) => s.resumeId)
  const matchScore = useResumeStore((s) => s.matchScore)
  const matched = useResumeStore((s) => s.matched)
  const missing = useResumeStore((s) => s.missing)
  const matchSuggestions = useResumeStore((s) => s.matchSuggestions)
  const setMatch = useResumeStore((s) => s.setMatch)

  const [jdText, setJdText] = useState('')
  const [loading, setLoading] = useState(false)
  const [hasResult, setHasResult] = useState(false)
  const [error, setError] = useState('')

  const handleMatch = async () => {
    if (!resumeId) return
    if (!jdText.trim()) {
      message.warning('请输入岗位描述（JD）')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res: any = await matchJob(resumeId, jdText)
      setMatch(res.match_score, res.matched, res.missing, res.suggestions)
      setHasResult(true)
      message.success('匹配分析完成')
    } catch {
      setError('匹配分析失败，请点击「开始匹配分析」重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="第三步：岗位匹配">
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <div>
          <div style={{ marginBottom: 8 }}>请粘贴目标岗位描述（JD）：</div>
          <TextArea
            rows={6}
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="例如：负责产品规划与设计，推动用户增长，要求 3 年以上产品经验，熟悉数据分析..."
          />
        </div>

        <Button type="primary" loading={loading} onClick={handleMatch}>
          开始匹配分析
        </Button>

        {error && (
          <Alert
            type="error"
            showIcon
            message={error}
            action={<Button size="small" onClick={handleMatch}>重试</Button>}
          />
        )}

        {loading && (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 12, color: '#666' }}>AI 正在分析匹配度...</div>
          </div>
        )}

        {hasResult && (
          <>
            <Card size="small">
              <Statistic
                title="岗位匹配度"
                value={matchScore}
                suffix="/ 100"
                valueStyle={{
                  color: matchScore >= 70 ? '#52c41a' : matchScore >= 50 ? '#faad14' : '#ff4d4f',
                }}
              />
            </Card>

            <Card size="small" title="已匹配的能力点">
              <Space wrap>
                {matched.map((m, i) => (
                  <Tag key={i} color="green">{m}</Tag>
                ))}
              </Space>
            </Card>

            <Card size="small" title="缺失的能力点">
              <Space wrap>
                {missing.map((m, i) => (
                  <Tag key={i} color="red">{m}</Tag>
                ))}
              </Space>
            </Card>

            <Card size="small" title="改进建议">
              <List
                dataSource={matchSuggestions}
                renderItem={(item, idx) => <List.Item>{idx + 1}. {item}</List.Item>}
              />
            </Card>

            <Alert
              message="提示"
              description="建议针对缺失的能力点，补充相关项目经历或技能描述，以提升匹配度。"
              type="info"
              showIcon
            />
          </>
        )}

        <Space>
          <Button onClick={onPrev}>上一步</Button>
          <Button type="primary" onClick={onNext}>下一步：评分报告</Button>
        </Space>
      </Space>
    </Card>
  )
}
