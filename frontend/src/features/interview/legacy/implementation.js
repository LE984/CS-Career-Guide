import { readLegacyStream } from './stream.js'
import { interviewDuration } from '../session-clock.js'

// The existing browser-driven, prompt-based interview implementation.
// No Vue refs, DOM, audio player or concrete HTTP client is owned here.
export class LegacyInterviewImplementation {
  constructor({ chatStream, saveReview, transcribe, readResume }) {
    this.chatStream = chatStream
    this.persistReview = saveReview
    this.transcribeAudio = transcribe
    this.readResume = readResume
  }

  async start({ style, sessionId, durationMinutes, enableTts = false, signal }, onEvent) {
    let resumePrompt = null
    try {
      resumePrompt = formatLegacyResume(this.readResume())
    } catch (error) {
      // Storage can be unavailable in browser privacy modes. The original page
      // treated that exactly like an absent resume and still started the turn.
      console.error('[RESUME] 解析简历数据失败:', error)
    }
    const promptType = style === 'pressure' ? 'pressure_interview' : 'interview'
    let interviewPrompt = `【面试模式】你是一位${getStyleDescription(style)}面试官。请开始一场${interviewDuration(durationMinutes)}分钟的面试。`

    if (resumePrompt) {
      interviewPrompt += `

【面试者简历信息】
${resumePrompt}

请根据以上简历信息，提出针对性的面试问题。`
    }

    interviewPrompt += `

要求：
1. 首先进行简短的自我介绍（说明你是面试官，面试风格）
2. 然后提出第一个面试问题
3. 在整个面试过程中，你只需要扮演面试官角色
4. 根据用户的回答，提出下一个相关问题
5. 保持${style === 'pressure' ? '压力面试' : style === 'technical' ? '技术面试' : style === 'behavioral' ? '行为面试' : '温和友好'}的风格

现在开始面试。`
    let timeout
    try {
      const response = await Promise.race([
        this.chatStream(interviewPrompt, promptType, style, sessionId, { enableTts, signal }),
        new Promise((_, reject) => {
          timeout = setTimeout(() => reject(new Error('请求超时')), 15000)
        })
      ])
      await readLegacyStream(response, onEvent)
    } finally {
      clearTimeout(timeout)
    }
  }

  async answer({ answer, style, sessionId, enableTts = false, signal }, onEvent) {
    const userMessage = answer
    const promptType = style === 'pressure' ? 'pressure_interview' : 'interview'
    const response = await this.chatStream(
      `【面试模式】用户的回答是："${userMessage}"

作为${getStyleDescription(style)}面试官，请：
1. 简要评价用户的回答（可选）
2. 提出下一个面试问题

注意：你只需扮演面试官角色，不要查询任何数据库信息。`, promptType, style, sessionId, { enableTts, signal }
    )
    await readLegacyStream(response, onEvent)
  }

  async generateReview({ messages, style, sessionId, signal }, onEvent = () => {}) {
    const conversation = reviewMessages(messages)
      .map(msg => `${msg.type === 'ai' ? '面试官' : '面试者'}：${msg.content}`)
      .join('\n')
    if (conversation.trim().length < 50) {
      return { skipped: true, content: '面试对话内容不足，无法生成复盘报告。请确保面试过程中有足够的交流。' }
    }
    const response = await this.chatStream(
      `【面试复盘模式】请对以下面试过程进行复盘，并提供改进建议。

面试风格：${getStyleDescription(style)}

对话记录：
${conversation}

请提供以下内容：
1. 面试表现总结（整体评价）
2. 回答的优点
3. 需要改进的地方
4. 具体改进建议
5. 下次面试的准备建议`, 'interview_review', style, sessionId || 'default_session', { enableTts: false, signal }
    )
    let content = ''
    await readLegacyStream(response, async event => {
      if (event.type === 'chunk' && event.content) content += event.content
      await onEvent(event)
    })
    if (!content.trim()) throw new Error('未获取到复盘内容')
    return { skipped: false, content }
  }

  saveReview({ messages, content, style, sessionId, remainingTime, totalDurationSeconds = 900 }) {
    const conversation = reviewMessages(messages)
    return this.persistReview({
      session_id: sessionId || 'default_session',
      review_content: content,
      interview_style: style || 'gentle',
      interview_duration: Math.max(0, Math.floor((totalDurationSeconds - remainingTime) / 60)),
      question_count: conversation.filter(msg => msg.type === 'ai').length,
      answer_count: conversation.filter(msg => msg.type === 'user').length
    })
  }

  transcribe(formData) {
    return this.transcribeAudio(formData)
  }
}

function reviewMessages(messages) {
  return messages.filter(msg => msg.content && !msg.content.includes('正在生成面试复盘'))
}

export function formatLegacyResume(resumeStr) {
  try {
    if (!resumeStr) {
      console.log('[RESUME] 未找到简历数据')
      return null
    }

    const resume = JSON.parse(resumeStr)

    // 构建简历提示词
    let resumePrompt = ''

    if (resume.name) {
      resumePrompt += `姓名：${resume.name}\n`
    }
    if (resume.target_position) {
      resumePrompt += `意向岗位：${resume.target_position}\n`
    }
    if (resume.self_evaluation) {
      resumePrompt += `个人自评：${resume.self_evaluation}\n`
    }
    if (resume.skills) {
      resumePrompt += `专业技能：${resume.skills}\n`
    }
    if (resume.education && resume.education.length > 0) {
      resumePrompt += `教育背景：\n`
      resume.education.forEach(edu => {
        if (edu.school) {
          resumePrompt += `  - ${edu.school} ${edu.major || ''} ${edu.degree || ''} ${edu.period || ''}\n`
        }
      })
    }
    if (resume.experience && resume.experience.length > 0) {
      resumePrompt += `实习经历：\n`
      resume.experience.forEach(exp => {
        if (exp.company) {
          resumePrompt += `  - ${exp.company} ${exp.position || ''} ${exp.period || ''}\n`
          if (exp.description) {
            resumePrompt += `    ${exp.description}\n`
          }
        }
      })
    }
    if (resume.projects && resume.projects.length > 0) {
      resumePrompt += `项目经验：\n`
      resume.projects.forEach(project => {
        if (project.name) {
          resumePrompt += `  - ${project.name} ${project.role || ''} ${project.period || ''}\n`
          if (project.description) {
            resumePrompt += `    ${project.description}\n`
          }
        }
      })
    }
    if (resume.certificates && resume.certificates.length > 0) {
      resumePrompt += `证书认证：\n`
      resume.certificates.forEach(cert => {
        if (cert.name) {
          resumePrompt += `  - ${cert.name} ${cert.issuer || ''} ${cert.period || ''}\n`
        }
      })
    }

    return resumePrompt.trim() || null
  } catch (error) {
    console.error('[RESUME] 解析简历数据失败:', error)
    return null
  }
}

export function getStyleDescription(style) {
  const descriptions = {
    gentle: '温和友好的',
    pressure: '压力型',
    technical: '技术导向的',
    behavioral: '行为面试'
  }
  return descriptions[style] || '专业的'
}

// 语音识别相关函数
