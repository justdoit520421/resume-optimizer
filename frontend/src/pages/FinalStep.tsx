// 步骤 6：最终简历预览与导出（Word / PDF）
import { useState } from 'react'
import { Card, Button, Space, message, Alert, Empty } from 'antd'
import { DownloadOutlined } from '@ant-design/icons'
import { exportResume } from '../api/resume'
import { useResumeStore } from '../store/resumeStore'

interface Props {
  onPrev: () => void
}

export default function FinalStep({ onPrev }: Props) {
  const resumeId = useResumeStore((s) => s.resumeId)
  const rawText = useResumeStore((s) => s.rawText)
  const optimizedText = useResumeStore((s) => s.optimizedText)
  const suggestions = useResumeStore((s) => s.suggestions)

  const [exporting, setExporting] = useState('')

  // 导出优化后简历为 Word / PDF
  const handleExport = async (format: 'docx' | 'pdf') => {
    if (!resumeId) return
    setExporting(format)
    try {
      const blob: any = await exportResume(resumeId, format)
      // 业务错误时后端返回 JSON（被 axios 转成 Blob），需解析提示
      if (blob.type && blob.type.includes('application/json')) {
        const text = await blob.text()
        try {
          message.error(JSON.parse(text).message || '导出失败')
        } catch {
          message.error('导出失败')
        }
        return
      }
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `优化后简历.${format}`
      a.click()
      URL.revokeObjectURL(url)
      message.success(`已导出 ${format === 'docx' ? 'Word' : 'PDF'} 文件`)
    } catch {
      message.error('导出失败，请稍后重试')
    } finally {
      setExporting('')
    }
  }

  const acceptedCount = suggestions.filter((s) => s.accepted).length
  const finalText = optimizedText || rawText

  return (
    <Card title="第六步：最终简历预览与导出">
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {optimizedText ? (
          <Alert
            type="success"
            showIcon
            message={`已应用 ${acceptedCount} 条优化建议，以下为最终简历内容`}
          />
        ) : (
          <Alert
            type="warning"
            showIcon
            message="尚未应用优化建议，当前展示为简历原文"
            description="可返回「优化对比」步骤接受建议后重新生成，或直接导出原文。"
          />
        )}

        <Card size="small" title="简历全文">
          {finalText ? (
            <pre
              style={{
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                maxHeight: 480,
                overflow: 'auto',
                margin: 0,
                fontFamily: 'inherit',
                fontSize: 14,
                lineHeight: 1.8,
              }}
            >
              {finalText}
            </pre>
          ) : (
            <Empty description="暂无内容" />
          )}
        </Card>

        <Card size="small" title="导出">
          <Space>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              loading={exporting === 'docx'}
              onClick={() => handleExport('docx')}
            >
              导出 Word
            </Button>
            <Button
              type="primary"
              icon={<DownloadOutlined />}
              loading={exporting === 'pdf'}
              onClick={() => handleExport('pdf')}
            >
              导出 PDF
            </Button>
          </Space>
        </Card>

        <Space>
          <Button onClick={onPrev}>上一步</Button>
        </Space>
      </Space>
    </Card>
  )
}
