import React, { useState } from "react";
import type { SearchResult, RetrievalResult, StreamChunk } from "../types";
import { config } from "../config";

interface SearchResultsProps {
  onViewDetail: (title: string) => void;
  onShowRecommendations: (title: string) => void;
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  onViewDetail,
  onShowRecommendations,
}) => {
  const [query, setQuery] = useState("");
  const [answer, setAnswer] = useState("");
  const [thinking, setThinking] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [apiResponse, setApiResponse] = useState<SearchResult[]>([]);
  const [sortAscending, setSortAscending] = useState(false);

  // 将后端API响应转换为前端格式
  const convertToSearchResult = (retrievalResult: RetrievalResult): SearchResult => {
    return {
      title: retrievalResult.metadata?.title || retrievalResult.id,
      relevance: Math.round(retrievalResult.score * 100),
      snippet: retrievalResult.text.substring(0, 200) + (retrievalResult.text.length > 200 ? "..." : "")
    };
  };

  const handleSearch = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setApiResponse([]);
    setThinking("")
    setAnswer("")

    // 创建 AbortController 用于超时控制
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30秒超时
    const aiSummary: string[] = [];
    const aiThinking: string[] = [];
    let lastText: string = ""
    let searchResults: SearchResult[] = [];

    const parseChunkText = (chunk: string): StreamChunk[] => {
      const chunkEvents = new Array<StreamChunk>()
      chunk = lastText + chunk
      const rawEvents = chunk.split("\n\n")
      if(rawEvents.length === 0) {
        return []
      }
      lastText = rawEvents.pop()
      for(let rawEvent of rawEvents) {
        if(!rawEvent.startsWith("data: ")) {
          continue
        }
        let chunkEvent = JSON.parse(rawEvent.slice(6))
        chunkEvents.push(chunkEvent)
      }
      return chunkEvents
    }

    const processEvent = (chunk: StreamChunk) => {
      switch (chunk.type) {
        case "retrieval":
          if (chunk.retrieval_results && chunk.retrieval_results.length > 0) {
            searchResults = chunk.retrieval_results.map(convertToSearchResult);
            setApiResponse(searchResults);
          }
          break;

        case "thinking":
          if (chunk.content) {
            aiThinking.push(chunk.content);
            const fullThinking = aiThinking.join('');
            setThinking(fullThinking);
          }
          break;

        case "content":
          if (chunk.content) {
            aiSummary.push(chunk.content);
            const fullSummary = aiSummary.join('');
            setAnswer(fullSummary);
          }
          break;

        case "done":
          setIsLoading(false);
          break;

        case "error":
          console.error("API错误:", chunk.error);
          setAnswer(chunk.error)
          setIsLoading(false);
          break;
      }
    }

    try{
      // 调用后端API
      const response = await fetch(`${config.apiBaseUrl}/api/v1/chat/completions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: query,
          top_k: 5,
          stream: true,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();

      if (!reader) {
        throw new Error("无法获取响应流");
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const received = decoder.decode(value, {stream: true});

        const chunkEvents = parseChunkText(received)
        for(let chunkEvent of chunkEvents) {
          processEvent(chunkEvent)
        }
      }
    } catch(e) {
      setIsLoading(false)
      setAnswer("检索失败: " + e)
    }

  }

  const sortedResults = [...apiResponse].sort((a, b) => {
    return sortAscending
      ? a.relevance - b.relevance
      : b.relevance - a.relevance;
  });

  return (
    <div className="main-content">
      {/* 搜索区域 */}
      <div className="search-section">
        <h1 className="main-title">凡人修仙传 · RAG 检索系统</h1>
        <p className="search-subtitle">
          基于《凡人修仙传》内容的智能检索与问答系统
        </p>

        <div className="search-container">
          <input
            type="text"
            className="search-input"
            placeholder="输入关键词搜索相关内容..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            // onKeyDown={(e) => {
            //   if (e.key === "Enter" && !isLoading) {
            //     handleSearch();
            //   }
            // }}
          />
          <button
            className="search-btn"
            onClick={handleSearch}
            disabled={isLoading}
          >
            <span>{isLoading ? "⏳" : "🔍"}</span>
            <span>{isLoading ? "搜索中..." : "搜索"}</span>
          </button>
        </div>

        <div className="tags-container">
          <span className="tags-label">热门标签：</span>
          <button className="tag-btn" onClick={() => setQuery("虚天鼎的作用")}>
            虚天鼎的作用
          </button>
        </div>
      </div>

      {/* 排序和统计 */}
      <div className="results-header">
        <h2 className="results-count">搜索结果 (共 {apiResponse.length} 条)</h2>
        <button className="sort-btn" onClick={() => {setSortAscending(!sortAscending)}}>
          按相关性排序 {sortAscending ? "▲" : "▼"}
        </button>
      </div>

      {/* AI 摘要 */}
      <div className="ai-summary">
        <div className="summary-header">
          <h2 className="summary-title">🤖 AI 智能摘要</h2>
          {isLoading && (
            <div className="loading-indicator">正在生成AI总结...</div>
          )}
        </div>
        <div className="summary-content">
          {thinking && (
            <div className="summary-thinking">
              <p className="thinking-text">
                {thinking}
              </p>
            </div>
          )}
          <p className="summary-text">
            {answer}
          </p>
        </div>
      </div>

      {/* 搜索结果列表 */}
      <div className="results-list">
        {sortedResults.map((result) => (
          <div key={result.title} className="result-card">
            <div className="card-header">
              <h3 className="card-title">{result.title}</h3>
              <div
                className={`relevance-tag ${result.relevance >= 90 ? "high" : "medium"}`}
              >
                <span>📊</span>
                <span>{result.relevance}% 相关</span>
              </div>
            </div>
            {/* <div className="chapter-info">
              <span>📖</span>
              <span>{result.chapter}</span>
            </div> */}
            <p className="card-snippet">{result.snippet}</p>
            <div className="card-actions">
              <button
                className="btn btn-primary"
                onClick={() => onViewDetail(result.title)}
              >
                <span>📋</span>
                <span>查看详情</span>
              </button>
              <button
                className="btn btn-outline"
                onClick={() => onShowRecommendations(result.title)}
              >
                <span>💡</span>
                <span>相关推荐</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
