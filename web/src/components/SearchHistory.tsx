import React, { useState, useEffect, useCallback } from "react";

interface SearchResult {
  title: string;
  relevance: number;
  chapter: string;
  snippet: string;
}

interface KeyPoint {
  icon: string;
  text: string;
}

interface AISummary {
  text: string;
  points: KeyPoint[];
}

interface SearchHistoryProps {
  onSelect: (query: string) => void;
  onClear: () => void;
}

export const SearchHistory: React.FC<SearchHistoryProps> = ({
  onSelect,
  onClear,
}) => {
  const [history, setHistory] = useState<string[]>([]);

  useEffect(() => {
    const loadHistory = () => {
      const rawHistory = localStorage.getItem("searchHistory");
      if (!rawHistory) {
        const DEFAULT_HISTORY = [
          "韩立修炼功法",
          "青竹蜂云剑",
          "乱星海秘境",
          "筑基丹配方",
          "血玉蜘蛛",
        ];
        setHistory(DEFAULT_HISTORY);
        return;
      }

      try {
        const parsed = JSON.parse(rawHistory);
        if (
          Array.isArray(parsed) &&
          parsed.every((item) => typeof item === "string")
        ) {
          setHistory(parsed);
        } else {
          const DEFAULT_HISTORY = [
            "韩立修炼功法",
            "青竹蜂云剑",
            "乱星海秘境",
            "筑基丹配方",
            "血玉蜘蛛",
          ];
          setHistory(DEFAULT_HISTORY);
        }
      } catch {
        const DEFAULT_HISTORY = [
          "韩立修炼功法",
          "青竹蜂云剑",
          "乱星海秘境",
          "筑基丹配方",
          "血玉蜘蛛",
        ];
        setHistory(DEFAULT_HISTORY);
      }
    };

    loadHistory();
  }, []);

  const addHistory = useCallback((query: string) => {
    const normalizedQuery = query.trim();
    if (!normalizedQuery) return;

    setHistory((prev) => {
      const newHistory = prev.filter((item) => item !== normalizedQuery);
      newHistory.unshift(normalizedQuery);
      return newHistory.slice(0, 10);
    });
  }, []);

  const removeHistory = useCallback((query: string) => {
    setHistory((prev) => prev.filter((item) => item !== query));
  }, []);

  const clearHistory = () => {
    setHistory([]);
    onClear();
  };

  const saveHistory = useCallback(() => {
    localStorage.setItem("searchHistory", JSON.stringify(history));
  }, [history]);

  useEffect(() => {
    saveHistory();
  }, [history, saveHistory]);

  return (
    <div className="sidebar">
      <h2 className="sidebar-title">📜 搜索历史</h2>

      <div className="search-history-list">
        {history.map((query) => (
          <div
            key={query}
            className="history-item"
            onClick={() => onSelect(query)}
          >
            <span className="history-icon">🔍</span>
            <span className="history-text">{query}</span>
            <button
              className="history-delete"
              aria-label="删除"
              onClick={(e) => {
                e.stopPropagation();
                removeHistory(query);
              }}
            >
              ×
            </button>
          </div>
        ))}
      </div>

      <button
        className="clear-history-btn"
        onClick={clearHistory}
        disabled={history.length === 0}
      >
        <span>🗑️</span>
        <span>清空历史</span>
      </button>
    </div>
  );
};
