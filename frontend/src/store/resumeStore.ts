// 全局状态管理：当前简历 ID、解析结果、评分、优化建议、匹配结果
import { create } from 'zustand'

interface ScoreDimension {
  name: string
  score: number
  max_score: number
  reason: string
}

interface Suggestion {
  original: string
  improved: string
  reason: string
  type: string
  accepted: boolean
}

interface ResumeState {
  resumeId: number | null
  rawText: string
  parsed: Record<string, any> | null

  // 评分
  totalScore: number
  dimensions: ScoreDimension[]
  scoreSummary: string

  // 优化
  jobType: string
  suggestions: Suggestion[]
  optimizedText: string

  // 匹配
  matchScore: number
  matched: string[]
  missing: string[]
  matchSuggestions: string[]

  setResumeId: (id: number) => void
  setParsed: (raw: string, parsed: Record<string, any>) => void
  setScore: (total: number, dims: ScoreDimension[], summary: string) => void
  setSuggestions: (items: Suggestion[]) => void
  setOptimizedText: (text: string) => void
  setMatch: (score: number, matched: string[], missing: string[], sug: string[]) => void
}

export const useResumeStore = create<ResumeState>((set) => ({
  resumeId: null,
  rawText: '',
  parsed: null,
  totalScore: 0,
  dimensions: [],
  scoreSummary: '',
  jobType: 'product',
  suggestions: [],
  optimizedText: '',
  matchScore: 0,
  matched: [],
  missing: [],
  matchSuggestions: [],

  setResumeId: (id) => set({ resumeId: id }),
  setParsed: (raw, parsed) => set({ rawText: raw, parsed }),
  setScore: (total, dimensions, summary) => set({ totalScore: total, dimensions, scoreSummary: summary }),
  setSuggestions: (suggestions) => set({ suggestions }),
  setOptimizedText: (text) => set({ optimizedText: text }),
  setMatch: (matchScore, matched, missing, matchSuggestions) =>
    set({ matchScore, matched, missing, matchSuggestions }),
}))
