import React from 'react';
import type { HistoryItem } from '../types';
import { CheckCircle, XCircle, HelpCircle, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';

interface HistoryListProps {
    history: HistoryItem[];
}

const StatusBadge: React.FC<{ status: HistoryItem['status'] }> = ({ status }) => {
    const styles = {
        valid: 'bg-green-100 text-green-800 border-green-200',
        not_found: 'bg-gray-100 text-gray-800 border-gray-200',
        unknown: 'bg-yellow-100 text-yellow-800 border-yellow-200',
        error: 'bg-red-100 text-red-800 border-red-200',
        searching: 'bg-blue-50 text-blue-600 border-blue-100 animate-pulse',
    };

    const icons = {
        valid: <CheckCircle className="w-4 h-4 mr-1" />,
        not_found: <XCircle className="w-4 h-4 mr-1" />,
        unknown: <HelpCircle className="w-4 h-4 mr-1" />,
        error: <AlertTriangle className="w-4 h-4 mr-1" />,
        searching: <div className="w-4 h-4 mr-1 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />,
    };

    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[status]}`}>
            {icons[status]}
            {status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')}
        </span>
    );
};

const HistoryCard: React.FC<{ item: HistoryItem }> = ({ item }) => {
    const [isOpen, setIsOpen] = React.useState(false);

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden transition-all hover:shadow-md">
            <div className="p-4 flex items-center justify-between">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center space-x-3 mb-1">
                        <h3 className="text-lg font-medium text-gray-900 truncate">
                            {item.request.domain}
                        </h3>
                        <StatusBadge status={item.status} />
                    </div>
                    <p className="text-sm text-gray-500">
                        {item.request.fullName || 'No name provided'} • {new Date(item.date).toLocaleString()}
                    </p>
                </div>

                <div className="flex items-center space-x-4">
                    {item.email && (
                        <div className="text-right">
                            <p className="text-sm font-medium text-gray-900">{item.email}</p>
                            <p className="text-xs text-green-600">Email found</p>
                        </div>
                    )}

                    <button
                        onClick={() => setIsOpen(!isOpen)}
                        className="p-1 hover:bg-gray-100 rounded-full transition-colors"
                    >
                        {isOpen ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
                    </button>
                </div>
            </div>

            {isOpen && (
                <div className="bg-gray-50 px-4 py-3 border-t border-gray-200 text-xs font-mono text-gray-600">
                    <div className="space-y-2">
                        <div>
                            <span className="font-semibold text-gray-700">Debug Info:</span> {item.debugInfo}
                        </div>
                        {item.errorMessage && (
                            <div className="text-red-600">
                                <span className="font-semibold">Error:</span> {item.errorMessage}
                            </div>
                        )}
                        {item.mxRecords.length > 0 && (
                            <div>
                                <span className="font-semibold text-gray-700">MX Records:</span> {item.mxRecords.join(', ')}
                            </div>
                        )}
                        {item.smtpLogs.length > 0 && (
                            <div>
                                <span className="font-semibold text-gray-700">SMTP Logs:</span>
                                <ul className="list-disc list-inside pl-2 mt-1 space-y-1">
                                    {item.smtpLogs.map((log, i) => (
                                        <li key={i} className="break-all">{log}</li>
                                    ))}
                                </ul>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export const HistoryList: React.FC<HistoryListProps> = ({ history }) => {
    const [filter, setFilter] = React.useState('');

    const filteredHistory = history.filter(item => {
        const search = filter.toLowerCase();
        return (
            item.request.domain.toLowerCase().includes(search) ||
            (item.request.fullName && item.request.fullName.toLowerCase().includes(search)) ||
            (item.email && item.email.toLowerCase().includes(search))
        );
    });

    return (
        <div className="h-full flex flex-col">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-800">Search History</h2>
                <input
                    type="text"
                    placeholder="Filter history..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 outline-none"
                />
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                {filteredHistory.length === 0 ? (
                    <div className="text-center py-12 text-gray-400">
                        <p>No search history yet.</p>
                    </div>
                ) : (
                    filteredHistory.map(item => (
                        <HistoryCard key={item.id} item={item} />
                    ))
                )}
            </div>
        </div>
    );
};
