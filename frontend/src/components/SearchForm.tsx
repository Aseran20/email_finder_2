import React, { useState } from 'react';
import { Search, Loader2, Mail, Globe } from 'lucide-react';
import type { EmailFinderRequest } from '../types';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';

interface SearchFormProps {
    onSearch: (request: EmailFinderRequest) => void;
    onCheckEmail?: (email: string, fullName?: string) => void;
    isLoading: boolean;
}

type SearchMode = 'domain' | 'email';

export const SearchForm: React.FC<SearchFormProps> = ({ onSearch, onCheckEmail, isLoading }) => {
    const [mode, setMode] = useState<SearchMode>('domain');
    const [domain, setDomain] = useState('');
    const [fullName, setFullName] = useState('');
    const [email, setEmail] = useState('');

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        if (mode === 'domain') {
            if (!domain || !fullName) return;

            onSearch({
                domain: domain.trim(),
                fullName: fullName.trim()
            });

            // Clear form after submission
            setDomain('');
            setFullName('');
        } else {
            // Email check mode
            if (!email) return;

            if (onCheckEmail) {
                onCheckEmail(email.trim(), fullName.trim() || undefined);
            }

            // Clear form after submission
            setEmail('');
            setFullName('');
        }
    };

    return (
        <Card className="elevation-2 animate-in">
            <CardHeader className="space-y-3">
                <CardTitle>Start Verification</CardTitle>
                <CardDescription className="font-mono text-xs">
                    {mode === 'domain' ? 'Enter domain and full name for SMTP validation' : 'Enter email address to verify'}
                </CardDescription>

                {/* Mode Switch */}
                <div className="flex gap-2 pt-2">
                    <Button
                        type="button"
                        variant={mode === 'domain' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setMode('domain')}
                        className="flex-1 font-mono"
                    >
                        <Globe className="w-3.5 h-3.5 mr-1.5" />
                        Domain Search
                    </Button>
                    <Button
                        type="button"
                        variant={mode === 'email' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setMode('email')}
                        className="flex-1 font-mono"
                    >
                        <Mail className="w-3.5 h-3.5 mr-1.5" />
                        Email Check
                    </Button>
                </div>
            </CardHeader>

            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-5">
                        {mode === 'domain' ? (
                            <>
                                <div className="space-y-2">
                                    <Label htmlFor="domain" className="text-sm">Domain</Label>
                                    <Input
                                        id="domain"
                                        type="text"
                                        value={domain}
                                        onChange={(e) => setDomain(e.target.value)}
                                        placeholder="company.com"
                                        className="font-mono"
                                        required
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="fullName" className="text-sm">Full Name</Label>
                                    <Input
                                        id="fullName"
                                        type="text"
                                        value={fullName}
                                        onChange={(e) => setFullName(e.target.value)}
                                        placeholder="John Doe"
                                        required
                                    />
                                </div>
                            </>
                        ) : (
                            <>
                                <div className="space-y-2">
                                    <Label htmlFor="email" className="text-sm">Email Address</Label>
                                    <Input
                                        id="email"
                                        type="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="john.doe@company.com"
                                        className="font-mono"
                                        required
                                    />
                                </div>

                                <div className="space-y-2">
                                    <Label htmlFor="fullNameFallback" className="text-sm">
                                        Full Name <span className="text-muted-foreground">(optional - for fallback)</span>
                                    </Label>
                                    <Input
                                        id="fullNameFallback"
                                        type="text"
                                        value={fullName}
                                        onChange={(e) => setFullName(e.target.value)}
                                        placeholder="John Doe"
                                    />
                                </div>
                            </>
                        )}
                    </div>

                    <Button
                        type="submit"
                        disabled={isLoading || (mode === 'domain' ? (!domain || !fullName) : !email)}
                        className="w-full font-mono"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Verifying...
                            </>
                        ) : (
                            <>
                                <Search className="w-4 h-4 mr-2" />
                                {mode === 'domain' ? 'Find Email' : 'Check Email'}
                            </>
                        )}
                    </Button>

                    <p className="text-xs text-center text-muted-foreground font-mono">
                        Internal verification · No external credits
                    </p>
                </form>
            </CardContent>
        </Card>
    );
};
