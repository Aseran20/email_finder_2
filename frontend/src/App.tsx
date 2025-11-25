import { useState } from 'react';
import { SearchForm } from './components/SearchForm';
import { HistoryList } from './components/HistoryList';
import type { EmailFinderRequest, HistoryItem, EmailFinderResponse } from './types';
import { Mail } from 'lucide-react';

function App() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSearch = async (request: EmailFinderRequest) => {
    const newId = Date.now().toString();
    const tempItem: HistoryItem = {
      id: newId,
      date: new Date().toISOString(),
      request,
      status: 'searching',
      patternsTested: [],
      smtpLogs: [],
      catchAll: false,
      mxRecords: [],
      debugInfo: 'Initializing search...',
    };

    setHistory(prev => [tempItem, ...prev]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/find-email', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      const data: EmailFinderResponse = await response.json();

      setHistory(prev => prev.map(item =>
        item.id === newId
          ? { ...item, ...data, status: data.status as HistoryItem['status'] }
          : item
      ));
    } catch (error) {
      setHistory(prev => prev.map(item =>
        item.id === newId
          ? {
            ...item,
            status: 'error',
            errorMessage: error instanceof Error ? error.message : 'Network error',
            debugInfo: 'Failed to connect to backend'
          }
          : item
      ));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center">
          <div className="flex items-center space-x-3">
            <div className="bg-blue-600 p-2 rounded-lg">
              <Mail className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-xl font-bold text-gray-900">Email Finder <span className="text-xs font-normal text-gray-500 ml-2">Internal MVP</span></h1>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 h-[calc(100vh-8rem)]">
          {/* Left Column - Search Form */}
          <div className="lg:col-span-4">
            <SearchForm onSearch={handleSearch} isLoading={isLoading} />
          </div>

          {/* Right Column - History */}
          <div className="lg:col-span-8 h-full overflow-hidden">
            <HistoryList history={history} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;
