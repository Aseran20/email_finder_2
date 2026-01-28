import React from 'react';
import type { HistoryItem } from '../types';
import { CheckCircle, XCircle, HelpCircle, AlertTriangle, ChevronDown, ChevronUp, Trash2, ChevronLeft, ChevronRight, Copy, Check } from 'lucide-react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Button } from '@/components/ui/button';

interface HistoryListProps {
    history: HistoryItem[];
    onDelete?: (id: string) => void;
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
            className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity"
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

const StatusBadge: React.FC<{ status: HistoryItem['status'] }> = ({ status }) => {
    const config = {
        valid: {
            className: "badge-success font-mono"
        },
        not_found: {
            className: "bg-muted text-muted-foreground border-muted-foreground/20 font-mono"
        },
        unknown: {
            className: "badge-warning font-mono"
        },
        error: {
            className: "badge-error font-mono"
        },
        searching: {
            className: "badge-info animate-pulse font-mono"
        },
    };

    const { className } = config[status];

    return (
        <Badge className={className}>
            {status.toUpperCase().replace('_', ' ')}
        </Badge>
    );
};

const HistoryCard: React.FC<{ item: HistoryItem; onDelete?: (id: string) => void }> = ({ item, onDelete }) => {
    const [isOpen, setIsOpen] = React.useState(false);

    return (
        <Card className="elevation-1 hover:elevation-2 transition-shadow animate-in group">
            <Collapsible open={isOpen} onOpenChange={setIsOpen}>
                <CardHeader className="pb-4">
                    <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0 space-y-2">
                            <div className="flex items-center gap-3">
                                <h3 className="font-mono text-lg font-medium truncate">
                                    {item.request.domain}
                                </h3>
                                <StatusBadge status={item.status} />
                            </div>
                            <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                <span>{item.request.fullName}</span>
                                <span className="text-border">·</span>
                                <time className="font-mono text-xs">
                                    {new Date(item.date).toLocaleString('en-US', {
                                        month: 'short',
                                        day: 'numeric',
                                        hour: '2-digit',
                                        minute: '2-digit'
                                    })}
                                </time>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            {item.email && (
                                <div className="text-right flex items-center gap-2 group">
                                    <div>
                                        <p className="font-mono text-sm font-medium text-primary">
                                            {item.email}
                                        </p>
                                        <p className="text-xs text-success font-mono">
                                            VERIFIED
                                        </p>
                                    </div>
                                    <CopyButton text={item.email} />
                                </div>
                            )}

                            {onDelete && (
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity text-destructive hover:text-destructive hover:bg-destructive/10"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        if (confirm('Delete this search from history?')) {
                                            onDelete(item.id);
                                        }
                                    }}
                                >
                                    <Trash2 className="w-4 h-4" />
                                </Button>
                            )}

                            <CollapsibleTrigger asChild>
                                <Button variant="ghost" size="icon" className="h-8 w-8">
                                    {isOpen ?
                                        <ChevronUp className="w-4 h-4" /> :
                                        <ChevronDown className="w-4 h-4" />
                                    }
                                </Button>
                            </CollapsibleTrigger>
                        </div>
                    </div>
                </CardHeader>

                <CollapsibleContent>
                    <CardContent className="pt-0">
                        <div className="bg-muted/50 rounded-md p-4 space-y-3 font-mono text-xs">
                            <div>
                                <span className="text-muted-foreground">Debug:</span>
                                <p className="mt-1 text-foreground">{item.debugInfo}</p>
                            </div>

                            {item.errorMessage && (
                                <div>
                                    <span className="text-destructive">Error:</span>
                                    <p className="mt-1 text-destructive">{item.errorMessage}</p>
                                </div>
                            )}

                            {item.mxRecords.length > 0 && (
                                <div>
                                    <span className="text-muted-foreground">MX Records:</span>
                                    <p className="mt-1 text-foreground">{item.mxRecords.join(', ')}</p>
                                </div>
                            )}

                            {item.smtpLogs.length > 0 && (
                                <div>
                                    <span className="text-muted-foreground">SMTP Logs:</span>
                                    <ul className="mt-2 space-y-1 text-foreground/80">
                                        {item.smtpLogs.map((log, i) => (
                                            <li key={i} className="pl-2 border-l-2 border-border">
                                                {log}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </CardContent>
                </CollapsibleContent>
            </Collapsible>
        </Card>
    );
};

export const HistoryList: React.FC<HistoryListProps> = ({ history, onDelete }) => {
    const [filter, setFilter] = React.useState('');
    const [currentPage, setCurrentPage] = React.useState(1);
    const itemsPerPage = 30;

    const filteredHistory = history.filter(item => {
        const search = filter.toLowerCase();
        return (
            item.request.domain.toLowerCase().includes(search) ||
            (item.request.fullName && item.request.fullName.toLowerCase().includes(search)) ||
            (item.email && item.email.toLowerCase().includes(search))
        );
    });

    const totalPages = Math.ceil(filteredHistory.length / itemsPerPage);
    const startIndex = (currentPage - 1) * itemsPerPage;
    const paginatedHistory = filteredHistory.slice(startIndex, startIndex + itemsPerPage);

    // Reset to page 1 when filter changes
    React.useEffect(() => {
        setCurrentPage(1);
    }, [filter]);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="font-display text-2xl font-semibold">
                        Search History
                    </h2>
                    <p className="text-sm text-muted-foreground font-mono mt-1">
                        {filteredHistory.length} {filter ? 'filtered' : 'total'} searches
                        {totalPages > 1 && ` · Page ${currentPage} of ${totalPages}`}
                    </p>
                </div>
                <Input
                    type="text"
                    placeholder="Filter results..."
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                    className="w-64 font-mono"
                />
            </div>

            <div className="space-y-4">
                {paginatedHistory.length === 0 ? (
                    <Card className="elevation-1">
                        <CardContent className="py-12 text-center">
                            <p className="text-muted-foreground">
                                {history.length === 0 ? 'No searches yet' : 'No matching results'}
                            </p>
                        </CardContent>
                    </Card>
                ) : (
                    paginatedHistory.map(item => (
                        <HistoryCard key={item.id} item={item} onDelete={onDelete} />
                    ))
                )}
            </div>

            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                        disabled={currentPage === 1}
                        className="font-mono"
                    >
                        <ChevronLeft className="w-4 h-4 mr-1" />
                        Previous
                    </Button>

                    <div className="flex items-center gap-1">
                        {Array.from({ length: totalPages }, (_, i) => i + 1)
                            .filter(page => {
                                // Show first, last, current, and ±1 from current
                                return page === 1 ||
                                       page === totalPages ||
                                       Math.abs(page - currentPage) <= 1;
                            })
                            .map((page, idx, arr) => (
                                <React.Fragment key={page}>
                                    {idx > 0 && arr[idx - 1] !== page - 1 && (
                                        <span className="text-muted-foreground px-2">...</span>
                                    )}
                                    <Button
                                        variant={page === currentPage ? "default" : "outline"}
                                        size="sm"
                                        onClick={() => setCurrentPage(page)}
                                        className="font-mono min-w-[40px]"
                                    >
                                        {page}
                                    </Button>
                                </React.Fragment>
                            ))
                        }
                    </div>

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                        disabled={currentPage === totalPages}
                        className="font-mono"
                    >
                        Next
                        <ChevronRight className="w-4 h-4 ml-1" />
                    </Button>
                </div>
            )}
        </div>
    );
};
