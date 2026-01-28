import React, { useState } from 'react';
import { Loader2, Download, Copy, Check, FileSpreadsheet } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Label } from '@/components/ui/label';

interface BulkResult {
    domain: string;
    fullName: string;
    status: string;
    email: string | null;
    catchAll: boolean;
    debugInfo: string;
}

interface ParsedRow {
    fullName: string;
    domain: string;
}

interface BulkSearchProps {
    apiUrl: string;
}

const CopyButton: React.FC<{ text: string }> = ({ text }) => {
    const [copied, setCopied] = React.useState(false);

    const handleCopy = async () => {
        try {
            await navigator.clipboard.writeText(text);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        } catch (err) {
            console.error('Failed to copy:', err);
        }
    };

    return (
        <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6"
            onClick={handleCopy}
        >
            {copied ? (
                <Check className="w-3.5 h-3.5 text-success" />
            ) : (
                <Copy className="w-3.5 h-3.5" />
            )}
        </Button>
    );
};

export const BulkSearch: React.FC<BulkSearchProps> = ({ apiUrl }) => {
    const [pastedData, setPastedData] = useState<string>('');
    const [parsedRows, setParsedRows] = useState<ParsedRow[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [results, setResults] = useState<BulkResult[]>([]);

    const parsePastedData = (text: string): ParsedRow[] => {
        if (!text.trim()) {
            return [];
        }

        // Split by lines
        const lines = text.trim().split('\n').filter(line => line.trim());

        if (lines.length === 0) return [];

        // Detect delimiter (tab or comma)
        const firstLine = lines[0];
        const delimiter = firstLine.includes('\t') ? '\t' : ',';

        // Parse each line
        const rows = lines.map(line => {
            const cols = line.split(delimiter).map(c => c.trim());

            // Accept 2 columns (Full Name, Domain) or 3 (First, Last, Domain)
            if (cols.length === 2) {
                return { fullName: cols[0], domain: cols[1] };
            } else if (cols.length === 3) {
                return { fullName: `${cols[0]} ${cols[1]}`, domain: cols[2] };
            }
            return null;
        }).filter(Boolean) as ParsedRow[];

        // Skip first line if it's a header
        const firstRow = rows[0];
        const hasHeader = firstRow && (
            firstRow.domain.toLowerCase().includes('domain') ||
            firstRow.fullName.toLowerCase().includes('name')
        );

        return hasHeader ? rows.slice(1) : rows;
    };

    const handlePasteChange = (text: string) => {
        setPastedData(text);
        const parsed = parsePastedData(text);
        setParsedRows(parsed);
        setResults([]); // Clear previous results
    };

    const downloadTemplate = () => {
        const template = `Full Name,Domain
John Doe,company.com
Jane Smith,example.com`;

        const blob = new Blob([template], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'bulk_search_template.csv';
        a.click();
        URL.revokeObjectURL(url);
    };

    const handleProcess = async () => {
        if (parsedRows.length === 0) {
            alert('Please paste some data first');
            return;
        }

        setIsProcessing(true);
        setResults([]);

        try {
            const response = await fetch(`${apiUrl}/api/bulk-search-json`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    searches: parsedRows.map(row => ({
                        domain: row.domain,
                        fullName: row.fullName
                    }))
                }),
            });

            const data = await response.json();

            if (response.ok) {
                setResults(data.results || []);
            } else {
                alert(`Error: ${data.detail || 'Processing failed'}`);
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
        a.download = `bulk_results_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    };

    const getStatusBadge = (status: string) => {
        const config = {
            valid: { className: "badge-success" },
            not_found: { className: "bg-muted text-muted-foreground" },
            catch_all: { className: "badge-warning" },
            error: { className: "badge-error" }
        };

        const statusKey = status === 'catch_all' ? 'catch_all' : status === 'valid' ? 'valid' : status === 'not_found' ? 'not_found' : 'error';
        const { className } = config[statusKey];

        return (
            <Badge className={`${className} font-mono`}>
                {status.toUpperCase().replace('_', ' ')}
            </Badge>
        );
    };

    return (
        <div className="space-y-6">
            <Card className="elevation-2 animate-in">
                <CardHeader className="space-y-3">
                    <div className="flex items-center justify-between">
                        <div>
                            <CardTitle>Bulk Verification</CardTitle>
                            <CardDescription className="font-mono text-xs mt-1">
                                Paste data from Excel/Sheets for batch SMTP validation
                            </CardDescription>
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={downloadTemplate}
                            className="font-mono"
                        >
                            <Download className="w-4 h-4 mr-2" />
                            CSV Template
                        </Button>
                    </div>
                </CardHeader>
                <CardContent className="space-y-5">
                    <div className="space-y-2">
                        <Label htmlFor="bulkData" className="text-sm">
                            Paste from Spreadsheet
                        </Label>
                        <textarea
                            id="bulkData"
                            value={pastedData}
                            onChange={(e) => handlePasteChange(e.target.value)}
                            placeholder="Full Name	Domain
John Doe	company.com
Jane Smith	example.com"
                            className="w-full min-h-[200px] px-3 py-2 text-sm font-mono border border-border rounded-md focus:outline-none focus:ring-2 focus:ring-ring resize-y"
                            disabled={isProcessing}
                        />
                        <p className="text-xs text-muted-foreground font-mono">
                            Paste from Excel (tab-separated) or CSV (comma-separated)
                        </p>
                    </div>

                    {parsedRows.length > 0 && (
                        <div className="bg-info/10 border border-info/20 rounded-md p-4">
                            <div className="flex items-center justify-between mb-2">
                                <p className="text-sm font-medium text-info">
                                    ✓ {parsedRows.length} rows detected
                                </p>
                                <FileSpreadsheet className="w-4 h-4 text-info" />
                            </div>
                            <div className="text-xs text-info/80 space-y-1 font-mono">
                                {parsedRows.slice(0, 3).map((row, i) => (
                                    <div key={i} className="truncate">
                                        {row.fullName} @ {row.domain}
                                    </div>
                                ))}
                                {parsedRows.length > 3 && (
                                    <div className="text-info/60">
                                        ... and {parsedRows.length - 3} more
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    <Button
                        onClick={handleProcess}
                        disabled={parsedRows.length === 0 || isProcessing}
                        className="w-full font-mono"
                    >
                        {isProcessing ? (
                            <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Processing... ({parsedRows.length} rows, 1s per row)
                            </>
                        ) : (
                            <>
                                <FileSpreadsheet className="w-4 h-4 mr-2" />
                                Start Processing ({parsedRows.length} rows)
                            </>
                        )}
                    </Button>
                </CardContent>
            </Card>

            {results.length > 0 && (
                <Card className="elevation-2 animate-in">
                    <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
                        <div>
                            <CardTitle className="text-xl">Results ({results.length})</CardTitle>
                            <p className="text-sm text-muted-foreground mt-1 font-mono">
                                {results.filter(r => r.status === 'valid').length} valid · {' '}
                                {results.filter(r => r.status === 'not_found').length} not found · {' '}
                                {results.filter(r => r.status === 'catch_all').length} catch-all
                            </p>
                        </div>
                        <Button
                            onClick={exportToCSV}
                            variant="outline"
                            className="font-mono"
                        >
                            <Download className="w-4 h-4 mr-2" />
                            Export CSV
                        </Button>
                    </CardHeader>

                    <CardContent className="p-0">
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-muted/50 border-y border-border">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono">Status</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono">Name</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono">Domain</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono">Email</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider font-mono">Debug Info</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {results.map((result, index) => (
                                        <tr key={index} className="hover:bg-muted/30 transition-colors">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                {getStatusBadge(result.status)}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                                                {result.fullName}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-mono text-muted-foreground">
                                                {result.domain}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                {result.email ? (
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-primary font-medium font-mono">{result.email}</span>
                                                        <CopyButton text={result.email} />
                                                    </div>
                                                ) : (
                                                    <span className="text-muted-foreground">-</span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 text-sm text-muted-foreground max-w-xs truncate font-mono">
                                                {result.debugInfo}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
};
