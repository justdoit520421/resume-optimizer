// 主应用：6 步流程（上传 → 解析 → 匹配 → 评分 → 优化 → 导出）
import { useState } from 'react'
import { Layout, Steps, Typography, theme } from 'antd'
import UploadStep from './pages/UploadStep'
import ParseStep from './pages/ParseStep'
import MatchStep from './pages/MatchStep'
import ScoreStep from './pages/ScoreStep'
import OptimizeStep from './pages/OptimizeStep'
import FinalStep from './pages/FinalStep'

const { Header, Content } = Layout
const { Title } = Typography

const steps = [
  { title: '上传简历' },
  { title: '解析预览' },
  { title: '岗位匹配' },
  { title: '评分报告' },
  { title: '优化对比' },
  { title: '最终简历' },
]

export default function App() {
  const [current, setCurrent] = useState(0)
  const { token } = theme.useToken()

  // 根据当前步骤渲染对应页面，子页面通过 onNext 回调推进
  const renderStep = () => {
    switch (current) {
      case 0:
        return <UploadStep onNext={() => setCurrent(1)} />
      case 1:
        return <ParseStep onNext={() => setCurrent(2)} onPrev={() => setCurrent(0)} />
      case 2:
        return <MatchStep onNext={() => setCurrent(3)} onPrev={() => setCurrent(1)} />
      case 3:
        return <ScoreStep onNext={() => setCurrent(4)} onPrev={() => setCurrent(2)} />
      case 4:
        return <OptimizeStep onNext={() => setCurrent(5)} onPrev={() => setCurrent(3)} />
      case 5:
        return <FinalStep onPrev={() => setCurrent(4)} />
      default:
        return null
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: token.colorPrimary, padding: '0 24px' }}>
        <Title level={4} style={{ color: '#fff', margin: 0, lineHeight: '64px' }}>
          简历智能优化工具
        </Title>
      </Header>
      <Content style={{ padding: '24px', maxWidth: 1100, margin: '0 auto', width: '100%' }}>
        <Steps
          current={current}
          items={steps}
          style={{ marginBottom: 32, background: '#fff', padding: 24, borderRadius: 8 }}
          onChange={(idx) => setCurrent(idx)}
        />
        {renderStep()}
      </Content>
    </Layout>
  )
}
