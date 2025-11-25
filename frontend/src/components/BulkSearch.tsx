import React, { useState } from 'react';
import { Upload, FileSpreadsheet, Loader2, Download, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

interface BulkResult {
    domain: string;
    fullName: string;
    status: string;
    email: string | null;
    catchAll: boolean;
    debugInfo: string;
}

interface BulkSearchProps {
    apiUrl: string;
}

export const BulkSearch: React.FC<BulkSearchProps> = ({ apiUrl }) => {
    const [file, setFile] = useState<File | null>(null);
    const [searchName, setSearchName] = useState<string>('');
    const [isProcessing, setIsProcessing] = useState(false);
    const [results, setResults] = useState<BulkResult[]>([]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            const selectedFile = e.target.files[0];
            setFile(selectedFile);
            setResults([]);
            setSearchName(selectedFile.name.replace(/\.(csv|xlsx|xls)$/, ''));
        }
    };

    const handleProcess = async () => {
        if (!file) {
            alert('Please upload a file');
            return;
        }

        setIsProcessing(true);
        setResults([]);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${apiUrl}/api/bulk-search`, {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();

            if (response.ok) {
                setResults(data.results || []);
            } else {
                alert(`Error: ${data.detail || 'Upload failed'}`);
            }
        } catch (error) {
            alert(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
        } finally {
            setIsProcessing(false);
        }
    };

    const exportToCSV = () => {
        if (results.length === 0) return;

        const headers = ['Domain', 'Full Name', 'Status', 'Email', 'Catch-All', 'Debug Info'];
        const rows = results.map(r => [
            r.domain,
            r.fullName,
            r.status,
            r.email || '',
            r.catchAll ? 'Yes' : 'No',
            r.debugInfo
        ]);

        const csv = [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${searchName || 'bulk_results'}_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'valid':
                return <CheckCircle className="w-5 h-5 text-green-600" />;
            case 'not_found':
                return <XCircle className="w-5 h-5 text-gray-400" />;
            case 'catch_all':
                return <AlertCircle className="w-5 h-5 text-yellow-600" />;
            default:
                return <XCircle className="w-5 h-5 text-red-600" />;
        }
    };

    return (
        <div className="space-y-6">
            <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
                <h2 className="text-xl font-semibold mb-4 text-gray-800">Bulk Email Search</h2>

                <div className="space-y-4">
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
                        <input
                            type="file"
                            accept=".csv,.xlsx"
                            onChange={handleFileChange}
                            className="hidden"
                            id="file-upload"
                            disabled={isProcessing}
                        />
                        <label htmlFor="file-upload" className="cursor-pointer">
                            <FileSpreadsheet className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                            {file ? (
                                <p className="text-sm font-medium text-gray-700">{file.name}</p>
                            ) : (
                                <>
                                    <p className="text-sm font-medium text-gray-700">Click to upload CSV or Excel</p>
                                    <p className="text-xs text-gray-500 mt-1">File must have columns: Name, Domain</p>
                                </>
                            )}
                        </label>
                    </div>

                    {file && (
                        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                            <p className="text-sm text-blue-800 mb-2"><strong>Column names required:</strong></p>
                            <ul className="text-xs text-blue-700 space-y-1 ml-4 list-disc">
                                <li><code className="bg-white px-1">Name</code> or <code className="bg-white px-1">fullName</code></li>
                                <li><code className="bg-white px-1">Domain</code></li>
                            </ul>
                        </div>
                    )}

                    <button
                        onClick={handleProcess}
                        disabled={!file || isProcessing}
                        className={`w-full flex items-center justify-center py-3 px-4 rounded-md text-white font-medium transition-all ${!file || isProcessing
                                ? 'bg-blue-400 cursor-not-allowed'
                                : 'bg-blue-600 hover:bg-blue-700 shadow-md hover:shadow-lg'
                            }`}
                    >
                        {isProcessing ? (
                            <>
                                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                                Processing... (1s delay per row)
                            </>
                        ) : (
                            <>
                                <Upload className="w-5 h-5 mr-2" />
                                Start Processing
                            </>
                        )}
                    </button>
                </div>
            </div>

            {results.length > 0 && (
                <div className="bg-white rounded-lg shadow-sm border border-gray-200">
                    <div className="p-6 border-b border-gray-200 flex justify-between items-center">
                        <div>
                            <h3 className="text-lg font-semibold text-gray-800">Results ({results.length})</h3>
                            <p className="text-sm text-gray-500 mt-1">
                                {results.filter(r => r.status === 'valid').length} valid, {' '}
                                {results.filter(r => r.status === 'not_found').length} not found, {' '}
                                {results.filter(r => r.status === 'catch_all').length} catch-all
                            </p>
                        </div>
                        <button
                            onClick={exportToCSV}
                            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
                        >
                            <Download className="w-4 h-4 mr-2" />
                            Export CSV
                        </button>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Domain</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Info</th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {results.map((result, index) => (
                                    <tr key={index} className="hover:bg-gray-50">
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                {getStatusIcon(result.status)}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {result.fullName}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {result.domain}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                                            {result.email ? (
                                                <span className="text-blue-600 font-medium">{result.email}</span>
                                            ) : (
                                                <span className="text-gray-400">-</span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">
                                            {result.debugInfo}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
};
