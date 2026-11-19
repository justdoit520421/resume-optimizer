// 步骤 1：上传简历
import { useState } from 'react'
import { Card, Upload, Button, message, Space, Alert } from 'antd'
import { UploadOutlined } from '@ant-design/icons'
import type { UploadFile } from 'antd'
import { uploadResume } from '../api/resume'
import { useResumeStore } from '../store/resumeStore'

interface Props {
  onNext: () => void
}

export default function UploadStep({ onNext }: Props) {
  const [fileList, setFileList] = useState<UploadFile[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const setResumeId = useResumeStore((s) => s.setResumeId)

  const beforeUpload = (file: File) => {
    const ok = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/msword'].includes(file.type) ||
      /\.(pdf|docx?|DOCX?)$/.test(file.name)
    if (!ok) {
      message.error('仅支持 PDF / Word 格式')
      return Upload.LIST_IGNORE
    }
    setFileList([file as unknown as UploadFile])
    return false // 阻止自动上传，手动触发
  }

  const handleUpload = async () => {
    if (fileList.length === 0) {
      message.warning('请先选择简历文件')
      return
    }
    setLoading(true)
    setError('')
    try {
      const res: any = await uploadResume(fileList[0] as unknown as File)
      setResumeId(res.resume_id)
      message.success('上传成功')
      onNext()
    } catch {
      setError('上传失败，请点击重试')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card title="第一步：上传简历">
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        <Upload
          beforeUpload={beforeUpload}
          onRemove={() => { setFileList([]); setError('') }}
          fileList={fileList}
          maxCount={1}
          accept=".pdf,.doc,.docx"
        >
          <Button icon={<UploadOutlined />}>选择简历文件（PDF / Word）</Button>
        </Upload>

        {error && (
          <Alert
            type="error"
            showIcon
            message={error}
            action={<Button size="small" onClick={handleUpload}>重试</Button>}
          />
        )}

        <Button type="primary" size="large" loading={loading} onClick={handleUpload} block>
          上传并开始解析
        </Button>
      </Space>
    </Card>
  )
}
