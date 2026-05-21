import React, { useState, useCallback } from "react";
import { SearchHistory } from "./components/SearchHistory";
import { SearchResults } from "./components/SearchResults";
import { mockResults, mockSummary } from "./components/mockData";
import type { SearchResult } from "./types";

function App() {
  const [query, setQuery] = useState("");
  const [currentResults, setCurrentResults] =
    useState<SearchResult[]>(mockResults);
  const [sortAscending, setSortAscending] = useState(false);
  const [totalCount, setTotalCount] = useState(23);
  const [isLoading, setIsLoading] = useState(false);

  const escapeHtml = (value: string): string => {
    return value.replace(/[&<>'"]/g, (char) => {
      const entities: Record<string, string> = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        "'": "&#39;",
        '"': "&quot;",
      };
      return entities[char];
    });
  };

  // 处理实时搜索
  const performSearch = useCallback(async (searchQuery: string) => {
    const normalizedQuery = searchQuery.trim();
    setIsLoading(true);

    if (!normalizedQuery) {
      setCurrentResults(mockResults);
      setTotalCount(23);
      setIsLoading(false);
      return;
    }

    // 这里可以直接使用SearchResults组件中的API调用
    // 为了保持兼容性，仍然使用mock数据作为初始加载
    const filteredResults = mockResults.filter(
      (result) =>
        result.title.includes(normalizedQuery) ||
        result.snippet.includes(normalizedQuery),
    );
    setCurrentResults(filteredResults);
    setTotalCount(Math.floor(Math.random() * 30) + 10);

    setIsLoading(false);
  }, []);

  // 处理API返回的搜索结果
  const handleApiResults = useCallback((results: SearchResult[]) => {
    setCurrentResults(results);
    setTotalCount(results.length);
  }, []);

  // 处理AI摘要
  const handleApiSummary = useCallback((summary: string) => {
    setAiSummary(summary);
  }, []);

  // AI摘要状态
  const [aiSummary, setAiSummary] = useState("根据搜索结果，韩立是《凡人修仙传》的主角，从凡人逐步修炼成仙。他的核心法宝青竹蜂云剑由万年金雷竹炼制而成，蕴含雷属性灵力。筑基期是修仙的关键阶段，需要筑基丹辅助，而血玉蜘蛛则是炼制筑基丹的重要材料。乱星海的虚天殿是韩立早期的重要冒险地点，内藏上古功法和珍稀法宝。");

  const handleSearch = useCallback(
    (searchQuery: string) => {
      performSearch(searchQuery);
    },
    [performSearch],
  );

  const handleHistorySelect = useCallback(
    (searchQuery: string) => {
      setQuery(searchQuery);
      performSearch(searchQuery).then(handleSearch);
    },
    [performSearch, handleSearch],
  );

  // const handleSearch = useCallback(
  //   (searchQuery: string) => {
  //     setQuery(searchQuery);
  //   },
  //   [],
  // );

  const handleHistoryClear = useCallback(() => {
    localStorage.removeItem("searchHistory");
    setQuery("");
    setCurrentResults(mockResults);
  }, []);

  const handleViewDetail = useCallback((title: string) => {
    window.alert(
      `查看详情：${title}\n\n此处将显示详细内容，包括完整的章节内容、人物关系图、修炼境界分析等。`,
    );
  }, []);

  const handleShowRecommendations = useCallback((title: string) => {
    window.alert(
      `相关推荐：${title}\n\n此处将显示与"${title}"相关的其他内容推荐，包括相似章节、相关人物、关联法宝等。`,
    );
  }, []);

  const handleSortToggle = useCallback(() => {
    setSortAscending((prev) => !prev);
  }, []);

  return (
    <div className="app">
      <div className="flex gap-8 mt-8">
        <SearchHistory
          onSelect={handleHistorySelect}
          onClear={handleHistoryClear}
        />
        <SearchResults
          onViewDetail={handleViewDetail}
          onShowRecommendations={handleShowRecommendations}
          sortAscending={sortAscending}
          onSortToggle={handleSortToggle}
          onApiResults={handleApiResults}
          onApiSummary={handleApiSummary}
        />
      </div>
    </div>
  );
}

export default App;
