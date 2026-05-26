import React, { useState, useCallback } from "react";
import { SearchHistory } from "./components/SearchHistory";
import { SearchResults } from "./components/SearchResults";
import { mockResults, mockSummary } from "./components/mockData";
import type { SearchResult } from "./types";

function App() {

  const handleHistoryClear = useCallback(() => {

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

  const handleHistorySelect = useCallback((query: string) => {}, [])

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
        />
      </div>
    </div>
  );
}

export default App;
