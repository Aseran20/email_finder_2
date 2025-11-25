export interface EmailFinderRequest {
    domain: string;
    fullName: string;
}

export interface EmailFinderResponse {
    status: 'valid' | 'not_found' | 'unknown' | 'error' | 'searching';
    email?: string | null;
    patternsTested: string[];
    smtpLogs: string[];
    catchAll: boolean;
    mxRecords: string[];
    debugInfo: string;
    errorMessage?: string | null;
}

export interface HistoryItem extends EmailFinderResponse {
    id: string;
    date: string;
    request: EmailFinderRequest;
}
