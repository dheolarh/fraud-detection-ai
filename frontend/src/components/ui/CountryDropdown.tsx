import { useState, useMemo } from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import countries from 'world-countries';

interface CountryDropdownProps {
    value: string;
    onChange: (country: string, currency: string) => void;
    placeholder?: string;
    disabled?: boolean;
    className?: string;
}

interface CountryInfo {
    name: string;
    currency: string;
    currencyName: string;
    flagEmoji: string;
    cca2: string;
    region: string;
}

export function CountryDropdown({
    value,
    onChange,
    placeholder = 'Select a country',
    disabled = false,
    className = '',
}: CountryDropdownProps) {
    const [search, setSearch] = useState('');

    // Map countries to useful data
    const countryData = useMemo<CountryInfo[]>(() => {
        return countries.map((country: any) => ({
            name: country.name.common,
            currency: country.currencies ? Object.keys(country.currencies)[0] : 'USD',
            currencyName: country.currencies
                ? Object.values(country.currencies)[0]?.name || 'US Dollar'
                : 'US Dollar',
            flagEmoji: country.flag,
            cca2: country.cca2.toLowerCase(),
            region: country.region,
        })).sort((a, b) => a.name.localeCompare(b.name));
    }, []);

    // Filter countries based on search
    const filteredCountries = useMemo(() => {
        if (!search) return countryData;
        const searchLower = search.toLowerCase();
        return countryData.filter(
            (country) =>
                country.name.toLowerCase().includes(searchLower) ||
                (country.currency && country.currency.toLowerCase().includes(searchLower))
        );
    }, [search, countryData]);

    const selectedCountry = countryData.find((c) => c.name === value);

    return (
        <Select
            value={value}
            onValueChange={(countryName) => {
                const country = countryData.find((c) => c.name === countryName);
                if (country) {
                    onChange(countryName, country.currency);
                }
            }}
            disabled={disabled}
        >
            <SelectTrigger className={className}>
                <SelectValue placeholder={placeholder}>
                    {selectedCountry && (
                        <span className="flex items-center gap-3">
                            <img 
                                src={`https://flagcdn.com/w40/${selectedCountry.cca2}.png`}
                                alt=""
                                className="h-3.5 w-auto rounded-sm object-cover shadow-sm ring-1 ring-white/10"
                            />
                            <span className="font-bold">{selectedCountry.name}</span>
                            <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/50">({selectedCountry.currency})</span>
                        </span>
                    )}
                </SelectValue>
            </SelectTrigger>
            <SelectContent className="glass-panel border-white/10 p-0 shadow-2xl">
                <div className="p-3 bg-white/[0.02] border-b border-white/5">
                    <Input
                        placeholder="Filter database..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="h-9 bg-white/5 border-white/5 focus:bg-white/10 rounded-xl text-xs font-bold transition-all"
                    />
                </div>
                <ScrollArea className="h-[280px] scrollbar-hide py-2 px-2">
                    {filteredCountries.length === 0 ? (
                        <div className="p-8 text-center text-[10px] font-black uppercase tracking-widest text-muted-foreground/30 italic">
                            No signal matches found
                        </div>
                    ) : (
                        filteredCountries.map((country) => (
                            <SelectItem key={country.name} value={country.name} className="rounded-xl focus:bg-primary focus:text-black mb-1 p-2">
                                <div className="flex items-center gap-3">
                                    <img 
                                        src={`https://flagcdn.com/w40/${country.cca2}.png`}
                                        alt=""
                                        className="h-3 w-4 rounded-[1px] object-cover border border-white/10"
                                    />
                                    <span className="text-xs font-bold">{country.name}</span>
                                    <span className="text-[9px] font-black uppercase tracking-widest text-muted-foreground/40 font-mono ml-auto pr-4">
                                        {country.currency}
                                    </span>
                                </div>
                            </SelectItem>
                        ))
                    )}
                </ScrollArea>
            </SelectContent>
        </Select>
    );
}
