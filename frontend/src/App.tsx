import { useState } from 'react';
import { SearchForm } from './components/SearchForm';
import { HistoryList } from './components/HistoryList';
import { BulkSearch } from './components/BulkSearch';
import type { EmailFinderRequest, HistoryItem, EmailFinderResponse } from './types';
import { Mail, Search, FileSpreadsheet } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

function App() {
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
      const response = await fetch(`${apiUrl}/api/find-email`, {
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

  const handleDelete = (id: string) => {
    setHistory(prev => prev.filter(item => item.id !== id));
  };

  const handleCheckEmail = async (email: string, fullName?: string) => {
    const newId = Date.now().toString();
    const tempItem: HistoryItem = {
      id: newId,
      date: new Date().toISOString(),
      request: {
        domain: email.split('@')[1] || email,
        fullName: fullName || email
      },
      status: 'searching',
      patternsTested: [],
      smtpLogs: [],
      catchAll: false,
      mxRecords: [],
      debugInfo: 'Checking email...',
    };

    setHistory(prev => [tempItem, ...prev]);
    setIsLoading(true);

    try {
      const response = await fetch(`${apiUrl}/api/check-email`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, fullName }),
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
    <div className="min-h-screen bg-background">
      <header className="border-b border-border/40 sticky top-0 z-10 bg-background/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-8 h-20 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-primary/10">
              <Mail className="w-6 h-6 text-primary" />
            </div>
            <div>
              <h1 className="font-display text-2xl font-semibold tracking-tight">
                Email Finder
              </h1>
              <p className="text-xs text-muted-foreground font-mono">
                SMTP Verification Tool
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-8 py-12">
        <Tabs defaultValue="single" className="w-full">
          <TabsList className="mb-8">
            <TabsTrigger value="single" className="font-mono">
              <Search className="w-4 h-4 mr-2" />
              Single Search
            </TabsTrigger>
            <TabsTrigger value="bulk" className="font-mono">
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              Bulk Search
            </TabsTrigger>
          </TabsList>

          <TabsContent value="single" className="animate-in">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              <div className="lg:col-span-4">
                <SearchForm onSearch={handleSearch} onCheckEmail={handleCheckEmail} isLoading={isLoading} />
              </div>
              <div className="lg:col-span-8">
                <HistoryList history={history} onDelete={handleDelete} />
              </div>
            </div>
          </TabsContent>

          <TabsContent value="bulk" className="animate-in">
            <BulkSearch apiUrl={apiUrl} />
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;
