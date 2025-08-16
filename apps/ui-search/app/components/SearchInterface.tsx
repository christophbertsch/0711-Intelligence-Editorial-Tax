'use client';

import { useState } from 'react';

interface SearchResult {
  title: string;
  snippet: string;
  score: number;
  source_url: string;
  doc_type?: string;
  citations?: Array<{ url: string; title: string }>;
}

interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
}

export default function SearchInterface() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim() }),
      });

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          Editorial Knowledge Search
        </h1>
        <p className="text-gray-600">
          Search through curated knowledge from trusted sources
        </p>
      </div>

      <form onSubmit={handleSearch} className="mb-8">
        <div className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Enter your search query..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-red-800">Error: {error}</p>
        </div>
      )}

      {results && (
        <div>
          <div className="mb-4 text-sm text-gray-600">
            Found {results.total} results for "{results.query}"
          </div>

          <div className="space-y-6">
            {results.results.map((result, index) => (
              <div key={index} className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-lg font-semibold text-blue-600 hover:text-blue-800">
                    <a href={result.source_url} target="_blank" rel="noopener noreferrer">
                      {result.title}
                    </a>
                  </h3>
                  <div className="flex items-center gap-2">
                    {result.doc_type && (
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        {result.doc_type}
                      </span>
                    )}
                    <span className="text-sm text-gray-500">
                      Score: {result.score.toFixed(2)}
                    </span>
                  </div>
                </div>

                <p className="text-gray-700 mb-3 leading-relaxed">
                  {result.snippet}
                </p>

                <div className="flex items-center justify-between text-sm">
                  <a
                    href={result.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-green-600 hover:text-green-800"
                  >
                    {new URL(result.source_url).hostname}
                  </a>

                  {result.citations && result.citations.length > 0 && (
                    <div className="text-gray-500">
                      {result.citations.length} citation{result.citations.length !== 1 ? 's' : ''}
                    </div>
                  )}
                </div>

                {result.citations && result.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-100">
                    <details className="text-sm">
                      <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
                        View citations
                      </summary>
                      <ul className="mt-2 space-y-1">
                        {result.citations.map((citation, citIndex) => (
                          <li key={citIndex}>
                            <a
                              href={citation.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-500 hover:text-blue-700"
                            >
                              {citation.title || citation.url}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </details>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}