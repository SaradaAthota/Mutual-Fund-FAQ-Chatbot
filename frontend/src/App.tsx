import { useMemo, useState, type FormEvent } from 'react'
import './App.css'

const examples = [
  'What is the expense ratio for HDFC Flexi Cap Direct Plan?',
  'Exit load for HDFC Small Cap Fund?',
  'How do I download my capital-gains statement on Groww?',
]

interface AnswerPayload {
  answer: string
  citations: string[]
  is_factual: boolean
  confidence: number
  method: string
  last_updated?: string
}

const backendUrl = import.meta.env.VITE_BACKEND_URL ?? 'http://127.0.0.1:8001'

const sortCitations = (citations: string[]): string[] => {
  const priority = (url: string) => {
    if (url.includes('groww.in')) return 0
    if (url.includes('hdfcfund.com')) return 1
    return 2
  }
  const deduped = Array.from(new Set(citations))
  return deduped.sort((a, b) => priority(a) - priority(b))
}

function App() {
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState<AnswerPayload | null>(null)
  const [status, setStatus] = useState<'idle' | 'loading' | 'error'>('idle')
  const [error, setError] = useState<string>('')

  const isDisabled = question.trim().length < 5 || status === 'loading'

  const heading = useMemo(
    () =>
      answer?.is_factual === false ? 'We only provide facts' : 'HDFC Mutual Fund Facts Assistant',
    [answer?.is_factual],
  )

  const handleSubmit = async (evt: FormEvent<HTMLFormElement>) => {
    evt.preventDefault()
    if (!question.trim()) return
    setStatus('loading')
    setError('')
    setAnswer(null)
    try {
      const response = await fetch(`${backendUrl}/ask`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: question.trim() }),
      })
      if (!response.ok) {
        const data = await response.json()
        throw new Error(data?.detail ?? 'Request failed')
      }
      const data: AnswerPayload = await response.json()
      setAnswer(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setStatus('idle')
    }
  }

  const handleExample = (text: string) => {
    setQuestion(text)
    setAnswer(null)
    setError('')
  }

  return (
    <div className="page">
      <main className="app-shell">
        <header>
          <p className="eyebrow">Groww · HDFC Mutual Fund</p>
          <h1>{heading}</h1>
          <p className="subtitle">
            Concise, citation-backed answers (≤3 sentences). Facts only. No investment advice.
          </p>
        </header>
        <section className="examples">
          <p>Try one:</p>
          <div className="chips">
            {examples.map((item) => (
              <button key={item} className="chip" type="button" onClick={() => handleExample(item)}>
                {item}
              </button>
            ))}
          </div>
        </section>

        <section>
          <form className="query-form" onSubmit={handleSubmit}>
            <label htmlFor="question" className="sr-only">
              Ask a factual question
            </label>
            <textarea
              id="question"
              placeholder="Ask about expense ratios, exit loads, lock-ins, statements, etc."
              value={question}
              onChange={(evt) => setQuestion(evt.target.value)}
              rows={4}
              required
            />
            <button type="submit" disabled={isDisabled}>
              {status === 'loading' ? 'Looking up…' : 'Get answer'}
            </button>
          </form>
          {error && <p className="error">{error}</p>}
        </section>

        <section className="answer-panel">
          {status === 'loading' && <p className="muted">Retrieving official Groww documents…</p>}
          {!answer && status !== 'loading' && <p className="muted">Your answer will appear here.</p>}
          {answer && (
            <article className="answer">
              <div className="answer-text">
                <p>{answer.answer}</p>
                {answer.last_updated && <p className="timestamp">{answer.last_updated}</p>}
              </div>
              {answer.citations.length > 0 && (
                <ul className="citations-list">
                  {sortCitations(answer.citations).map((url) => (
                    <li key={url}>
                      <a href={url} target="_blank" rel="noreferrer">
                        {url}
                      </a>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          )}
        </section>

        <footer>
          <p>Facts-only. No investment advice.</p>
        </footer>
      </main>
    </div>
  )
}

export default App
