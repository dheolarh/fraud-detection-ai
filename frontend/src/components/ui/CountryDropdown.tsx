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

export function CountryDropdown({
    value,
    onChange,
    placeholder = 'Select a country',
    disabled = false,
    className = '',
}: CountryDropdownProps) {
    const [search, setSearch] = useState('');

    // Map countries to useful data
    const countryData = useMemo(() => {
        return countries.map((country) => ({
            name: country.name.common,
            currency: country.currencies ? Object.keys(country.currencies)[0] : 'USD',
            currencyName: country.currencies
                ? Object.values(country.currencies)[0]?.name || 'US Dollar'
                : 'US Dollar',
            flag: country.flag,
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
                        <span className="flex items-center gap-2">
                            <span>{selectedCountry.flag}</span>
                            <span>{selectedCountry.name}</span>
                            <span className="text-xs text-muted-foreground">({selectedCountry.currency})</span>
                        </span>
                    )}
                </SelectValue>
            </SelectTrigger>
            <SelectContent>
                <div className="p-2">
                    <Input
                        placeholder="Search countries..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="mb-2"
                    />
                </div>
                <ScrollArea className="h-[300px]">
                    {filteredCountries.length === 0 ? (
                        <div className="p-4 text-center text-sm text-muted-foreground">
                            No countries found
                        </div>
                    ) : (
                        filteredCountries.map((country) => (
                            <SelectItem key={country.name} value={country.name}>
                                <div className="flex items-center gap-2">
                                    <span>{country.flag}</span>
                                    <span>{country.name}</span>
                                    <span className="text-xs text-muted-foreground">
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
