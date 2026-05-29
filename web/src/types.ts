export interface SearchResult {
  title: string;
  relevance: number;
  snippet: string;
}

export interface HistoryItem {
  query: string;
  timestamp: number;
}

export interface RetrievalResult {
  id: string;
  text: string;
  score: number;
  metadata?: {
    title?: string;
    chapter?: string;
    source?: string;
    [key: string]: any;
  };
}

export interface StreamChunk {
  type: "thinking" | "content" | "retrieval" | "done" | "error";
  content?: string;
  retrieval_results?: RetrievalResult[];
  error?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
}

export interface ChatCompletionResponse {
  answer: string;
  retrieval_results: RetrievalResult[];
  reasoning?: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  model: string;
}

export interface ChatCompletionResponse {
  answer: string;
  retrieval_results: RetrievalResult[];
  reasoning?: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  model: string;
}
