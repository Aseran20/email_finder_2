import React, { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';
import type { EmailFinderRequest } from '../types';

interface SearchFormProps {
    onSearch: (request: EmailFinderRequest) => void;
    isLoading: boolean;
}

export const SearchForm: React.FC<SearchFormProps> = ({ onSearch, isLoading }) => {
    const [domain, setDomain] = useState('');
    const [fullName, setFullName] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!domain || !fullName) return;

        onSearch({
            domain,
            fullName
        });
    };

    return (
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <h2 className="text-xl font-semibold mb-6 text-gray-800">Start your Search</h2>

            <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Domain *
                        </label>
                        <input
                            type="text"
                            value={domain}
                            onChange={(e) => setDomain(e.target.value)}
                            placeholder="e.g. google.com"
                            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Full Name *
                        </label>
                        <input
                            type="text"
                            value={fullName}
                            onChange={(e) => setFullName(e.target.value)}
                            placeholder="e.g. John Doe"
                            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-colors"
                            required
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={isLoading || !domain || !fullName}
                    className={`w-full flex items-center justify-center py-3 px-4 rounded-md text-white font-medium transition-all ${isLoading || !domain || !fullName
                        ? 'bg-blue-400 cursor-not-allowed'
                        : 'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg'
                        }`}
                >
                    {isLoading ? (
                        <>
                            <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                            Searching...
                        </>
                    ) : (
                        <>
                            <Search className="w-5 h-5 mr-2" />
                            Find Email
                        </>
                    )}
                </button>

                <p className="text-xs text-center text-gray-500 mt-4">
                    Internal tool – no external credits used
                </p>
            </form>
        </div>
    );
};
